from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from src.config.settings import settings

# Create async engine (lazy)
def get_engine():
    return create_async_engine(settings.database_url, echo=True)

# Create session factory
async def get_async_session():
    engine = get_engine()
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()

async def get_db() -> AsyncSession:
    async for session in get_async_session():
        yield session