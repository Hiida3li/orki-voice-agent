"""
Conversation state model and persistence.
Handles tracking and saving of agent configuration state.
"""
import os
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ConversationExample(BaseModel):
    """A single conversation example for training."""
    customer_message: str
    agent_response: str


class HandoverReason(BaseModel):
    """A reason for handing over to human agent."""
    reason: str
    description: str


class ConversationState(BaseModel):
    """Complete state of agent configuration conversation."""
    agent_name: Optional[str] = None
    agent_gender: Optional[str] = None
    personality: Optional[str] = None
    languages: List[str] = Field(default_factory=list)
    dialect: Optional[str] = None
    interaction_steps: List[str] = Field(default_factory=list)
    conversation_examples: List[ConversationExample] = Field(default_factory=list)
    handover_reasons: List[HandoverReason] = Field(default_factory=list)
    additional_instructions: Optional[str] = None
    completed: bool = False
    completion_reason: Optional[str] = None
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary for JSON serialization."""
        data = self.model_dump()
        # Convert datetime to string
        if data.get('completed_at'):
            data['completed_at'] = data['completed_at'].isoformat()
        # Convert nested models to dicts
        data['conversation_examples'] = [
            {'customer_message': ex.customer_message, 'agent_response': ex.agent_response}
            for ex in self.conversation_examples
        ]
        data['handover_reasons'] = [
            {'reason': hr.reason, 'description': hr.description}
            for hr in self.handover_reasons
        ]
        return data
    
    def update_from_tool(self, tool_name: str, response: Dict[str, Any]) -> None:
        """Update state from tool response."""
        field_mapping = {
            'get_agent_name': 'agent_name',
            'get_agent_gender': 'agent_gender',
            'get_personality': 'personality',
            'get_languages': 'languages',
            'get_dialect': 'dialect',
            'get_interaction_steps': 'interaction_steps',
            'get_conversation_examples': 'conversation_examples',
            'get_handover_reasons': 'handover_reasons',
            'get_additional_instructions': 'additional_instructions',
        }
        
        if tool_name in field_mapping:
            field = field_mapping[tool_name]
            value = response.get(field)
            if value is not None:
                # Handle special cases for nested models
                if field == 'conversation_examples' and isinstance(value, list):
                    self.conversation_examples = [
                        ConversationExample(**ex) if isinstance(ex, dict) else ex
                        for ex in value
                    ]
                elif field == 'handover_reasons' and isinstance(value, list):
                    self.handover_reasons = [
                        HandoverReason(**hr) if isinstance(hr, dict) else hr
                        for hr in value
                    ]
                else:
                    setattr(self, field, value)
        
        elif tool_name == 'conversation_complete':
            self.completed = True
            self.completion_reason = response.get('reason', response.get('completion_reason'))
            self.completed_at = datetime.now()


class ConversationPersistence:
    """Handles saving and loading conversation state."""
    
    def __init__(self, output_dir: str = "conversation_outputs"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    async def save(
        self,
        user_id: str,
        session_id: str,
        state: ConversationState,
        tool_results: List[Dict[str, Any]]
    ) -> str:
        """Save conversation state and tool results to JSON file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.output_dir}/conversation_{user_id}_{timestamp}.json"
        
        output = {
            "session_id": session_id,
            "user_id": user_id,
            "timestamp": timestamp,
            "conversation_state": state.to_dict(),
            "tool_results_log": tool_results,
            "metadata": {
                "completed": state.completed,
                "completion_reason": state.completion_reason,
                "total_tool_calls": len(tool_results)
            }
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved conversation to: {filename}")
        return filename
    
    async def load(self, filename: str) -> Dict[str, Any]:
        """Load conversation from JSON file."""
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
