"""
Tool registry for agent configuration.
Centralizes tool registration and management.
"""
from typing import List, Callable, Dict, Any
from google.genai import types

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


class ToolRegistry:
    """Registry for managing agent configuration tools."""

    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._register_default_tools()

    def _register_default_tools(self) -> None:
        """Register all default configuration tools."""
        self._tools = {
            'get_agent_name': get_agent_name,
            'get_agent_gender': get_agent_gender,
            'get_personality': get_personality,
            'get_languages': get_languages,
            'get_dialect': get_dialect,
            'get_interaction_steps': get_interaction_steps,
            'get_conversation_examples': get_conversation_examples,
            'get_handover_reasons': get_handover_reasons,
            'get_additional_instructions': get_additional_instructions,
            'conversation_complete': conversation_complete,
        }

    def register(self, name: str, tool_func: Callable) -> None:
        """Register a custom tool."""
        self._tools[name] = tool_func

    def get(self, name: str) -> Callable:
        """Get a tool by name."""
        return self._tools.get(name)

    def get_all(self) -> List[Callable]:
        """Get all registered tools as a list."""
        return list(self._tools.values())

    def get_names(self) -> List[str]:
        """Get all registered tool names."""
        return list(self._tools.keys())


def get_tool_declarations() -> List[types.FunctionDeclaration]:
    """Get function declarations for all tools."""
    return [
        types.FunctionDeclaration(
            name="get_agent_name",
            description="Captures the desired name for the AI agent. Call this when the user provides a name for their agent.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "agent_name": types.Schema(
                        type=types.Type.STRING,
                        description="The name the user wants for their AI agent"
                    )
                },
                required=["agent_name"]
            )
        ),
        types.FunctionDeclaration(
            name="get_agent_gender",
            description="Sets the gender of the AI agent based on the name or user preference.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "gender": types.Schema(
                        type=types.Type.STRING,
                        description=f"The gender of the agent. Must be one of: {', '.join(VALID_GENDERS)}",
                        enum=VALID_GENDERS
                    )
                },
                required=["gender"]
            )
        ),
        types.FunctionDeclaration(
            name="get_personality",
            description="Captures the personality style for the AI agent. Call this when the user specifies or agrees to a personality type.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "personality": types.Schema(
                        type=types.Type.STRING,
                        description=f"The personality type. Must be one of: {', '.join(VALID_PERSONALITIES)}",
                        enum=VALID_PERSONALITIES
                    )
                },
                required=["personality"]
            )
        ),
        types.FunctionDeclaration(
            name="get_languages",
            description="Captures the language(s) the AI agent should support.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "languages": types.Schema(
                        type=types.Type.ARRAY,
                        items=types.Schema(
                            type=types.Type.STRING,
                            enum=VALID_LANGUAGES
                        ),
                        description=f"List of languages. Valid options: {', '.join(VALID_LANGUAGES)}"
                    )
                },
                required=["languages"]
            )
        ),
        types.FunctionDeclaration(
            name="get_dialect",
            description="Captures the Arabic dialect for the AI agent. Only call this if Arabic is selected as a language.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "dialect": types.Schema(
                        type=types.Type.STRING,
                        description=f"The Arabic dialect. Must be one of: {', '.join(VALID_DIALECTS)}",
                        enum=VALID_DIALECTS
                    )
                },
                required=["dialect"]
            )
        ),
        types.FunctionDeclaration(
            name="get_interaction_steps",
            description="Captures the step-by-step interaction flow for the AI agent.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "interaction_steps": types.Schema(
                        type=types.Type.ARRAY,
                        items=types.Schema(type=types.Type.STRING),
                        description=f"List of interaction steps (max {MAX_INTERACTION_STEPS})"
                    )
                },
                required=["interaction_steps"]
            )
        ),
        types.FunctionDeclaration(
            name="get_conversation_examples",
            description="Captures sample customer-agent dialogues to train the AI on the brand's voice.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "conversation_examples": types.Schema(
                        type=types.Type.ARRAY,
                        items=types.Schema(
                            type=types.Type.OBJECT,
                            properties={
                                "customer_message": types.Schema(
                                    type=types.Type.STRING,
                                    description="What the customer says"
                                ),
                                "agent_response": types.Schema(
                                    type=types.Type.STRING,
                                    description="How the agent should respond"
                                )
                            },
                            required=["customer_message", "agent_response"]
                        ),
                        description=f"List of conversation examples (max {MAX_CONVERSATION_EXAMPLES})"
                    )
                },
                required=["conversation_examples"]
            )
        ),
        types.FunctionDeclaration(
            name="get_handover_reasons",
            description="Configures when the AI agent should transfer the conversation to a human.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "handover_reasons": types.Schema(
                        type=types.Type.ARRAY,
                        items=types.Schema(
                            type=types.Type.OBJECT,
                            properties={
                                "reason": types.Schema(
                                    type=types.Type.STRING,
                                    description="Short name for the trigger"
                                ),
                                "description": types.Schema(
                                    type=types.Type.STRING,
                                    description="When this trigger should activate"
                                )
                            },
                            required=["reason", "description"]
                        ),
                        description=f"List of handover reasons (max {MAX_HANDOVER_REASONS})"
                    )
                },
                required=["handover_reasons"]
            )
        ),
        types.FunctionDeclaration(
            name="get_additional_instructions",
            description="Sets any custom behavioral instructions for the AI agent.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "instructions": types.Schema(
                        type=types.Type.STRING,
                        description=f"Custom instructions (max {MAX_ADDITIONAL_INSTRUCTIONS_LENGTH} chars)"
                    )
                },
                required=["instructions"]
            )
        ),
        types.FunctionDeclaration(
            name="conversation_complete",
            description="Signals that the onboarding conversation is complete.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "reason": types.Schema(
                        type=types.Type.STRING,
                        description="Why the conversation is ending (e.g., 'setup_complete', 'user_requested')"
                    )
                },
                required=["reason"]
            )
        ),
    ]



tool_registry = ToolRegistry()
