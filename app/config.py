"""
Application Configuration using Pydantic Settings
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List, Optional
import os


class Settings(BaseSettings):
    """Application settings from environment variables"""

    # Anthropic API
    anthropic_api_key: str = Field(
        ...,
        description="Anthropic API key for Claude"
    )

    # Redis - Railway provides REDIS_URL
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )

    # PostgreSQL - Railway provides DATABASE_URL
    database_url: str = Field(
        ...,
        description="PostgreSQL connection URL with asyncpg driver"
    )

    # Application
    environment: str = Field(
        default="development",
        description="Environment: development, staging, or production"
    )
    debug: bool = Field(
        default=True,
        description="Enable debug mode"
    )
    allowed_origins: str = Field(
        default="http://localhost:5173,http://localhost:3000",
        description="Comma-separated list of allowed CORS origins"
    )

    # Rate Limiting
    rate_limit_per_minute: int = Field(
        default=10,
        description="Maximum requests per minute per IP"
    )
    rate_limit_per_hour: int = Field(
        default=50,
        description="Maximum requests per hour per IP"
    )
    session_message_limit: int = Field(
        default=20,
        description="Maximum messages per session"
    )
    daily_request_limit: int = Field(
        default=1000,
        description="Maximum requests per day"
    )

    # Cost Monitoring
    daily_cost_limit_usd: float = Field(
        default=5.0,
        description="Maximum daily cost in USD"
    )
    cost_alert_threshold_usd: float = Field(
        default=4.0,
        description="Cost threshold for alerts in USD"
    )

    # LLM Configuration
    llm_model: str = Field(
        default="claude-3-5-haiku-20241022",
        description="Claude model to use"
    )
    max_tokens: int = Field(
        default=1000,
        description="Maximum tokens in LLM response"
    )
    temperature: float = Field(
        default=0.7,
        description="LLM temperature (0-1)"
    )

    # Session Configuration
    session_ttl_hours: int = Field(
        default=24,
        description="Session TTL in hours"
    )
    conversation_history_length: int = Field(
        default=10,
        description="Number of messages to keep in history"
    )

    @property
    def cors_origins(self) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        return [origin.strip() for origin in self.allowed_origins.split(",")]

    @property
    def session_ttl_seconds(self) -> int:
        """Convert session TTL to seconds"""
        return self.session_ttl_hours * 3600

    @property
    def async_database_url(self) -> str:
        """
        Convert DATABASE_URL to async format if needed.

        Railway provides: postgresql://...
        We need: postgresql+asyncpg://...

        This property automatically converts it.
        """
        if self.database_url.startswith("postgresql://"):
            return self.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return self.database_url

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra environment variables from Railway


# Global settings instance
settings = Settings()
