"""
Voice Agent Application Entry Point.
FastAPI app factory with dependency injection and startup configuration.
"""
import os
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config.settings import settings
from .config.observability import setup_phoenix_tracing, get_phoenix_info
from .api import main_router, api_router
from .tools import tool_registry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance
    """
    # Initialize Phoenix tracing early
    phoenix_tracer = setup_phoenix_tracing()

    # Verify API key
    if not settings.google_api_key:
        raise ValueError("GOOGLE_API_KEY is required")

    # Create FastAPI app
    app = FastAPI(
        title="ADK Voice Agent",
        description="Voice-based AI agent configuration system",
        version="1.0.0"
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_credentials,
        allow_methods=settings.cors_methods,
        allow_headers=settings.cors_headers,
    )

    # Include routers
    app.include_router(main_router)
    app.include_router(api_router)

    # Log startup info
    logger.info("Initializing agent with tools...")
    tools = tool_registry.get_all()
    logger.info(f"Number of tools: {len(tools)}")
    for tool in tools:
        logger.info(f"  Tool: {tool}")

    return app


def print_startup_banner():
    """Print startup information banner."""
    print("=" * 60)
    print("ADK Voice Agent with Tools - Starting Up")
    print("=" * 60)

    # Show Phoenix status
    phoenix_info = get_phoenix_info()
    print(f"\nObservability Status:")
    if phoenix_info['status'] == 'active':
        print(f"   Phoenix Tracing: ACTIVE")
        print(f"   Project: {phoenix_info['project_name']}")
        print(f"   Endpoint: {phoenix_info['endpoint']}")
        print(f"   Dashboard: https://app.phoenix.arize.com")
    elif phoenix_info['status'] == 'disabled':
        print(f"   Phoenix Tracing: DISABLED")
        print(f"   To enable: Set ENABLE_PHOENIX_TRACING=true in .env")
    else:
        print(f"   Phoenix Tracing: MISSING CREDENTIALS")
        print(f"   Add PHOENIX_API_KEY and PHOENIX_COLLECTOR_ENDPOINT to .env")

    # Check SSL
    use_ssl = os.path.exists("cert.pem") and os.path.exists("key.pem")

    print("\nServer Configuration:")
    protocol = "HTTPS" if use_ssl else "HTTP"
    address = f"{protocol.lower()}://localhost:{settings.port}"
    print(f"   Protocol: {protocol}")
    print(f"   Address: {address}")

    print("\nEndpoints:")
    print("   Start Here: / (redirects to /business)")
    print("   Business Context: /business")
    print("   Voice Configuration: /enhanced")
    print("   WebSocket: /ws/{user_id}")
    print("   Health Check: /health")

    print("\n" + "=" * 60)
    print("Starting server...")
    print("=" * 60 + "\n")


def run_server():
    """Run the server with uvicorn."""
    import uvicorn

    print_startup_banner()

    # Check SSL
    use_ssl = os.path.exists("cert.pem") and os.path.exists("key.pem")

    if use_ssl:
        uvicorn.run(
            "voice_agent.main:app",
            host=settings.host,
            port=settings.port,
            ssl_keyfile="key.pem",
            ssl_certfile="cert.pem"
        )
    else:
        uvicorn.run(
            "voice_agent.main:app",
            host=settings.host,
            port=settings.port
        )


# Create app instance
app = create_app()


if __name__ == "__main__":
    run_server()
