"""
Agent configuration tools.
Tools for collecting agent configuration through voice conversation.
"""
import datetime
from typing import Dict, Any, List
from google.adk.tools import ToolContext

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
    ToolValidator,
    StateUpdater,
    create_success_response,
    create_error_response
)


validator = ToolValidator()
state_updater = StateUpdater()


def get_agent_name(agent_name: str, tool_context: ToolContext) -> Dict[str, Any]:
    """Captures the desired name for the AI agent."""
    result = validator.validate_non_empty_string(agent_name, "Agent name")
    if not result.valid:
        return result.to_error_response()
    
    name = agent_name.strip()
    state_updater.update(tool_context, "agent_name", name)
    
    return create_success_response("agent_name", name, f"Agent name set to '{name}'")


def get_agent_gender(gender: str, tool_context: ToolContext) -> Dict[str, Any]:
    """Sets the gender of the AI agent."""
    result = validator.validate_enum(gender, VALID_GENDERS, "gender")
    if not result.valid:
        return result.to_error_response()
    
    state_updater.update(tool_context, "agent_gender", gender)
    
    return create_success_response("gender", gender, f"Agent gender set to '{gender}'")


def get_personality(personality: str, tool_context: ToolContext) -> Dict[str, Any]:
    """Captures the personality style for the AI agent."""
    result = validator.validate_enum(personality, VALID_PERSONALITIES, "personality")
    if not result.valid:
        return result.to_error_response()
    
    state_updater.update(tool_context, "personality", personality)
    
    return create_success_response("personality", personality, f"Personality set to '{personality}'")


def get_languages(languages: List[str], tool_context: ToolContext) -> Dict[str, Any]:
    """Captures the language(s) the AI agent should support."""
    result = validator.validate_list_items(languages, VALID_LANGUAGES, "languages")
    if not result.valid:
        return result.to_error_response()
    
    state_updater.update(tool_context, "languages", languages)
    
    requires_dialect = "Arabic" in languages
    message = f"Languages set to: {', '.join(languages)}"
    if requires_dialect:
        message += " - Arabic dialect required"
    
    return create_success_response(
        "languages", languages, message,
        requires_dialect=requires_dialect
    )


def get_dialect(dialect: str, tool_context: ToolContext) -> Dict[str, Any]:
    """Captures the Arabic dialect for the AI agent."""
    # Check if Arabic is selected
    languages = tool_context.state.get("languages", [])
    if "Arabic" not in languages:
        return create_error_response(
            "Dialect can only be set if Arabic is selected as a language."
        )
    
    result = validator.validate_enum(dialect, VALID_DIALECTS, "dialect")
    if not result.valid:
        return result.to_error_response()
    
    state_updater.update(tool_context, "dialect", dialect)
    
    return create_success_response("dialect", dialect, f"Arabic dialect set to '{dialect}'")


def get_interaction_steps(interaction_steps: List[str], tool_context: ToolContext) -> Dict[str, Any]:
    """Captures the step-by-step interaction flow for the AI agent."""
    if not isinstance(interaction_steps, list):
        return create_error_response(
            f"Expected list, got {type(interaction_steps).__name__}"
        )
    
    result = validator.validate_list_length(
        interaction_steps, "interaction_steps", 
        min_length=1, max_length=MAX_INTERACTION_STEPS
    )
    if not result.valid:
        return result.to_error_response()
    
    # Validate each step is non-empty string
    for i, step in enumerate(interaction_steps, 1):
        if not isinstance(step, str) or not step.strip():
            return create_error_response(f"Step {i} must be a non-empty string.")
    
    cleaned_steps = [step.strip() for step in interaction_steps]
    state_updater.update(tool_context, "interaction_steps", cleaned_steps)
    
    status = "success"
    message = f"Interaction steps configured with {len(cleaned_steps)} steps"
    if len(cleaned_steps) > 5:
        status = "warning"
        message = f" {len(cleaned_steps)} steps configured. Consider consolidating (recommended: 2-5)"
    
    return {
        "status": status,
        "interaction_steps": cleaned_steps,
        "step_count": len(cleaned_steps),
        "message": message
    }


def get_conversation_examples(
    conversation_examples: List[Dict[str, str]], 
    tool_context: ToolContext
) -> Dict[str, Any]:
    """Captures sample customer-agent dialogues."""
    if not isinstance(conversation_examples, list):
        return create_error_response(
            f"Expected list, got {type(conversation_examples).__name__}"
        )
    
    result = validator.validate_dict_list(
        conversation_examples,
        required_keys=["customer_message", "agent_response"],
        field_name="conversation_examples"
    )
    if not result.valid:
        return result.to_error_response()
    
    # Clean and validate each example
    validated = []
    for i, ex in enumerate(conversation_examples, 1):
        customer_msg = str(ex["customer_message"]).strip()
        agent_resp = str(ex["agent_response"]).strip()
        
        if not customer_msg or not agent_resp:
            return create_error_response(f"Example {i} has empty message or response.")
        
        validated.append({
            "customer_message": customer_msg,
            "agent_response": agent_resp
        })
    
    state_updater.update(tool_context, "conversation_examples", validated)
    
    status = "success"
    message = f"{len(validated)} conversation examples saved"
    if len(validated) > MAX_CONVERSATION_EXAMPLES:
        status = "warning"
        message = f" {len(validated)} examples saved. Consider using 3-5 key examples."
    
    return {
        "status": status,
        "conversation_examples": validated,
        "example_count": len(validated),
        "message": message
    }


def get_handover_reasons(
    handover_reasons: List[Dict[str, str]], 
    tool_context: ToolContext
) -> Dict[str, Any]:
    """Configures when the AI agent should transfer to a human."""
    if not isinstance(handover_reasons, list):
        return create_error_response(
            f"Expected list, got {type(handover_reasons).__name__}"
        )
    
    result = validator.validate_dict_list(
        handover_reasons,
        required_keys=["reason", "description"],
        field_name="handover_reasons"
    )
    if not result.valid:
        return result.to_error_response()
    
    # Clean and validate each reason
    validated = []
    for i, hr in enumerate(handover_reasons, 1):
        reason = str(hr["reason"]).strip()
        description = str(hr["description"]).strip()
        
        if not reason or not description:
            return create_error_response(f"Handover reason {i} has empty reason or description.")
        
        validated.append({"reason": reason, "description": description})
    
    state_updater.update(tool_context, "handover_reasons", validated)
    
    status = "success"
    message = f"{len(validated)} handover reasons configured"
    if len(validated) > MAX_HANDOVER_REASONS:
        status = "warning"
        message = f" {len(validated)} reasons configured. Consider using 3-5 key scenarios."
    
    return {
        "status": status,
        "handover_reasons": validated,
        "reason_count": len(validated),
        "message": message
    }


def get_additional_instructions(
    instructions: str, 
    tool_context: ToolContext
) -> Dict[str, Any]:
    """Sets custom behavioral instructions for the AI agent."""
    result = validator.validate_non_empty_string(instructions, "Instructions")
    if not result.valid:
        return result.to_error_response()
    
    cleaned = instructions.strip()
    
    state_updater.update(tool_context, "additional_instructions", cleaned)
    
    status = "success"
    message = "Additional instructions configured successfully"
    if len(cleaned) > MAX_ADDITIONAL_INSTRUCTIONS_LENGTH:
        status = "warning"
        message = f" Long instructions ({len(cleaned)} chars) may affect response time."
    
    return {
        "status": status,
        "instructions": cleaned,
        "character_count": len(cleaned),
        "message": message
    }


def conversation_complete(reason: str, tool_context: ToolContext) -> Dict[str, Any]:
    """Signals that the conversation is complete."""
    tool_context.state["conversation_complete"] = True
    tool_context.state["completion_reason"] = reason
    
    conversation_state = tool_context.state.get("conversation_state", {})
    conversation_state["completed_at"] = datetime.datetime.now().isoformat()
    conversation_state["completion_reason"] = reason
    tool_context.state["conversation_state"] = conversation_state
    
    return {
        "status": "success",
        "completed": True,
        "message": "Conversation completed. Thank you for configuring your agent!",
        "final_config": conversation_state
    }
