"""
WebSocket connection lifecycle handlers.
Manages connection setup, messaging, and cleanup.
"""
import asyncio
import base64
import json
import logging
from typing import Optional, Dict, Any

from fastapi import WebSocket, WebSocketDisconnect
from google.genai.types import Content, Part

from ..core.session import session_manager, SessionData
from ..core.state import ConversationPersistence
from .messaging import (
    SafeWebSocket,
    AgentToClientHandler,
    ClientToAgentHandler
)
from .protocol import create_connection_message

logger = logging.getLogger(__name__)


class WebSocketConnectionHandler:
    """Handles the complete lifecycle of a WebSocket connection."""

    def __init__(self, persistence_dir: str = "conversation_outputs"):
        self.persistence = ConversationPersistence(persistence_dir)

    async def handle(
        self,
        websocket: WebSocket,
        user_id: str,
        is_audio: bool = True,
        business_context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Handle a WebSocket connection from start to finish.

        Args:
            websocket: The FastAPI WebSocket connection
            user_id: Unique identifier for the user
            is_audio: Whether audio mode is enabled
            business_context: Optional business context for personalization
        """
        await websocket.accept()
        logger.info(f"Client #{user_id} connected (audio={is_audio})")

        try:
            # Create session
            session = await session_manager.create(
                user_id=user_id,
                is_audio=is_audio,
                business_context=business_context
            )

            # Send connection confirmation
            await websocket.send_json(
                create_connection_message(
                    session_id=session.session_id,
                    audio_enabled=is_audio
                )
            )

            # Trigger agent greeting for audio mode
            if is_audio:
                initial_trigger = Content(parts=[Part(text="[SESSION_START]")])
                session.live_queue.send_content(initial_trigger)
                logger.info(f"Sent initial trigger to agent for user {user_id}")

            # Run bidirectional messaging
            await self._run_messaging(websocket, session)

        except WebSocketDisconnect:
            logger.info(f"Client #{user_id} disconnected")
        except Exception as e:
            logger.error(f"WebSocket error for user {user_id}: {e}", exc_info=True)
        finally:
            # Cleanup
            session_manager.remove(user_id)
            logger.info(f"Session ended for user {user_id}")

    async def _run_messaging(
        self,
        websocket: WebSocket,
        session: SessionData
    ) -> None:
        """Run bidirectional messaging between client and agent."""
        safe_ws = SafeWebSocket(websocket)

        # Create handlers
        agent_handler = AgentToClientHandler(
            websocket=safe_ws,
            session=session,
            persistence=self.persistence
        )
        client_handler = ClientToAgentHandler(
            websocket=websocket,
            session=session
        )

        # Run both handlers concurrently
        tasks = [
            asyncio.create_task(agent_handler.run()),
            asyncio.create_task(client_handler.run())
        ]

        await asyncio.gather(*tasks, return_exceptions=True)


def decode_business_context(encoded: Optional[str]) -> Optional[Dict[str, Any]]:
    """
    Decode business context from URL-encoded base64 JSON.

    Args:
        encoded: URL-encoded base64 JSON string

    Returns:
        Decoded business context dict, or None if decoding fails
    """
    if not encoded:
        return None

    try:
        import urllib.parse
        decoded_str = urllib.parse.unquote(encoded)
        return json.loads(base64.b64decode(decoded_str))
    except Exception as e:
        logger.error(f"Error decoding business context: {e}")
        return None


# Default handler instance
connection_handler = WebSocketConnectionHandler()
