"""
Security Middleware

Adds security headers and implements security best practices:
- Content Security Policy (CSP)
- X-Content-Type-Options
- X-Frame-Options
- Strict-Transport-Security (HSTS)
- Request validation and sanitization
"""
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import re
import html

from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Content Security Policy - restrictive for API
        response.headers["Content-Security-Policy"] = (
            "default-src 'none'; "
            "frame-ancestors 'none'; "
            "base-uri 'none';"
        )

        # HSTS - only enable in production with HTTPS
        # Uncomment when deploying with HTTPS
        # response.headers["Strict-Transport-Security"] = (
        #     "max-age=31536000; includeSubDomains"
        # )

        return response


class InputValidationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to validate and sanitize inputs
    """

    # Patterns to detect potential injection attacks
    SUSPICIOUS_PATTERNS = [
        r"<script[^>]*>.*?</script>",  # XSS
        r"javascript:",  # JavaScript protocol
        r"on\w+\s*=",  # Event handlers
        r"(?i)(union|select|insert|update|delete|drop|create|alter|exec|execute)\s",  # SQL injection attempts
    ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Only validate POST requests with JSON body
        if request.method == "POST" and "application/json" in request.headers.get("content-type", "").lower():
            try:
                # Get request body
                body = await request.body()

                if body:
                    body_str = body.decode("utf-8")

                    # Check for suspicious patterns (basic detection)
                    for pattern in self.SUSPICIOUS_PATTERNS:
                        if re.search(pattern, body_str, re.IGNORECASE):
                            logger.warning(
                                f"Suspicious pattern detected in request from "
                                f"{request.client.host if request.client else 'unknown'}: "
                                f"Pattern: {pattern}"
                            )
                            # In a real-world scenario, you might want to block this
                            # For now, we just log it

                    # Reconstruct request with original body
                    # This is necessary because we consumed the body
                    async def receive():
                        return {"type": "http.request", "body": body}

                    request._receive = receive

            except Exception as e:
                logger.error(f"Error in input validation: {e}")

        response = await call_next(request)
        return response


def sanitize_input(text: str, max_length: int = 1000) -> str:
    """
    Sanitize user input to prevent injection attacks.

    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length

    Returns:
        Sanitized text

    Raises:
        HTTPException: If input is invalid
    """
    if not text or not isinstance(text, str):
        raise HTTPException(status_code=400, detail="Input must be a non-empty string")

    # Trim whitespace
    text = text.strip()

    # Check if empty after stripping
    if not text:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # Check length
    if len(text) > max_length:
        raise HTTPException(
            status_code=400,
            detail=f"Input exceeds maximum length of {max_length} characters"
        )

    # HTML escape to prevent XSS (just in case)
    # Note: This is defensive - the frontend should handle rendering safely
    text = html.escape(text, quote=False)

    return text


def validate_session_id(session_id: str) -> bool:
    """
    Validate session ID format (UUID v4).

    Args:
        session_id: Session ID to validate

    Returns:
        True if valid UUID format
    """
    uuid_pattern = re.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$',
        re.IGNORECASE
    )
    return bool(uuid_pattern.match(session_id))
