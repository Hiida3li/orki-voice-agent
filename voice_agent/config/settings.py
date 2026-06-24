"""
Application settings and configuration.
Centralizes all environment variables and app configuration.
"""
import os
import logging
from typing import Optional, List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # Ignore extra fields from .env
        protected_namespaces=('settings_',)  # Avoid conflict with model_name
    )

    # API Keys
    google_api_key: str = Field(default="")

    # Server
    host: str = "0.0.0.0"
    port: int = 8006
    debug: bool = False

    # SSL
    ssl_certfile: Optional[str] = "cert.pem"
    ssl_keyfile: Optional[str] = "key.pem"

    # Agent
    model_name: str = "gemini-2.5-flash-native-audio-latest"
    agent_voice: str = "Charon"

    # CORS
    cors_origins: List[str] = Field(default=["*"])
    cors_credentials: bool = True
    cors_methods: List[str] = Field(default=["*"])
    cors_headers: List[str] = Field(default=["*"])

    # Audio
    input_sample_rate: int = 16000
    output_sample_rate: int = 24000

    # Phoenix (handled by observability module)
    phoenix_api_key: Optional[str] = None
    phoenix_collector_endpoint: Optional[str] = None
    phoenix_project_name: Optional[str] = "voice-agent-tools"
    enable_phoenix_tracing: bool = False

    def validate_api_key(self) -> None:
        """Validate that required API key is set."""
        if not self.google_api_key:
            raise ValueError("GOOGLE_API_KEY is required. Set it in .env file.")

    @property
    def ssl_enabled(self) -> bool:
        """Check if SSL certificates exist."""
        return (
            self.ssl_certfile and
            self.ssl_keyfile and
            os.path.exists(self.ssl_certfile) and
            os.path.exists(self.ssl_keyfile)
        )


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Configure application logging."""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)



settings = Settings()
logger = setup_logging()
