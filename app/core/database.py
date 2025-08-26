"""
Database connection and session management
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.config import settings

# Modern SQLAlchemy 2.0 declarative base
class Base(DeclarativeBase):
    pass

# Create SQLAlchemy engine with optimized pooling
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # Log SQL queries in debug mode
    pool_size=int(getattr(settings, 'DB_POOL_SIZE', 10)),
    max_overflow=int(getattr(settings, 'DB_MAX_OVERFLOW', 20)),
    pool_pre_ping=True,  # Validate connections before use
    pool_recycle=300,    # Recycle connections every 5 minutes
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Database dependency for FastAPI routes"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
