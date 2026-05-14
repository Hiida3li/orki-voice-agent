"""
Business context models.
Pydantic models for business information and API requests.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, HttpUrl


class FAQ(BaseModel):
    """A single FAQ entry."""
    question: str
    answer: str


class BusinessContext(BaseModel):
    """Business context extracted from website."""
    company_name: str = "Unknown"
    description: str = ""
    faqs: List[FAQ] = Field(default_factory=list)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "company_name": self.company_name,
            "description": self.description,
            "faqs": [{"question": faq.question, "answer": faq.answer} for faq in self.faqs],
            "error": self.error
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BusinessContext":
        """Create from dictionary."""
        faqs = [FAQ(**faq) for faq in data.get("faqs", [])]
        return cls(
            company_name=data.get("company_name", "Unknown"),
            description=data.get("description", ""),
            faqs=faqs,
            error=data.get("error")
        )

    @classmethod
    def empty(cls) -> "BusinessContext":
        """Create empty context with default values."""
        return cls(company_name="Unknown")


class BusinessContextRequest(BaseModel):
    """Request model for business context extraction."""
    website_url: str


class BusinessContextResponse(BaseModel):
    """Response model for business context extraction."""
    company_name: str
    description: str
    faqs: List[Dict[str, str]] = Field(default_factory=list)
    error: Optional[str] = None
