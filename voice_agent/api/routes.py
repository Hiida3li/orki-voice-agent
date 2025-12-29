"""
REST API endpoints.
Defines all HTTP endpoints for the voice agent.
"""
import logging
from typing import Optional
from pathlib import Path

from fastapi import APIRouter, WebSocket
from fastapi.responses import HTMLResponse, RedirectResponse

from ..config.settings import settings
from ..config.observability import get_phoenix_info
from ..core.agent import get_default_agent
from ..core.session import session_manager
from ..business import extract_business_context
from ..websocket import connection_handler, decode_business_context
from ..tools import tool_registry
from .models import (
    HealthResponse,
    BusinessContextRequest,
    BusinessContextResponse
)

logger = logging.getLogger(__name__)

# Create routers
main_router = APIRouter()
api_router = APIRouter(prefix="/api")


# --- HTML Routes ---

@main_router.get("/")
async def root():
    """Redirect to business context page (starting point of the flow)."""
    return RedirectResponse(url="/business")


@main_router.get("/enhanced")
async def enhanced_ui_page():
    """Serve the enhanced UI with tool calls and configuration display."""
    # Try package static folder first, then fallback to root
    static_path = Path(__file__).parent.parent / "static" / "enhanced_ui.html"
    if not static_path.exists():
        static_path = Path("enhanced_ui.html")

    with open(static_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@main_router.get("/business")
async def business_context_page():
    """Serve the business context input page."""
    # Try package static folder first, then fallback to root
    static_path = Path(__file__).parent.parent / "static" / "business_context.html"
    if not static_path.exists():
        static_path = Path("business_context.html")

    with open(static_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


# --- API Routes ---

@api_router.post("/extract-business-context", response_model=BusinessContextResponse)
async def api_extract_business_context(request: BusinessContextRequest):
    """
    Extract business context from a website URL using LLM.

    Uses Gemini to intelligently extract:
    - company_name: str
    - description: str
    - faqs: List[Dict] with 'question' and 'answer' keys (LLM-generated)
    """
    logger.info(f"Extracting business context from: {request.website_url}")

    context = await extract_business_context(request.website_url)

    return context


@main_router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint with Phoenix tracing status."""
    phoenix_info = get_phoenix_info()
    default_agent = get_default_agent()

    return {
        "status": "healthy",
        "active_sessions": session_manager.active_count,
        "agent": default_agent.name,
        "model": settings.model_name,
        "tools_enabled": len(tool_registry.get_all()),
        "tools": [str(t) for t in tool_registry.get_all()],
        "observability": {
            "phoenix_tracing": phoenix_info['status'],
            "phoenix_enabled": phoenix_info['enabled'],
            "phoenix_project": phoenix_info.get('project_name')
        }
    }


# --- WebSocket Route ---

@main_router.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str,
    is_audio: str = "true",
    business_context: Optional[str] = None
):
    """WebSocket endpoint for voice agent communication."""
    # Convert is_audio string to boolean
    audio_enabled = is_audio.lower() == "true"

    # Decode business context if provided
    business_context_data = decode_business_context(business_context)
    if business_context_data:
        logger.info(
            f"Business context received for {user_id}: "
            f"{business_context_data.get('company_name', 'Unknown')}"
        )

    # Handle the connection
    await connection_handler.handle(
        websocket=websocket,
        user_id=user_id,
        is_audio=audio_enabled,
        business_context=business_context_data
    )
