"""
Base classes for tool validation and state management.
Eliminates duplication across tool implementations.
"""
from typing import Dict, Any, List, Optional
from google.adk.tools import ToolContext


class ValidationResult:
    """Result of a validation operation."""
    
    def __init__(self, valid: bool, error_message: Optional[str] = None):
        self.valid = valid
        self.error_message = error_message
    
    def to_error_response(self) -> Dict[str, Any]:
        """Convert to error response dict."""
        return {
            "status": "error",
            "error_message": self.error_message
        }


class ToolValidator:
    """Base validator for tool inputs."""
    
    @staticmethod
    def validate_non_empty_string(value: str, field_name: str) -> ValidationResult:
        """Validate that a string is not empty."""
        if not value or not value.strip():
            return ValidationResult(
                False, 
                f"{field_name} cannot be empty. Please provide a valid value."
            )
        return ValidationResult(True)
    
    @staticmethod
    def validate_enum(value: str, valid_options: List[str], field_name: str) -> ValidationResult:
        """Validate that a value is in a list of valid options."""
        if value not in valid_options:
            return ValidationResult(
                False,
                f"Invalid {field_name}. Must be one of: {', '.join(valid_options)}. Received: {value}"
            )
        return ValidationResult(True)
    
    @staticmethod
    def validate_list_items(
        items: List[str], 
        valid_options: List[str], 
        field_name: str
    ) -> ValidationResult:
        """Validate that all items in a list are from valid options."""
        if not items or not isinstance(items, list):
            return ValidationResult(
                False,
                f"{field_name} must be a non-empty list."
            )
        
        invalid = [item for item in items if item not in valid_options]
        if invalid:
            return ValidationResult(
                False,
                f"Invalid {field_name}: {invalid}. Valid options are: {valid_options}"
            )
        return ValidationResult(True)
    
    @staticmethod
    def validate_list_length(
        items: List, 
        field_name: str,
        min_length: int = 1,
        max_length: int = 10
    ) -> ValidationResult:
        """Validate list length is within bounds."""
        if not items:
            return ValidationResult(
                False,
                f"{field_name} cannot be empty."
            )
        if len(items) < min_length:
            return ValidationResult(
                False,
                f"{field_name} must have at least {min_length} items."
            )
        if len(items) > max_length:
            return ValidationResult(
                False,
                f"{field_name} cannot have more than {max_length} items. Received: {len(items)}"
            )
        return ValidationResult(True)
    
    @staticmethod
    def validate_dict_list(
        items: List[Dict],
        required_keys: List[str],
        field_name: str
    ) -> ValidationResult:
        """Validate a list of dictionaries has required keys."""
        if not items or not isinstance(items, list):
            return ValidationResult(
                False,
                f"{field_name} must be a non-empty list of objects."
            )
        
        for i, item in enumerate(items):
            if not isinstance(item, dict):
                return ValidationResult(
                    False,
                    f"Item {i+1} in {field_name} must be an object, got: {type(item).__name__}"
                )
            missing = [key for key in required_keys if key not in item]
            if missing:
                return ValidationResult(
                    False,
                    f"Item {i+1} in {field_name} is missing required fields: {missing}"
                )
        return ValidationResult(True)
    
    @staticmethod
    def validate_string_length(
        value: str,
        field_name: str,
        max_length: int
    ) -> ValidationResult:
        """Validate string length does not exceed maximum."""
        if len(value) > max_length:
            return ValidationResult(
                False,
                f"{field_name} exceeds maximum length of {max_length} characters. Current: {len(value)}"
            )
        return ValidationResult(True)


class StateUpdater:
    """Handles updating tool context state."""
    
    @staticmethod
    def update(
        tool_context: ToolContext,
        state_key: str,
        value: Any,
        conversation_key: Optional[str] = None
    ) -> None:
        """
        Update both session state and conversation state.
        
        Args:
            tool_context: The tool context to update
            state_key: Key for session state
            value: Value to store
            conversation_key: Optional different key for conversation state (defaults to state_key)
        """
        # Update session state
        tool_context.state[state_key] = value
        
        # Update conversation state
        conv_key = conversation_key or state_key
        conversation_state = tool_context.state.get("conversation_state", {})
        conversation_state[conv_key] = value
        tool_context.state["conversation_state"] = conversation_state
    
    @staticmethod
    def get_conversation_state(tool_context: ToolContext) -> Dict[str, Any]:
        """Get the current conversation state."""
        return tool_context.state.get("conversation_state", {})


def create_success_response(
    field_name: str,
    value: Any,
    message: str,
    **extra_fields
) -> Dict[str, Any]:
    """Create a standardized success response."""
    response = {
        "status": "success",
        field_name: value,
        "message": message
    }
    response.update(extra_fields)
    return response


def create_error_response(error_message: str) -> Dict[str, Any]:
    """Create a standardized error response."""
    return {
        "status": "error",
        "error_message": error_message
    }
