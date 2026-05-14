"""
Bidirectional message routing.
Handles agent-to-client and client-to-agent message flow.
"""
import asyncio
import base64
import logging
from typing import Dict, Any, Optional, Callable, Awaitable

from fastapi import WebSocket
from google.adk.agents import LiveRequestQueue
from google.adk.runners import InMemoryRunner
from google.adk.agents.run_config import RunConfig
from google.genai.types import Content, Part, Blob

from ..core.state import ConversationState, ConversationPersistence
from ..core.session import SessionData, session_manager
from .protocol import (
    create_tool_call_message,
    create_tool_result_message,
    create_state_update_message,
    create_text_message,
    create_audio_message,
    create_turn_complete_message,
    create_interrupted_message,
    create_error_message,
    create_pong_message
)

logger = logging.getLogger(__name__)


class SafeWebSocket:
    """Wrapper for safe WebSocket operations."""

    def __init__(self, websocket: WebSocket):
        self.websocket = websocket

    async def send_json(self, data: dict) -> bool:
        """
        Safely send JSON data.

        Returns:
            True if sent successfully, False if connection closed
        """
        try:
            if self.websocket.client_state.name != "CONNECTED":
                return False
            await self.websocket.send_json(data)
            return True
        except RuntimeError as e:
            if "websocket.send" in str(e).lower():
                logger.debug("WebSocket already closed, skipping message")
                return False
            raise
        except Exception as e:
            logger.error(f"Error sending WebSocket message: {e}")
            return False


class ConversationStateTracker:
    """Tracks conversation state from tool results."""

    # Mapping of tool names to state keys
    TOOL_STATE_MAPPING = {
        'get_agent_name': 'agent_name',
        'get_agent_gender': ('agent_gender', 'gender'),
        'get_personality': 'personality',
        'get_languages': 'languages',
        'get_dialect': 'dialect',
        'get_interaction_steps': 'interaction_steps',
        'get_conversation_examples': 'conversation_examples',
        'get_handover_reasons': 'handover_reasons',
        'get_additional_instructions': ('additional_instructions', 'instructions'),
    }

    def __init__(self):
        self.state: Dict[str, Any] = {}
        self.tool_results_log: list = []

    def update_from_tool_result(
        self,
        tool_name: str,
        response: Dict[str, Any]
    ) -> None:
        """Update state from a tool result."""
        if response.get('status') != 'success':
            return

        mapping = self.TOOL_STATE_MAPPING.get(tool_name)

        if mapping:
            if isinstance(mapping, tuple):
                # (state_key, response_key)
                state_key, response_key = mapping
                value = response.get(response_key)
            else:
                # Same key for state and response
                state_key = mapping
                value = response.get(state_key)

            if value is not None:
                self.state[state_key] = value
                logger.info(f"Updated conversation_state[{state_key}]: {value}")

        elif tool_name == 'conversation_complete':
            self.state['completed'] = True
            final_config = response.get('final_config', {})
            self.state['completion_reason'] = final_config.get('completion_reason')

    def log_tool_result(
        self,
        tool_name: str,
        result: Dict[str, Any]
    ) -> None:
        """Log a tool result with timestamp."""
        self.tool_results_log.append({
            "timestamp": asyncio.get_event_loop().time(),
            "tool_name": tool_name,
            "result": result
        })

    def is_complete(self) -> bool:
        """Check if conversation is complete."""
        return self.state.get('completed', False)


class AgentToClientHandler:
    """Handles agent responses and sends to client."""

    def __init__(
        self,
        websocket: SafeWebSocket,
        session: SessionData,
        persistence: ConversationPersistence
    ):
        self.websocket = websocket
        self.session = session
        self.persistence = persistence
        self.state_tracker = ConversationStateTracker()

    async def run(self) -> None:
        """Run the agent-to-client message loop."""
        try:
            async for event in self.session.runner.run_live(
                user_id=self.session.user_id,
                session_id=self.session.session_id,
                live_request_queue=self.session.live_queue,
                run_config=self.session.run_config
            ):
                if not await self._handle_event(event):
                    return  # Connection closed
        except Exception as e:
            logger.error(f"Error in agent messaging: {e}", exc_info=True)
            await self.websocket.send_json(create_error_message(str(e)))

    async def _handle_event(self, event) -> bool:
        """Handle a single event from the agent. Returns False if connection closed."""
        # Handle content parts (tool calls, responses, text, audio)
        if hasattr(event, 'content') and event.content and hasattr(event.content, 'parts'):
            for part in event.content.parts:
                if not await self._handle_part(part, event):
                    return False

        # Handle turn completion
        if hasattr(event, 'turn_complete') and event.turn_complete:
            session_manager.reset_interruption(self.session.user_id)
            if not await self.websocket.send_json(create_turn_complete_message()):
                return False
            logger.info("Turn completed")

        # Handle interruption
        if hasattr(event, 'interrupted') and event.interrupted:
            user_initiated = self.session.user_interrupted
            logger.info(f"Interruption detected (user_initiated={user_initiated})")
            session_manager.set_interrupted(self.session.user_id)
            if not await self.websocket.send_json(create_interrupted_message()):
                return False
            logger.info("Interrupted - output stopped")

        return True

    async def _handle_part(self, part, event) -> bool:
        """Handle a content part. Returns False if connection closed."""
        # Function call
        if hasattr(part, 'function_call') and part.function_call:
            fc = part.function_call
            message = create_tool_call_message(
                tool_name=fc.name,
                tool_id=fc.id,
                arguments=fc.args if hasattr(fc, 'args') else {}
            )
            if not await self.websocket.send_json(message):
                return False
            logger.info(f"Tool called: {fc.name} with args: {message['arguments']}")

        # Function response
        if hasattr(part, 'function_response') and part.function_response:
            fr = part.function_response

            # Debug: Log the actual response structure
            logger.info(f"DEBUG: Tool {fr.name} raw response type: {type(fr.response)}")
            logger.info(f"DEBUG: Tool {fr.name} raw response: {fr.response}")

            # Log and track state
            self.state_tracker.log_tool_result(fr.name, fr.response)
            self.state_tracker.update_from_tool_result(fr.name, fr.response)

            # Debug: Log the updated state
            logger.info(f"DEBUG: State tracker state after update: {self.state_tracker.state}")

            # Send tool result
            message = create_tool_result_message(
                tool_name=fr.name,
                tool_id=fr.id,
                result=fr.response
            )
            if not await self.websocket.send_json(message):
                return False

            # Send state update
            state_message = create_state_update_message(self.state_tracker.state)
            if not await self.websocket.send_json(state_message):
                return False

            logger.info(f"Tool result for {fr.name}: {fr.response}")

            # Save on completion
            if fr.name == 'conversation_complete' and fr.response.get('completed'):
                await self._save_conversation()

        # Text response
        if hasattr(part, 'text') and part.text:
            message = create_text_message(
                text=part.text,
                partial=getattr(event, 'partial', False)
            )
            if not await self.websocket.send_json(message):
                return False
            logger.info(f"Sent text: {part.text[:50]}...")

        # Audio response
        if hasattr(part, 'inline_data') and part.inline_data:
            inline_data = part.inline_data
            if hasattr(inline_data, 'data') and hasattr(inline_data, 'mime_type'):
                # Skip if interrupted
                if session_manager.is_cancelled(self.session.user_id):
                    logger.debug("Skipping audio chunk - user interrupted")
                    return True

                message = create_audio_message(
                    audio_data=inline_data.data,
                    mime_type=inline_data.mime_type
                )
                if not await self.websocket.send_json(message):
                    return False
                logger.debug(f"Sent audio chunk ({len(inline_data.data)} bytes)")

        return True

    async def _save_conversation(self) -> None:
        """Save conversation to file."""
        state = ConversationState()
        for key, value in self.state_tracker.state.items():
            if hasattr(state, key):
                setattr(state, key, value)
        state.completed = True

        await self.persistence.save(
            user_id=self.session.user_id,
            session_id=self.session.session_id,
            state=state,
            tool_results=self.state_tracker.tool_results_log
        )


class ClientToAgentHandler:
    """Handles client messages and sends to agent."""

    def __init__(
        self,
        websocket: WebSocket,
        session: SessionData
    ):
        self.websocket = websocket
        self.session = session
        self.safe_ws = SafeWebSocket(websocket)

    async def run(self) -> None:
        """Run the client-to-agent message loop."""
        try:
            while True:
                data = await self.websocket.receive_json()
                await self._handle_message(data)
        except Exception as e:
            logger.error(f"Error in client messaging: {e}", exc_info=True)

    async def _handle_message(self, data: Dict[str, Any]) -> None:
        """Handle a single message from the client."""
        mime_type = data.get("mime_type", "")
        content_data = data.get("data", "")
        msg_type = data.get("type", "")

        if mime_type == "text/plain":
            # Text input
            content = Content(parts=[Part(text=content_data)])
            self.session.live_queue.send_content(content)
            logger.info(f"Client #{self.session.user_id} sent text: {content_data}")

        elif mime_type == "audio/pcm":
            # Audio input
            audio_bytes = base64.b64decode(content_data)
            audio_blob = Blob(
                mime_type="audio/pcm;rate=16000",
                data=audio_bytes
            )
            self.session.live_queue.send_realtime(audio_blob)
            logger.debug(f"Client #{self.session.user_id} sent audio: {len(audio_bytes)} bytes")

        elif msg_type == "user_speaking":
            # User started speaking - set interruption
            logger.info(f"User #{self.session.user_id} started speaking")
            session_manager.set_interrupted(self.session.user_id, user_initiated=True)
            logger.info("Interruption flag set - stopping audio output")

        elif msg_type == "ping":
            # Keepalive ping
            await self.safe_ws.send_json(create_pong_message())
