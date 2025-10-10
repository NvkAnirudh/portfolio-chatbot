"""
FastAPI Application Entry Point
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.db.session import init_db, close_db
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
    """Health check endpoint"""
    return {
        "status": "healthy",
        "environment": settings.environment,
    }
