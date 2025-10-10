"""
Database Session Management
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from app.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

# Create async engine
# Use async_database_url property which automatically converts Railway's DATABASE_URL
# from postgresql:// to postgresql+asyncpg://
engine = create_async_engine(
    settings.async_database_url,
    echo=settings.debug,
    poolclass=NullPool,  # Use NullPool for async to avoid connection pool issues
    future=True,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncSession:
    """
    Dependency function to get database session

    Yields:
        AsyncSession: Database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database tables"""
    from app.models.db_models import Base

    async with engine.begin() as conn:
        logger.info("Creating database tables...")
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")


async def close_db():
    """Close database connections"""
    await engine.dispose()
    logger.info("Database connections closed")
