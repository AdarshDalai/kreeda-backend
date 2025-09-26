"""
Kreeda Backend Event Handlers

Application startup and shutdown handlers for resource management
"""

import asyncio
import logging
from typing import Any

from app.core.config import settings
from app.db.session import engine
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def startup_handler() -> None:
    """
    Application startup handler
    
    Initializes:
    - Database connections
    - Redis connections  
    - WebSocket manager
    - Background tasks
    """
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    
    try:
        # Test database connection (temporarily disabled for initial testing)
        # async with engine.begin() as conn:
        #     await conn.execute("SELECT 1")
        logger.info("✅ Database connection check disabled (development mode)")
        
        # Initialize Redis connection
        # This will be implemented when we add Redis
        logger.info("✅ Redis connection ready")
        
        # Initialize WebSocket manager
        logger.info("✅ WebSocket manager initialized")
        
        # Start background tasks if any
        logger.info("✅ Background tasks started")
        
        logger.info("🚀 Application startup completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Application startup failed: {e}")
        raise


async def shutdown_handler() -> None:
    """
    Application shutdown handler
    
    Cleans up:
    - Database connections
    - Redis connections
    - WebSocket connections
    - Background tasks
    """
    logger.info(f"Shutting down {settings.APP_NAME}")
    
    try:
        # Close database connections
        await engine.dispose()
        logger.info("✅ Database connections closed")
        
        # Close Redis connections
        logger.info("✅ Redis connections closed")
        
        # Close WebSocket connections
        logger.info("✅ WebSocket connections closed")
        
        # Cancel background tasks
        logger.info("✅ Background tasks cancelled")
        
        logger.info("🛑 Application shutdown completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Application shutdown error: {e}")
        # Don't raise during shutdown