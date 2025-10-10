"""
FastAPI Application Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.db.session import init_db, close_db
from app.utils.logger import setup_logger
from app.routes import chat

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

# Configure CORS
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
