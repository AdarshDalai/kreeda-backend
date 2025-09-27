"""
Debug API Endpoints

Simple debugging endpoints
"""

from fastapi import APIRouter

router = APIRouter(prefix="/debug", tags=["debug"])


@router.get("/ping")
async def ping():
    """Simple ping endpoint"""
    return {"message": "pong"}


@router.get("/test-db-import")
async def test_db_import():
    """Test database import"""
    try:
        from app.db.session import get_db_session
        return {"status": "success", "message": "Database session import successful"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/test-cricket-models")
async def test_cricket_models():
    """Test cricket models import"""
    try:
        from app.models.cricket import Team, Player, Match
        return {"status": "success", "message": "Cricket models import successful"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/test-cricket-schemas")
async def test_cricket_schemas():
    """Test cricket schemas import"""
    try:
        from app.schemas.cricket import Team as TeamSchema, Player as PlayerSchema
        return {"status": "success", "message": "Cricket schemas import successful"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/test-db-query")
async def test_db_query():
    """Test database query"""
    try:
        from fastapi import Depends
        from sqlalchemy.ext.asyncio import AsyncSession
        from sqlalchemy import select, func
        from app.db.session import get_db_session
        from app.models.cricket import Team
        
        # This is just a test - we can't use dependency injection here
        # But we can test the query construction
        query = select(func.count(Team.id))
        return {"status": "success", "message": f"Query construction successful: {str(query)}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/test-db-connection")
async def test_db_connection():
    """Test actual database connection"""
    try:
        from sqlalchemy.ext.asyncio import AsyncSession
        from sqlalchemy import text
        from app.db.session import AsyncSessionLocal
        
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1"))
            row = result.fetchone()
            
        return {"status": "success", "message": f"Database connection successful, got: {row}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}