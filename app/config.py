"""
Application Configuration using Pydantic Settings
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings from environment variables"""

    # Anthropic API
    anthropic_api_key: str

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # PostgreSQL
    database_url: str

    # Application
    environment: str = "development"
    debug: bool = True
    allowed_origins: str = "http://localhost:5173,http://localhost:3000"

    # Rate Limiting
    rate_limit_per_minute: int = 10
    rate_limit_per_hour: int = 50
    session_message_limit: int = 20
    daily_request_limit: int = 1000

    # Cost Monitoring
    daily_cost_limit_usd: float = 5.0
    cost_alert_threshold_usd: float = 4.0

    # LLM Configuration
    llm_model: str = "claude-3-5-haiku-20241022"
    max_tokens: int = 1000
    temperature: float = 0.7

    # Session Configuration
    session_ttl_hours: int = 24
    conversation_history_length: int = 10

    @property
    def cors_origins(self) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        return [origin.strip() for origin in self.allowed_origins.split(",")]

    @property
    def session_ttl_seconds(self) -> int:
        """Convert session TTL to seconds"""
        return self.session_ttl_hours * 3600

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
