"""
Voice Agent Package.

A modular voice-based AI agent configuration system built with
Google ADK, FastAPI, and WebSockets.

Usage:
    # Run the server
    python -m voice_agent

    # Or import components
    from voice_agent import app
    from voice_agent.core import session_manager
    from voice_agent.tools import tool_registry
"""
from .main import app, create_app, run_server

__version__ = "1.0.0"
__all__ = ['app', 'create_app', 'run_server']
