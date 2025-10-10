"""
Cost Control Middleware

Implements budget controls to prevent runaway API costs:
- Daily cost limits
- Request count limits
- Cost monitoring and alerts
"""
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
from datetime import datetime

from app.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class CostControlMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce daily cost budgets and request limits.

    This middleware checks if the daily budget has been exceeded before
    processing chat requests that would incur LLM API costs.
    """

    # Daily budget limits (can be configured via environment variables)
    DAILY_COST_LIMIT_USD = float(settings.daily_cost_limit_usd)  # Default: $5.00
    DAILY_REQUEST_LIMIT = int(settings.daily_request_limit)  # Default: 1000

    async def dispatch(self, request: Request, call_next: Callable):
        # Only check cost controls for chat endpoints
        if request.url.path == "/api/chat" and request.method == "POST":
            try:
                # Get database session from request state
                # Note: This requires the request to have gone through the database middleware
                from app.db.session import async_session_maker
                from app.db.repository import CostTrackingRepository

                async with async_session_maker() as db:
                    # Get today's costs
                    today_cost = await CostTrackingRepository.get_today_cost(db)
                    today_requests = await CostTrackingRepository.get_today_requests(db)

                    # Check if daily cost limit exceeded
                    if today_cost >= self.DAILY_COST_LIMIT_USD:
                        logger.error(
                            f"Daily cost limit exceeded: ${today_cost:.2f} >= "
                            f"${self.DAILY_COST_LIMIT_USD:.2f}"
                        )
                        raise HTTPException(
                            status_code=429,
                            detail=f"Daily cost budget of ${self.DAILY_COST_LIMIT_USD:.2f} "
                            f"has been reached. Please try again tomorrow."
                        )

                    # Check if daily request limit exceeded
                    if today_requests >= self.DAILY_REQUEST_LIMIT:
                        logger.error(
                            f"Daily request limit exceeded: {today_requests} >= "
                            f"{self.DAILY_REQUEST_LIMIT}"
                        )
                        raise HTTPException(
                            status_code=429,
                            detail=f"Daily request limit of {self.DAILY_REQUEST_LIMIT} "
                            f"has been reached. Please try again tomorrow."
                        )

                    # Log warning if approaching limits (80% threshold)
                    cost_threshold = self.DAILY_COST_LIMIT_USD * 0.8
                    request_threshold = self.DAILY_REQUEST_LIMIT * 0.8

                    if today_cost >= cost_threshold:
                        logger.warning(
                            f"Approaching daily cost limit: ${today_cost:.4f} "
                            f"(${self.DAILY_COST_LIMIT_USD:.2f} limit)"
                        )

                    if today_requests >= request_threshold:
                        logger.warning(
                            f"Approaching daily request limit: {today_requests} "
                            f"({self.DAILY_REQUEST_LIMIT} limit)"
                        )

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error checking cost controls: {e}")
                # Continue processing if cost check fails (fail open)
                # In production, you might want to fail closed for safety

        response = await call_next(request)
        return response


async def check_cost_budget(db) -> dict:
    """
    Check current cost budget status.

    Args:
        db: Database session

    Returns:
        Dictionary with budget status information
    """
    from app.db.repository import CostTrackingRepository

    today_cost = await CostTrackingRepository.get_today_cost(db)
    today_requests = await CostTrackingRepository.get_today_requests(db)

    daily_cost_limit = float(settings.daily_cost_limit_usd)
    daily_request_limit = int(settings.daily_request_limit)

    return {
        "today_cost_usd": today_cost,
        "today_requests": today_requests,
        "daily_cost_limit_usd": daily_cost_limit,
        "daily_request_limit": daily_request_limit,
        "cost_remaining_usd": max(0, daily_cost_limit - today_cost),
        "requests_remaining": max(0, daily_request_limit - today_requests),
        "cost_utilization_percent": (today_cost / daily_cost_limit * 100) if daily_cost_limit > 0 else 0,
        "request_utilization_percent": (today_requests / daily_request_limit * 100) if daily_request_limit > 0 else 0,
        "budget_exceeded": today_cost >= daily_cost_limit or today_requests >= daily_request_limit,
    }
