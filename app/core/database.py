from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Create async database engine
engine = create_async_engine(
    settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
    echo=settings.ENVIRONMENT == "development",
    future=True
)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Create base class for models
Base = declarative_base()


async def get_db():
    """Dependency to get database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database tables."""
    try:
        # Try to connect to database
        async with engine.begin() as conn:
            # Import all models to ensure they are registered
            from app.models import user, team, match, tournament, score  # noqa
            
            # Create all tables (if they don't exist)
            # This is safe as we use IF NOT EXISTS in SQL
            await conn.run_sync(Base.metadata.create_all)
            
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.warning(f"⚠️  Database initialization failed: {e}")
        logger.info("📝 The app will continue without database connectivity")
        # Don't raise the exception - let the app start without DB
        pass


async def close_db():
    """Close database connections."""
    await engine.dispose()
    logger.info("Database connections closed")
