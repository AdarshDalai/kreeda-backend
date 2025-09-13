import logging

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base

from app.config import settings

logger = logging.getLogger(__name__)

# Create base class for models
Base = declarative_base()
metadata = MetaData()

# Engine and session will be created when needed
engine = None
AsyncSessionLocal = None


def get_engine():
    global engine
    if engine is None:
        engine = create_async_engine(
            settings.database_url,
            echo=settings.debug,
            future=True,
        )
    return engine


def get_session_local():
    global AsyncSessionLocal
    if AsyncSessionLocal is None:
        AsyncSessionLocal = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return AsyncSessionLocal


async def init_db():
    """Initialize database tables"""
    try:
        async with get_engine().begin() as conn:
            # Import all models to register them with Base
            from app.models import cricket, user  # noqa: F401

            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


from typing import AsyncGenerator

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session"""
    async with get_session_local()() as session:
        try:
            yield session
        finally:
            await session.close()
