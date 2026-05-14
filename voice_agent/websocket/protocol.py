"""
WebSocket message types and encoding.
Defines the protocol for client-server communication.
"""
import base64
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any, List


class MessageType(str, Enum):
    """Types of WebSocket messages."""
    # Incoming from client
    TEXT_INPUT = "text/plain"
    AUDIO_INPUT = "audio/pcm"
    USER_SPEAKING = "user_speaking"
    PING = "ping"

    # Outgoing to client
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    STATE_UPDATE = "state_update"
    TURN_COMPLETE = "turn_complete"
    INTERRUPTED = "interrupted"
    ERROR = "error"
    PONG = "pong"
    CONNECTED = "connected"


@dataclass
class IncomingMessage:
    """Parsed incoming WebSocket message."""
    type: MessageType
    data: Any
    mime_type: Optional[str] = None

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> "IncomingMessage":
        """Parse incoming JSON message."""
        mime_type = data.get("mime_type", "")
        content_data = data.get("data", "")
        msg_type = data.get("type", "")

        if mime_type == "text/plain":
            return cls(
                type=MessageType.TEXT_INPUT,
                data=content_data,
                mime_type=mime_type
            )
        elif mime_type == "audio/pcm":
            # Decode base64 audio
            audio_bytes = base64.b64decode(content_data)
            return cls(
                type=MessageType.AUDIO_INPUT,
                data=audio_bytes,
                mime_type=mime_type
            )
        elif msg_type == "user_speaking":
            return cls(type=MessageType.USER_SPEAKING, data=None)
        elif msg_type == "ping":
            return cls(type=MessageType.PING, data=None)
        else:
            raise ValueError(f"Unknown message type: {mime_type or msg_type}")


@dataclass
class OutgoingMessage:
    """Outgoing WebSocket message."""
    type: MessageType
    data: Dict[str, Any]

    def to_json(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return self.data


def create_tool_call_message(
    tool_name: str,
    tool_id: str,
    arguments: Dict[str, Any]
) -> Dict[str, Any]:
    """Create tool call notification message."""
    return {
        "type": "tool_call",
        "tool_name": tool_name,
        "tool_id": tool_id,
        "arguments": arguments
    }


def create_tool_result_message(
    tool_name: str,
    tool_id: str,
    result: Dict[str, Any]
) -> Dict[str, Any]:
    """Create tool result message."""
    return {
        "type": "tool_result",
        "tool_name": tool_name,
        "tool_id": tool_id,
        "result": result
    }


def create_state_update_message(
    conversation_state: Dict[str, Any]
) -> Dict[str, Any]:
    """Create state update message."""
    return {
        "type": "state_update",
        "conversation_state": conversation_state
    }


def create_text_message(
    text: str,
    partial: bool = False
) -> Dict[str, Any]:
    """Create text response message."""
    return {
        "mime_type": "text/plain",
        "data": text,
        "partial": partial
    }


def create_audio_message(
    audio_data: bytes,
    mime_type: str
) -> Dict[str, Any]:
    """Create audio response message."""
    return {
        "mime_type": mime_type,
        "data": base64.b64encode(audio_data).decode()
    }


def create_connection_message(
    session_id: str,
    audio_enabled: bool
) -> Dict[str, Any]:
    """Create connection confirmation message."""
    return {
        "connected": True,
        "session_id": session_id,
        "audio_enabled": audio_enabled
    }


def create_turn_complete_message() -> Dict[str, Any]:
    """Create turn complete message."""
    return {"turn_complete": True}


def create_interrupted_message() -> Dict[str, Any]:
    """Create interruption message."""
    return {"interrupted": True}


def create_error_message(error: str) -> Dict[str, Any]:
    """Create error message."""
    return {"error": error}


def create_pong_message() -> Dict[str, Any]:
    """Create pong response message."""
    return {"type": "pong"}
