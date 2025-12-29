from typing import Dict, Any, List
from google.adk.tools import ToolContext, FunctionTool
def get_additional_instructions(
        instructions: str,
        tool_context: ToolContext
) -> Dict[str, Any]:
    """
    Sets custom behavioral instructions for the AI agent.

    These instructions control how the agent behaves, responds, and handles
    various situations beyond the standard configuration.

    Args:
        instructions: Custom instructions in English that define agent behavior.
                     The AI agent translates non-English input before calling this tool.
        tool_context: Context object containing session state

    Returns:
        Success: {'status': 'success', 'instructions': '...', 'message': 'Instructions set'}
        Error: {'status': 'error', 'error_message': '...'}
    """

    # Validate input
    if not instructions or not instructions.strip():
        return {
            "status": "error",
            "error_message": "Instructions cannot be empty."
        }

    cleaned_instructions = instructions.strip()

    # Optional: Check length
    if len(cleaned_instructions) > 2000:
        return {
            "status": "warning",
            "instructions": cleaned_instructions,
            "message": "⚠️ Long instructions (>2000 chars) may affect agent response time."
        }

    # Store instructions
    tool_context.state["additional_instructions"] = cleaned_instructions

    conversation_state = tool_context.state.get("conversation_state", {})
    conversation_state["additional_instructions"] = cleaned_instructions
    tool_context.state["conversation_state"] = conversation_state

    return {
        "status": "success",
        "instructions": cleaned_instructions,
        "character_count": len(cleaned_instructions),
        "message": "Additional instructions configured successfully"
    }



