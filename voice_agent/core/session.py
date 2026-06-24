"""
Session lifecycle and storage.
Manages WebSocket sessions and agent state.
"""
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

from google.adk.agents import LiveRequestQueue
from google.adk.runners import InMemoryRunner
from google.adk.agents.run_config import RunConfig
from google.genai.types import (
    SpeechConfig,
    VoiceConfig,
    PrebuiltVoiceConfig
)

from ..config.settings import settings
from .agent import agent_factory

logger = logging.getLogger(__name__)


@dataclass
class SessionData:
    """Data for an active session."""
    session_id: str
    user_id: str
    run_config: RunConfig
    live_queue: LiveRequestQueue
    runner: InMemoryRunner
    is_audio: bool = True
    should_cancel_output: bool = False
    user_interrupted: bool = False
    business_context: Optional[Dict[str, Any]] = None

    def reset_interruption_flags(self) -> None:
        """Reset interruption flags for new turn."""
        self.should_cancel_output = False
        self.user_interrupted = False

    def set_interrupted(self, user_initiated: bool = True) -> None:
        """Mark session as interrupted."""
        self.should_cancel_output = True
        self.user_interrupted = user_initiated


class SessionManager:
    """Manages active WebSocket sessions."""

    def __init__(self):
        self._sessions: Dict[str, SessionData] = {}

    def get(self, user_id: str) -> Optional[SessionData]:
        """Get session for user."""
        return self._sessions.get(user_id)

    def exists(self, user_id: str) -> bool:
        """Check if session exists for user."""
        return user_id in self._sessions

    def set_interrupted(self, user_id: str, user_initiated: bool = True) -> bool:
        """
        Mark a session as interrupted.

        Returns:
            True if session exists and was marked, False otherwise
        """
        session = self.get(user_id)
        if session:
            session.set_interrupted(user_initiated)
            return True
        return False

    def reset_interruption(self, user_id: str) -> bool:
        """
        Reset interruption flags for a session.

        Returns:
            True if session exists, False otherwise
        """
        session = self.get(user_id)
        if session:
            session.reset_interruption_flags()
            return True
        return False

    def is_cancelled(self, user_id: str) -> bool:
        """Check if session output should be cancelled."""
        session = self.get(user_id)
        return session.should_cancel_output if session else False

    async def create(
        self,
        user_id: str,
        is_audio: bool = True,
        business_context: Optional[Dict[str, Any]] = None
    ) -> SessionData:
        """
        Create a new session for a user.

        Args:
            user_id: Unique user identifier
            is_audio: Whether to enable audio mode
            business_context: Optional business context for the agent

        Returns:
            SessionData for the new session
        """
        # Create agent and runner
        if business_context:
            agent = agent_factory.create(business_context)
            runner = agent_factory.create_runner(agent)
            logger.info(f"Using custom runner with business context for user {user_id}")
        else:
            agent = agent_factory.create()
            runner = agent_factory.create_runner(agent)
            logger.info(f"Using default runner for user {user_id}")

        # Create session via runner
        session = await runner.session_service.create_session(
            app_name="adk_streaming_app",
            user_id=user_id
        )

        # Configure run based on mode
        run_config = self._create_run_config(is_audio)

        # Create LiveRequestQueue
        live_queue = LiveRequestQueue()

        # Create session data
        session_data = SessionData(
            session_id=session.id,
            user_id=user_id,
            run_config=run_config,
            live_queue=live_queue,
            runner=runner,
            is_audio=is_audio,
            business_context=business_context
        )

        # Store session
        self._sessions[user_id] = session_data

        logger.info(
            f"Started session for user {user_id}, "
            f"audio={is_audio}, session_id={session.id}"
        )

        return session_data

    def _create_run_config(self, is_audio: bool) -> RunConfig:
        """Create run configuration based on mode."""
        if is_audio:
            speech_config = SpeechConfig(
                voice_config=VoiceConfig(
                    prebuilt_voice_config=PrebuiltVoiceConfig(
                        voice_name=settings.agent_voice
                    )
                )
            )
            return RunConfig(
                response_modalities=["AUDIO"],
                speech_config=speech_config
            )
        else:
            return RunConfig(
                response_modalities=["TEXT"]
            )

    def remove(self, user_id: str) -> Optional[SessionData]:
        """
        Remove and cleanup a session.

        Args:
            user_id: User to remove session for

        Returns:
            The removed session data, or None if not found
        """
        session = self._sessions.pop(user_id, None)
        if session:
            session.live_queue.close()
            logger.info(f"Session ended for user {user_id}")
        return session

    @property
    def active_count(self) -> int:
        """Number of active sessions."""
        return len(self._sessions)

    def get_all(self) -> Dict[str, SessionData]:
        """Get all active sessions."""
        return self._sessions.copy()



session_manager = SessionManager()
