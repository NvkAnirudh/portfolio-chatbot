"""
FastAPI Application Entry Point
"""
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from slowapi.errors import RateLimitExceeded
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import sys

from app.config import settings
from app.db.session import init_db, close_db, get_db
from app.utils.logger import setup_logger
from app.routes import chat
from app.middleware.rate_limiter import limiter, RateLimitMiddleware
from app.middleware.security import SecurityHeadersMiddleware, InputValidationMiddleware
from app.middleware.cost_control import CostControlMiddleware

logger = setup_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events
    """
    # Startup
    logger.info("🚀 Starting Portfolio Chatbot API...")
    logger.info(f"📍 Environment: {settings.environment}")
    logger.info(f"🔧 Debug Mode: {settings.debug}")

    # Note: Database initialization is handled by Alembic migrations
    # Uncomment below line if you want to auto-create tables in development
    # await init_db()

    yield

    # Shutdown
    logger.info("👋 Shutting down Portfolio Chatbot API...")
    await close_db()


# Initialize FastAPI app
app = FastAPI(
    title="Portfolio Chatbot API",
    description="AI-powered chatbot for Anirudh Nuti's portfolio website",
    version="1.0.0",
    debug=settings.debug,
    lifespan=lifespan,
)

# Register rate limiter state
app.state.limiter = limiter


# Exception handler for rate limiting
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Handle rate limit exceeded errors"""
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Rate limit exceeded. Please try again later.",
            "retry_after": "60 seconds"
        },
        headers={"Retry-After": "60"}
    )


# Add middleware (order matters - last added is executed first)
# 1. Security headers (outermost - applies to all responses)
app.add_middleware(SecurityHeadersMiddleware)

# 2. Rate limiting
app.add_middleware(RateLimitMiddleware)

# 3. Input validation (disabled temporarily - implemented at endpoint level)
# app.add_middleware(InputValidationMiddleware)

# 4. Cost control
app.add_middleware(CostControlMiddleware)

# 5. CORS (should be one of the last)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Portfolio Chatbot API",
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """Basic health check endpoint for Railway monitoring"""
    return {
        "status": "healthy",
        "environment": settings.environment,
    }


@app.get("/health/detailed")
async def detailed_health_check(db: AsyncSession = Depends(get_db)):
    """
    Comprehensive health check endpoint

    Checks:
    - API status
    - Database connectivity
    - Redis connectivity
    - Configuration status

    Returns detailed health metrics for monitoring
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.environment,
        "version": "1.0.0",
        "checks": {}
    }

    # Check database connection
    try:
        from app.db.repository import CostTrackingRepository
        await CostTrackingRepository.get_today_cost(db)
        health_status["checks"]["database"] = {
            "status": "healthy",
            "message": "PostgreSQL connected"
        }
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "message": f"Database error: {str(e)}"
        }

    # Check Redis connection
    try:
        from app.services.conversation_manager import conversation_manager
        # Try to ping Redis
        conversation_manager.redis_client.ping()
        health_status["checks"]["redis"] = {
            "status": "healthy",
            "message": "Redis connected"
        }
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["redis"] = {
            "status": "unhealthy",
            "message": f"Redis error: {str(e)}"
        }

    # Check LLM service configuration
    try:
        anthropic_key_set = bool(settings.anthropic_api_key and settings.anthropic_api_key != "your_anthropic_api_key_here")
        if anthropic_key_set:
            health_status["checks"]["llm"] = {
                "status": "healthy",
                "message": "Anthropic API key configured",
                "model": settings.llm_model
            }
        else:
            health_status["status"] = "degraded"
            health_status["checks"]["llm"] = {
                "status": "warning",
                "message": "Anthropic API key not configured"
            }
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["checks"]["llm"] = {
            "status": "warning",
            "message": f"LLM config error: {str(e)}"
        }

    # System information
    health_status["system"] = {
        "python_version": sys.version.split()[0],
        "debug_mode": settings.debug
    }

    return health_status


@app.get("/metrics")
async def metrics(db: AsyncSession = Depends(get_db)):
    """
    Application metrics endpoint

    Returns:
    - Session statistics
    - Cost tracking
    - Request counts
    """
    try:
        from app.services.conversation_manager import conversation_manager
        from app.db.repository import CostTrackingRepository

        # Get session stats
        session_stats = conversation_manager.get_session_stats()

        # Get today's cost and request stats
        today_cost = await CostTrackingRepository.get_today_cost(db)
        today_requests = await CostTrackingRepository.get_today_requests(db)

        # Get cost tracking details
        cost_tracking = await CostTrackingRepository.get_today_tracking(db)

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "sessions": {
                "active_sessions": session_stats.get("active_sessions", 0),
                "total_messages": session_stats.get("total_messages", 0)
            },
            "costs": {
                "today_cost_usd": today_cost,
                "today_requests": today_requests,
                "daily_limit_usd": float(settings.daily_cost_limit_usd),
                "daily_request_limit": int(settings.daily_request_limit),
                "utilization_percent": (today_cost / float(settings.daily_cost_limit_usd) * 100) if float(settings.daily_cost_limit_usd) > 0 else 0
            },
            "tracking": {
                "total_tokens": cost_tracking.get("total_tokens", 0) if cost_tracking else 0,
                "cache_read_tokens": cost_tracking.get("cache_read_tokens", 0) if cost_tracking else 0,
                "requests": cost_tracking.get("requests", 0) if cost_tracking else 0
            },
            "configuration": {
                "environment": settings.environment,
                "llm_model": settings.llm_model,
                "max_tokens": settings.max_tokens,
                "rate_limit_per_minute": settings.rate_limit_per_minute
            }
        }
    except Exception as e:
        logger.error(f"Error retrieving metrics: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to retrieve metrics", "detail": str(e)}
        )
