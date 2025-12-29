"""
WebSocket handling module.
Connection management and bidirectional messaging.
"""
from .protocol import (
    MessageType,
    IncomingMessage,
    OutgoingMessage,
    create_tool_call_message,
    create_tool_result_message,
    create_state_update_message,
    create_text_message,
    create_audio_message,
    create_connection_message,
    create_turn_complete_message,
    create_interrupted_message,
    create_error_message,
    create_pong_message
)
from .messaging import (
    SafeWebSocket,
    ConversationStateTracker,
    AgentToClientHandler,
    ClientToAgentHandler
)
from .handlers import (
    WebSocketConnectionHandler,
    decode_business_context,
    connection_handler
)

__all__ = [
    # Protocol
    'MessageType',
    'IncomingMessage',
    'OutgoingMessage',
    'create_tool_call_message',
    'create_tool_result_message',
    'create_state_update_message',
    'create_text_message',
    'create_audio_message',
    'create_connection_message',
    'create_turn_complete_message',
    'create_interrupted_message',
    'create_error_message',
    'create_pong_message',
    # Messaging
    'SafeWebSocket',
    'ConversationStateTracker',
    'AgentToClientHandler',
    'ClientToAgentHandler',
    # Handlers
    'WebSocketConnectionHandler',
    'decode_business_context',
    'connection_handler',
]
