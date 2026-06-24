"""
Phoenix Observability Configuration for Voice Agent
Following Phoenix documentation for Google ADK integration
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def setup_phoenix_tracing() -> Optional[object]:
    """
    Initialize Phoenix tracing for observability.

    This function:
    1. Checks if Phoenix tracing is enabled via environment variables
    2. Validates required Phoenix credentials
    3. Registers the Phoenix tracer with OpenTelemetry
    4. Auto-instruments Google ADK for automatic trace collection

    Returns:
        tracer_provider: The OpenTelemetry tracer provider if successful, None otherwise

    Environment Variables Required:
        ENABLE_PHOENIX_TRACING: Set to "true" to enable
        PHOENIX_API_KEY: Your Phoenix API key
        PHOENIX_COLLECTOR_ENDPOINT: Your Phoenix collector endpoint
        PHOENIX_PROJECT_NAME: (Optional) Project name for organizing traces
    """

    enable_tracing = os.getenv("ENABLE_PHOENIX_TRACING", "false").lower() == "true"

    if not enable_tracing:
        logger.info("Phoenix tracing is disabled. Set ENABLE_PHOENIX_TRACING=true to enable.")
        return None


    api_key = os.getenv("PHOENIX_API_KEY")
    collector_endpoint = os.getenv("PHOENIX_COLLECTOR_ENDPOINT")

    if not api_key or not collector_endpoint:
        logger.warning(
            "Phoenix tracing enabled but credentials missing. "
            "Please set PHOENIX_API_KEY and PHOENIX_COLLECTOR_ENDPOINT in .env file. "
            "Tracing will be disabled."
        )
        return None


    if not api_key.strip() or not collector_endpoint.strip():
        logger.warning(
            "Phoenix credentials are empty. Please add valid values to .env file. "
            "Tracing will be disabled."
        )
        return None

    try:
        # Import Phoenix components
        from phoenix.otel import register

        # Get project name (default to 'voice-agent-tools')
        project_name = os.getenv("PHOENIX_PROJECT_NAME", "voice-agent-tools")

        # Set environment variables for Phoenix
        os.environ["PHOENIX_API_KEY"] = api_key
        os.environ["PHOENIX_COLLECTOR_ENDPOINT"] = collector_endpoint


        logger.info(f"Initializing Phoenix tracing for project: {project_name}")
        logger.info(f"Phoenix endpoint: {collector_endpoint}")


        tracer_provider = register(
            project_name=project_name,
            auto_instrument=True,  # Automatically instrument Google ADK
            batch=True  # Use BatchSpanProcessor instead of SimpleSpanProcessor
        )

        logger.info(" Phoenix tracing initialized successfully!")
        logger.info(" Traces will be available at: https://app.phoenix.arize.com")
        logger.info(" All agent interactions, tool calls, and model requests will be traced")

        return tracer_provider

    except ImportError as e:
        logger.error(
            f"Failed to import Phoenix libraries: {e}. "
            "Please install with: pip install openinference-instrumentation-google-adk arize-phoenix-otel"
        )
        return None

    except Exception as e:
        logger.error(f"Failed to initialize Phoenix tracing: {e}", exc_info=True)
        logger.warning("Continuing without Phoenix tracing...")
        return None


def get_phoenix_info() -> dict:
    """
    Get information about Phoenix tracing status.

    Returns:
        dict: Information about Phoenix configuration and status
    """
    enabled = os.getenv("ENABLE_PHOENIX_TRACING", "false").lower() == "true"
    api_key = os.getenv("PHOENIX_API_KEY", "")
    endpoint = os.getenv("PHOENIX_COLLECTOR_ENDPOINT", "")
    project = os.getenv("PHOENIX_PROJECT_NAME", "voice-agent-tools")

    has_credentials = bool(api_key and api_key.strip() and endpoint and endpoint.strip())

    return {
        "enabled": enabled,
        "configured": has_credentials,
        "project_name": project if has_credentials else None,
        "endpoint": endpoint if has_credentials else None,
        "status": (
            "active" if (enabled and has_credentials) else
            "disabled" if not enabled else
            "missing_credentials"
        )
    }



if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("=" * 60)
    print("Phoenix Configuration Test")
    print("=" * 60)

    # Get Phoenix info
    info = get_phoenix_info()
    print("\nPhoenix Status:")
    print(f"  Enabled: {info['enabled']}")
    print(f"  Configured: {info['configured']}")
    print(f"  Status: {info['status']}")
    if info['project_name']:
        print(f"  Project: {info['project_name']}")
    if info['endpoint']:
        print(f"  Endpoint: {info['endpoint']}")

    # Try to initialize
    print("\nInitializing Phoenix...")
    tracer = setup_phoenix_tracing()

    if tracer:
        print("\n Phoenix is ready to trace your agent!")
    else:
        print("\n  Phoenix tracing is not active")
        if not info['enabled']:
            print("   → Set ENABLE_PHOENIX_TRACING=true in .env to enable")
        elif not info['configured']:
            print("   → Add PHOENIX_API_KEY and PHOENIX_COLLECTOR_ENDPOINT to .env")

    print("\n" + "=" * 60)
