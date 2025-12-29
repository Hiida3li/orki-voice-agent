"""
Agent Configuration Tools for Voice-to-Voice AI Agent
"""

from typing import Dict, Any, List
from google.adk.tools import ToolContext, FunctionTool

VALID_PERSONALITIES = [
    "Empathetic and Friendly",
    "Formal and Professional",
    "Salesperson",
    "Fun and Humorous",
    "Casual and Down-To-Earth"
]

VALID_LANGUAGES = [
    "English",
    "Arabic",
    "Hindi",
    "Urdu"
]

VALID_DIALECTS = [
    "Omani",
    "Saudi",
    "Bahraini",
    "Kuwaiti",
    "Qatari",
    "Emirati",
    "Fusha (MSA)"

]


def get_agent_name(agent_name: str, tool_context: ToolContext) -> Dict[str, Any]:
    """
    Captures the desired name for the AI agent being configured.

    Use this tool when the user provides or confirms the name they want to give
    to their AI agent. This is typically the first piece of information gathered.

    Args:
        agent_name: The name the user wants to give to their AI agent (e.g., "Ali", "CustomerServiceBot", "Maya")
        tool_context: Context object containing session state and conversation information

    Returns:
        A dictionary indicating the outcome.
        On success, status is 'success' and includes 'agent_name' and 'message'.
        Example: {'status': 'success', 'agent_name': 'Ali', 'message': 'Agent name set to Ali'}
    """
    if not agent_name or not agent_name.strip():
        return {
            "status": "error",
            "error_message": "Agent name cannot be empty. Please provide a valid name."
        }

    agent_name = agent_name.strip()

    tool_context.state["agent_name"] = agent_name

    conversation_state = tool_context.state.get("conversation_state", {})
    conversation_state["agent_name"] = agent_name
    tool_context.state["conversation_state"] = conversation_state

    return {
        "status": "success",
        "agent_name": agent_name,
        "message": f"Agent name set to '{agent_name}'"
    }


def get_agent_gender(gender: str, tool_context: ToolContext) -> Dict[str, Any]:
    """
    Sets the gender of the AI agent based on the voice agent's determination.

    The voice agent analyzes the name and determines if it's typically male or female,
    then calls this tool with the determined gender.

    IMPORTANT: This tool should be called IMMEDIATELY after get_agent_name is called.

    Args:
        gender: The gender determined by the voice agent ("Male" or "Female")
        tool_context: Context object containing session state

    Returns:
        A dictionary confirming the gender setting.
        Example: {'status': 'success', 'gender': 'Female', 'message': 'Agent gender set to Female'}
    """

    # Validate input
    valid_genders = ["Male", "Female"]
    if gender not in valid_genders:
        return {
            "status": "error",
            "error_message": f"Invalid gender. Must be 'Male' or 'Female', received: {gender}"
        }

    # Store in session state
    tool_context.state["agent_gender"] = gender

    # Update conversation state
    conversation_state = tool_context.state.get("conversation_state", {})
    conversation_state["agent_gender"] = gender
    tool_context.state["conversation_state"] = conversation_state

    return {
        "status": "success",
        "gender": gender,
        "message": f"Agent gender set to '{gender}'"
    }


def get_personality(personality: str, tool_context: ToolContext) -> Dict[str, Any]:
    """
    Captures the personality style for the AI agent.

    Use this tool when the user selects or confirms the personality type for their agent.
    The personality determines how the agent communicates with customers.
    Only ONE personality can be selected from the valid options.

    Args:
        personality: The selected personality type. Must be one of:
                    - "Empathetic and Friendly"
                    - "Formal and Professional"
                    - "Salesperson"
                    - "Fun and Humorous"
                    - "Casual and Down-To-Earth"

    Returns:
        A dictionary indicating the outcome.
        On success, status is 'success' and includes 'personality' and 'message'.
        On failure, status is 'error' and includes 'error_message' with valid options.
        Example success: {'status': 'success', 'personality': 'Empathetic and Friendly', 'message': '...'}
        Example error: {'status': 'error', 'error_message': 'Invalid personality. Must be one of: ...'}
    """
    # Validate personality is in valid options
    if personality not in VALID_PERSONALITIES:
        return {
            "status": "error",
            "error_message": f"Invalid personality. Must be one of: {', '.join(VALID_PERSONALITIES)}"
        }

    # Store in session state
    tool_context.state["personality"] = personality

    # Update conversation state
    conversation_state = tool_context.state.get("conversation_state", {})
    conversation_state["personality"] = personality
    tool_context.state["conversation_state"] = conversation_state

    return {
        "status": "success",
        "personality": personality,
        "message": f"Personality set to '{personality}'"
    }


def get_languages(languages: List[str], tool_context: ToolContext) -> Dict[str, Any]:
    """
    Captures the language(s) the AI agent should support.

    Use this tool when the user selects or confirms the languages their agent should speak.
    The agent must support at least ONE language, but can support multiple languages.

    Args:
        languages: List of selected languages. Can select multiple. Must include at least one of:
                  - "English"
                  - "Arabic"
                  - "Hindi"
                  - "Urdu"
                  Example: ["English", "Arabic"] or ["Hindi"]

    Returns:
        A dictionary indicating the outcome.
        On success, status is 'success' and includes 'languages', 'message', and 'requires_dialect' flag.
        On failure, status is 'error' and includes 'error_message'.
        Example success: {'status': 'success', 'languages': ['English', 'Arabic'], 'requires_dialect': True, 'message': '...'}
        Example error: {'status': 'error', 'error_message': 'At least one language must be selected'}
    """
    # Validate at least one language
    if not languages or len(languages) == 0:
        return {
            "status": "error",
            "error_message": "At least one language must be selected"
        }

    # Validate all languages are valid
    invalid_languages = [lang for lang in languages if lang not in VALID_LANGUAGES]
    if invalid_languages:
        return {
            "status": "error",
            "error_message": f"Invalid language(s): {', '.join(invalid_languages)}. Valid options: {', '.join(VALID_LANGUAGES)}"
        }

    # Store in session state
    tool_context.state["languages"] = languages

    # Update conversation state
    conversation_state = tool_context.state.get("conversation_state", {})
    conversation_state["languages"] = languages
    tool_context.state["conversation_state"] = conversation_state

    # Check if Arabic is selected (requires dialect)
    requires_dialect = "Arabic" in languages

    return {
        "status": "success",
        "languages": languages,
        "requires_dialect": requires_dialect,
        "message": f"Languages set to: {', '.join(languages)}" +
                   (" - Arabic dialect required" if requires_dialect else "")
    }


def get_dialect(dialect: str, tool_context: ToolContext) -> Dict[str, Any]:
    """
    Captures the Arabic dialect for the AI agent.

    IMPORTANT: This tool should ONLY be called if the user has selected "Arabic"
    as one of their languages. If Arabic was not selected, return an error.
    Only ONE dialect can be selected from the valid options.

    Args:
        dialect: The selected Arabic dialect. Must be one of:
                - "Omani"
                - "Saudi"
                - "Bahraini"
                - "Kuwaiti"
                - "Qatari"
                - "Emirati"
                - "Fusha (MSA)"


    Returns:
        A dictionary indicating the outcome.
        On success, status is 'success' and includes 'dialect' and 'message'.
        On failure, status is 'error' and includes 'error_message'.
        Example success: {'status': 'success', 'dialect': 'Omani', 'message': 'Arabic dialect set to Omani'}
        Example error: {'status': 'error', 'error_message': 'Dialect can only be set if Arabic is selected as a language'}
    """
    # Check if Arabic is in the selected languages
    languages = tool_context.state.get("languages", [])
    if "Arabic" not in languages:
        return {
            "status": "error",
            "error_message": "Dialect can only be set if Arabic is selected as a language. Please ask user to select Arabic first."
        }

    # Validate dialect is in valid options
    if dialect not in VALID_DIALECTS:
        return {
            "status": "error",
            "error_message": f"Invalid dialect. Must be one of: {', '.join(VALID_DIALECTS)}"
        }

    # Store in session state
    tool_context.state["dialect"] = dialect

    # Update conversation state
    conversation_state = tool_context.state.get("conversation_state", {})
    conversation_state["dialect"] = dialect
    tool_context.state["conversation_state"] = conversation_state

    return {
        "status": "success",
        "dialect": dialect,
        "message": f"Arabic dialect set to '{dialect}'"
    }


def get_interaction_steps(interaction_steps: List[str], tool_context: ToolContext) -> Dict[str, Any]:
    """
    Captures the step-by-step interaction flow for the AI agent.

    This defines the sequence of actions the agent should follow during each customer interaction,
    such as identifying intent, guiding the conversation, and collecting information.

    Use this tool when the user defines or confirms the interaction steps for their agent.

    Args:
        interaction_steps: List of step descriptions defining the agent's interaction flow.
                          Each step should describe a specific action or stage in the conversation.
                          Must contain at least 1 step, recommended 2-5 steps.
                          Example: [
                              "Step 1: Identify the customer's intent by asking a simple, open-ended question",
                              "Step 2: Guide the conversation toward useful options",
                              "Step 3: Collect necessary information: name, contact details, location"
                          ]
        tool_context: Context object containing session state and conversation information

    Returns:
        A dictionary indicating the outcome.
        On success, status is 'success' and includes 'interaction_steps', 'step_count', and 'message'.
        On failure, status is 'error' and includes 'error_message'.
        Example success: {
            'status': 'success',
            'interaction_steps': ['Step 1: ...', 'Step 2: ...'],
            'step_count': 2,
            'message': 'Interaction steps configured with 2 steps'
        }
        Example error: {
            'status': 'error',
            'error_message': 'At least one interaction step must be provided'
        }
    """
    # Type checking - ensure it's a list
    if not isinstance(interaction_steps, list):
        return {
            "status": "error",
            "error_message": f"Invalid input type. Expected list, got {type(interaction_steps).__name__}. Please provide steps as a list."
        }

    # Validate input - must have at least 1 step
    if not interaction_steps or len(interaction_steps) == 0:
        return {
            "status": "error",
            "error_message": "At least one interaction step must be provided. Please define the conversation flow."
        }

    # Validate each step is a string and not empty
    for i, step in enumerate(interaction_steps, 1):
        if not isinstance(step, str):
            return {
                "status": "error",
                "error_message": f"Step {i} is not a string (type: {type(step).__name__}). All steps must be text strings."
            }
        if not step or not step.strip():
            return {
                "status": "error",
                "error_message": f"Step {i} is empty. Each step must have content."
            }

    cleaned_steps = [step.strip() for step in interaction_steps]

    if len(cleaned_steps) > 10:
        return {
            "status": "warning",
            "interaction_steps": cleaned_steps,
            "step_count": len(cleaned_steps),
            "message": f"⚠️  {len(cleaned_steps)} steps configured. Consider consolidating for clarity (recommended: 2-5 steps)."
        }

    # Store in session state
    tool_context.state["interaction_steps"] = cleaned_steps

    # Update conversation state
    conversation_state = tool_context.state.get("conversation_state", {})
    conversation_state["interaction_steps"] = cleaned_steps
    tool_context.state["conversation_state"] = conversation_state

    return {
        "status": "success",
        "interaction_steps": cleaned_steps,
        "step_count": len(cleaned_steps),
        "message": f"Interaction steps configured with {len(cleaned_steps)} step{'s' if len(cleaned_steps) != 1 else ''}"
    }


def get_conversation_examples(conversation_examples: List[Dict[str, str]], tool_context: ToolContext) -> Dict[str, Any]:
    """
    Captures sample customer-agent dialogues that demonstrate the brand's voice and communication style.

    These examples help the AI understand and mirror the exact tone, wording, and style the business
    wants to use with customers. Each example should show how the agent responds to different
    customer scenarios.

    Use this tool when the user provides sample conversations that illustrate their brand voice.

    Args:
        conversation_examples: List of conversation example objects. Each object should have:
                              - "customer_message": The customer's message/question
                              - "agent_response": How the agent should respond

                              Example: [
                                  {
                                      "customer_message": "Hi, I saw your cake post on Instagram. Is it still available?",
                                      "agent_response": "Hi there! Yes, it's available. Would you prefer 1kg or 2kg?"
                                  },
                                  {
                                      "customer_message": "Can I get a discount on bulk orders?",
                                      "agent_response": "Definitely! I can offer bundle pricing or free delivery depending on your total."
                                  }
                              ]

                              Recommended: 2-5 examples covering different scenarios
        tool_context: Context object containing session state

    Returns:
        A dictionary indicating the outcome.
        On success, status is 'success' and includes 'conversation_examples', 'example_count', and 'message'.
        On failure, status is 'error' and includes 'error_message'.
        Example success: {
            'status': 'success',
            'conversation_examples': [...],
            'example_count': 3,
            'message': '3 conversation examples saved'
        }
    """
    if not isinstance(conversation_examples, list):
        return {
            "status": "error",
            "error_message": f"Invalid input type. Expected list, got {type(conversation_examples).__name__}."
        }

    if not conversation_examples or len(conversation_examples) == 0:
        return {
            "status": "error",
            "error_message": "At least one conversation example must be provided."
        }

    # Validate each example
    validated_examples = []
    for i, example in enumerate(conversation_examples, 1):
        if not isinstance(example, dict):
            return {
                "status": "error",
                "error_message": f"Example {i} is not a valid object (type: {type(example).__name__})."
            }

        # Check required fields
        if "customer_message" not in example:
            return {
                "status": "error",
                "error_message": f"Example {i} is missing 'customer_message' field."
            }

        if "agent_response" not in example:
            return {
                "status": "error",
                "error_message": f"Example {i} is missing 'agent_response' field."
            }

        # Validate fields are not empty
        customer_msg = example["customer_message"].strip() if isinstance(example["customer_message"], str) else ""
        agent_resp = example["agent_response"].strip() if isinstance(example["agent_response"], str) else ""

        if not customer_msg:
            return {
                "status": "error",
                "error_message": f"Example {i} has empty customer message."
            }

        if not agent_resp:
            return {
                "status": "error",
                "error_message": f"Example {i} has empty agent response."
            }

        validated_examples.append({
            "customer_message": customer_msg,
            "agent_response": agent_resp
        })

    # Warn if too many examples
    if len(validated_examples) > 10:
        return {
            "status": "warning",
            "conversation_examples": validated_examples,
            "example_count": len(validated_examples),
            "message": f" {len(validated_examples)} examples saved. Consider using 3-5 key examples for clarity."
        }

    # Store in session state
    tool_context.state["conversation_examples"] = validated_examples

    # Update conversation state
    conversation_state = tool_context.state.get("conversation_state", {})
    conversation_state["conversation_examples"] = validated_examples
    tool_context.state["conversation_state"] = conversation_state

    return {
        "status": "success",
        "conversation_examples": validated_examples,
        "example_count": len(validated_examples),
        "message": f"{len(validated_examples)} conversation example{'s' if len(validated_examples) != 1 else ''} saved to capture your brand voice"
    }


def get_handover_reasons(handover_reasons: List[Dict[str, str]], tool_context: ToolContext) -> Dict[str, Any]:
    """
    Configures when the AI agent should transfer the conversation to a human agent.

    Handover reasons define specific scenarios where the AI recognizes it needs human
    intervention, such as frustrated customers, explicit requests for humans, or
    insufficient information to help.

    Use this tool when the user defines scenarios where the agent should escalate to a human.

    Args:
        handover_reasons: List of handover reason objects. Each object must have:
                         - "reason": Short name/title of the handover reason
                         - "description": When this handover should trigger

                         Example: [
                             {
                                 "reason": "Customer Frustration",
                                 "description": "When the customer expresses frustration, anger, or dissatisfaction multiple times"
                             },
                             {
                                 "reason": "Human Request",
                                 "description": "When the customer explicitly asks to speak with a human agent"
                             },
                             {
                                 "reason": "Complex Issue",
                                 "description": "When the issue requires specialized knowledge beyond the AI's capabilities"
                             }
                         ]

                         Recommended: 2-5 handover reasons covering common escalation scenarios
        tool_context: Context object containing session state

    Returns:
        A dictionary indicating the outcome.
        On success, status is 'success' and includes 'handover_reasons', 'reason_count', and 'message'.
        On failure, status is 'error' and includes 'error_message'.
        Example success: {
            'status': 'success',
            'handover_reasons': [...],
            'reason_count': 3,
            'message': '3 handover reasons configured'
        }
    """
    if not isinstance(handover_reasons, list):
        return {
            "status": "error",
            "error_message": f"Invalid input type. Expected list, got {type(handover_reasons).__name__}."
        }

    if not handover_reasons or len(handover_reasons) == 0:
        return {
            "status": "error",
            "error_message": "At least one handover reason must be provided."
        }

    validated_reasons = []
    for i, reason_obj in enumerate(handover_reasons, 1):
        if not isinstance(reason_obj, dict):
            return {
                "status": "error",
                "error_message": f"Handover reason {i} is not a valid object (type: {type(reason_obj).__name__})."
            }


        if "reason" not in reason_obj:
            return {
                "status": "error",
                "error_message": f"Handover reason {i} is missing 'reason' field."
            }

        if "description" not in reason_obj:
            return {
                "status": "error",
                "error_message": f"Handover reason {i} is missing 'description' field."
            }

        # Validate fields are not empty
        reason_name = reason_obj["reason"].strip() if isinstance(reason_obj["reason"], str) else ""
        description = reason_obj["description"].strip() if isinstance(reason_obj["description"], str) else ""

        if not reason_name:
            return {
                "status": "error",
                "error_message": f"Handover reason {i} has empty reason name."
            }

        if not description:
            return {
                "status": "error",
                "error_message": f"Handover reason {i} has empty description."
            }

        validated_reasons.append({
            "reason": reason_name,
            "description": description
        })

    # Warn if too many handover reasons
    if len(validated_reasons) > 20:
        return {
            "status": "warning",
            "handover_reasons": validated_reasons,
            "reason_count": len(validated_reasons),
            "message": f"  {len(validated_reasons)} handover reasons configured. Consider using 3-5 key scenarios for clarity."
        }

    # Store in session state
    tool_context.state["handover_reasons"] = validated_reasons

    # Update conversation state
    conversation_state = tool_context.state.get("conversation_state", {})
    conversation_state["handover_reasons"] = validated_reasons
    tool_context.state["conversation_state"] = conversation_state

    return {
        "status": "success",
        "handover_reasons": validated_reasons,
        "reason_count": len(validated_reasons),
        "message": f"{len(validated_reasons)} handover reason{'s' if len(validated_reasons) != 1 else ''} configured for human escalation"
    }

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
            "message": " Long instructions (>2000 chars) may affect agent response time."
        }

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



def conversation_complete(reason: str, tool_context: ToolContext) -> Dict[str, Any]:
    """
    Signals that the conversation is complete and the user wants to end the session.

    Use this tool when the user indicates they are done with the conversation by saying
    phrases like: "done", "that's it", "thank you", "we're finished", "all set",
    "I'm done", "goodbye", etc.

    This tool will mark the conversation as complete, trigger the final JSON export,
    and prepare to terminate the session.

    Args:
        reason: The reason or phrase that triggered completion (e.g., "User said thank you", "User said done")

    Returns:
        A dictionary indicating the outcome.
        Always returns status 'success' with completion message.
        Example: {'status': 'success', 'completed': True, 'message': 'Conversation completed. Thank you!', 'final_config': {...}}
    """
    # Mark conversation as complete
    tool_context.state["conversation_complete"] = True
    tool_context.state["completion_reason"] = reason

    # Get final conversation state
    conversation_state = tool_context.state.get("conversation_state", {})

    # Add metadata
    import datetime
    conversation_state["completed_at"] = datetime.datetime.now().isoformat()
    conversation_state["completion_reason"] = reason

    # Store final state
    tool_context.state["conversation_state"] = conversation_state

    # Signal that the agent should prepare to terminate
    # We don't use tool_context.actions.escalate here because we want a graceful completion

    return {
        "status": "success",
        "completed": True,
        "message": "Conversation completed. Thank you for configuring your agent!",
        "final_config": conversation_state
    }


# Create FunctionTool instances for each tool
get_agent_name_tool = FunctionTool(func=get_agent_name)
get_agent_gender_tool = FunctionTool(func=get_agent_gender)
get_personality_tool = FunctionTool(func=get_personality)
get_languages_tool = FunctionTool(func=get_languages)
get_dialect_tool = FunctionTool(func=get_dialect)
get_interaction_steps_tool = FunctionTool(func=get_interaction_steps)
get_conversation_examples_tool = FunctionTool(func=get_conversation_examples)
get_handover_reasons_tool = FunctionTool(func=get_handover_reasons)
get_additional_instructions_tool = FunctionTool(func=get_additional_instructions)
conversation_complete_tool = FunctionTool(func=conversation_complete)

# Export all tools as a list for easy import
all_tools = [
    get_agent_name_tool,
    get_agent_gender_tool,
    get_personality_tool,
    get_languages_tool,
    get_dialect_tool,
    get_interaction_steps_tool,
    get_conversation_examples_tool,
    get_handover_reasons_tool,
    get_additional_instructions_tool,
    conversation_complete_tool
]
