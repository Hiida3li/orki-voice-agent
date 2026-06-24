"""
Voice agent configuration tools.
Provides tools for collecting agent configuration through voice conversation.
"""
from .constants import (
    VALID_PERSONALITIES,
    VALID_LANGUAGES,
    VALID_DIALECTS,
    VALID_GENDERS,
    MAX_INTERACTION_STEPS,
    MAX_CONVERSATION_EXAMPLES,
    MAX_HANDOVER_REASONS,
    MAX_ADDITIONAL_INSTRUCTIONS_LENGTH
)

from .base import (
    ValidationResult,
    ToolValidator,
    StateUpdater,
    create_success_response,
    create_error_response
)

from .configuration import (
    get_agent_name,
    get_agent_gender,
    get_personality,
    get_languages,
    get_dialect,
    get_interaction_steps,
    get_conversation_examples,
    get_handover_reasons,
    get_additional_instructions,
    conversation_complete
)

from .registry import (
    ToolRegistry,
    tool_registry,
    get_tool_declarations
)


__all__ = [

    'VALID_PERSONALITIES',
    'VALID_LANGUAGES',
    'VALID_DIALECTS',
    'VALID_GENDERS',
    'MAX_INTERACTION_STEPS',
    'MAX_CONVERSATION_EXAMPLES',
    'MAX_HANDOVER_REASONS',
    'MAX_ADDITIONAL_INSTRUCTIONS_LENGTH',

    'ValidationResult',
    'ToolValidator',
    'StateUpdater',
    'create_success_response',
    'create_error_response',

    'get_agent_name',
    'get_agent_gender',
    'get_personality',
    'get_languages',
    'get_dialect',
    'get_interaction_steps',
    'get_conversation_examples',
    'get_handover_reasons',
    'get_additional_instructions',
    'conversation_complete',

    'ToolRegistry',
    'tool_registry',
    'get_tool_declarations',
]
