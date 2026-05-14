"""
API request/response models.
Pydantic models for REST endpoints.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    active_sessions: int
    agent: str
    model: str
    tools_enabled: int
    tools: List[str]
    observability: Dict[str, Any]


class BusinessContextRequest(BaseModel):
    """Request to extract business context from a URL."""
    website_url: str


class BusinessContextResponse(BaseModel):
    """Response with extracted business context."""
    company_name: str
    description: str = ""
    faqs: List[Dict[str, str]] = Field(default_factory=list)
    error: Optional[str] = None


class SessionInfo(BaseModel):
    """Information about an active session."""
    session_id: str
    user_id: str
    is_audio: bool
    has_business_context: bool


class ErrorResponse(BaseModel):
    """Generic error response."""
    error: str
    detail: Optional[str] = None
