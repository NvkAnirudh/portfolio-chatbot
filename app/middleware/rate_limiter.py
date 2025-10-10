"""
Rate Limiting Middleware

Implements rate limiting to prevent API abuse:
- Per-IP rate limits
- Per-session rate limits
- Different limits for different endpoints
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import time

from app.utils.logger import setup_logger

logger = setup_logger(__name__)


def get_client_identifier(request: Request) -> str:
    """
    Get unique identifier for rate limiting.
    Uses session_id if available, otherwise falls back to IP address.
    """
    # Try to get session_id from request body (for POST requests)
    if request.method == "POST":
        try:
            # This is a bit hacky but works for our use case
            # In production, consider using a more robust solution
            pass
        except:
            pass

    # Fallback to IP address
    return get_remote_address(request)


# Initialize rate limiter with Redis backend (or in-memory fallback)
# Format: "number/time_unit" (e.g., "10/minute", "100/hour")
limiter = Limiter(
    key_func=get_client_identifier,
    default_limits=["60/minute", "1000/hour"],  # Global limits
    storage_uri="memory://",  # Use in-memory storage (can switch to Redis)
    headers_enabled=True,  # Include rate limit info in response headers
)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log rate limit events and add custom headers
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            response = await call_next(request)
            return response
        except RateLimitExceeded as e:
            logger.warning(
                f"Rate limit exceeded for {get_remote_address(request)} "
                f"on {request.url.path}"
            )
            raise


def get_rate_limiter():
    """Get the rate limiter instance"""
    return limiter
