"""
Kreeda Backend Health Check Endpoints

System health and status monitoring endpoints
"""

from datetime import datetime
from fastapi import APIRouter, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.config import settings
from app.db.session import get_db_session
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Basic health check endpoint
    
    Returns:
        Basic health status information
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT
    }


@router.get("/detailed", status_code=status.HTTP_200_OK)
async def detailed_health_check(db: AsyncSession = Depends(get_db_session)):
    """
    Detailed health check with system dependencies
    
    Args:
        db: Database session dependency
        
    Returns:
        Detailed health status including database connectivity
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "checks": {}
    }
    
    # Database health check
    try:
        result = await db.execute(text("SELECT 1"))
        result.fetchone()
        health_status["checks"]["database"] = {
            "status": "healthy",
            "message": "Database connection successful"
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}"
        }
    
    # Redis health check (placeholder for now)
    health_status["checks"]["redis"] = {
        "status": "healthy",
        "message": "Redis connection not implemented yet"
    }
    
    # WebSocket manager health check (placeholder for now)
    health_status["checks"]["websocket"] = {
        "status": "healthy", 
        "message": "WebSocket manager not implemented yet"
    }
    
    return health_status


@router.get("/ready", status_code=status.HTTP_200_OK)
async def readiness_check(db: AsyncSession = Depends(get_db_session)):
    """
    Kubernetes readiness probe endpoint
    
    Args:
        db: Database session dependency
        
    Returns:
        Ready status for container orchestration
    """
    try:
        # Quick database connectivity check
        await db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return {"status": "not ready", "error": str(e)}


@router.get("/live", status_code=status.HTTP_200_OK)
async def liveness_check():
    """
    Kubernetes liveness probe endpoint
    
    Returns:
        Live status for container orchestration
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat()
    }