"""
Kreeda Backend - Main FastAPI Application
Cricket scoring made simple, fast, and reliable
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import json
from typing import Dict, List, Optional
import asyncio
import logging
from datetime import datetime, timezone

from app.core.config import settings
from app.core.logging import logger, get_request_logger, log_request, log_error
from app.core.middleware import SecurityHeadersMiddleware, RequestLoggingMiddleware, DistributedRateLimitMiddleware, RequestIDMiddleware, RedisRateLimitMiddleware
from app.api.cricket import router as cricket_router
from app.api.auth import router as auth_router
from app.api.v1.cricket import router as v1_cricket_router
from app.api.v1.auth import router as v1_auth_router

# Setup logging
request_logger = get_request_logger()


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Digital cricket scoring and team management API",
    docs_url="/docs" if settings.DEBUG else None,  # Disable docs in production
    redoc_url="/redoc" if settings.DEBUG else None
)

# Add middleware in correct order (last added = first executed)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)

# Add compression middleware for better performance
from starlette.middleware.gzip import GZipMiddleware
app.add_middleware(GZipMiddleware, minimum_size=1000)  # Compress responses > 1KB

if not settings.DEBUG:
    # Use Redis-based rate limiting for better performance
    try:
        app.add_middleware(RedisRateLimitMiddleware, calls_per_minute=settings.RATE_LIMIT_PER_MINUTE)
        logger.info("✅ Redis-based rate limiting enabled")
    except Exception as e:
        logger.warning(f"⚠️  Redis rate limiting failed, using DynamoDB fallback: {e}")
        app.add_middleware(DistributedRateLimitMiddleware, calls_per_minute=settings.RATE_LIMIT_PER_MINUTE)

# Security Middleware
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["localhost", "127.0.0.1", "testserver", "*.kreeda.app"]
)

# CORS Middleware - Security hardened
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=settings.DEBUG,  # Only allow credentials in development
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Explicit methods only
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "X-Request-ID"
    ],  # Explicit headers only
    max_age=86400,  # Cache preflight for 24 hours
)

# Include routers
app.include_router(auth_router, prefix="/api/auth", tags=["authentication"])
app.include_router(cricket_router, prefix="/api/cricket", tags=["cricket"])

# Include versioned routers with proper error handling
def include_versioned_routers():
    """Include versioned API routers with proper error handling"""
    try:
        # Include versioned routers (already imported at top)
        app.include_router(v1_auth_router, prefix="/api/v1/auth", tags=["v1-authentication"])
        app.include_router(v1_cricket_router, prefix="/api/v1/cricket", tags=["v1-cricket"])

        logger.info("✅ Versioned API endpoints (v1) loaded successfully")
        return True

    except Exception as e:
        logger.error(f"❌ Error loading versioned routers: {e}")
        logger.info("ℹ️  Running with current API version only")
        return False

# Load versioned routers
versioned_routers_loaded = include_versioned_routers()


# Polling endpoint for live match updates (serverless-compatible)
@app.get("/api/cricket/matches/{match_id}/updates")
async def get_match_updates(match_id: str, since: Optional[str] = None):
    """Get match updates since timestamp (polling alternative to WebSocket)"""
    try:
        from app.services.dynamodb_cricket_scoring import DynamoDBService
        db_service = DynamoDBService()

        # Get current match state
        match = db_service.get_match(match_id)
        if not match:
            raise HTTPException(status_code=404, detail="Match not found")

        # Get live score
        live_score = db_service.get_live_score(match_id)

        # For MVP, return current state
        # In production, you could filter by 'since' timestamp
        return {
            "match_id": match_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "match_status": match.get("status", "unknown"),
            "live_score": live_score.dict() if hasattr(live_score, 'dict') else live_score,
            "message": "Use this endpoint to poll for match updates"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get match updates: {str(e)}"
        )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Application health check with detailed metrics"""
    from datetime import datetime, timezone
    from typing import Dict, Any

    try:
        # Basic health info
        health_data: Dict[str, Any] = {
            "status": "healthy",
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Database connectivity check
        try:
            from app.services.dynamodb_cricket_scoring import DynamoDBService
            db_service = DynamoDBService()
            # Try a simple operation to test connectivity
            test_table = db_service.dynamodb.Table(db_service.table_name)
            test_table.table_status
            health_data["database"] = {
                "status": "healthy",
                "table_name": db_service.table_name,
                "region": settings.AWS_REGION
            }
        except Exception as e:
            health_data["database"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_data["status"] = "degraded"

        # System metrics (with graceful fallback if psutil not available)
        try:
            import psutil
            import time

            health_data["system"] = {
                "cpu_percent": psutil.cpu_percent(interval=0.1),
                "memory": {
                    "total_mb": psutil.virtual_memory().total / 1024 / 1024,
                    "available_mb": psutil.virtual_memory().available / 1024 / 1024,
                    "percent_used": psutil.virtual_memory().percent
                },
                "disk": {
                    "total_mb": psutil.disk_usage('/').total / 1024 / 1024,
                    "free_mb": psutil.disk_usage('/').free / 1024 / 1024,
                    "percent_used": psutil.disk_usage('/').percent
                },
                "uptime_seconds": time.time() - psutil.boot_time()
            }
        except ImportError:
            health_data["system"] = {
                "message": "System monitoring unavailable - psutil not installed",
                "cpu_percent": "unknown",
                "memory": "unknown",
                "disk": "unknown"
            }

        # API endpoints status
        health_data["endpoints"] = {
            "docs": "/docs",
            "health": "/health",
            "auth_config": "/api/auth/config",
            "cricket_api": "/api/cricket/health"
        }

        # Version information
        health_data["api_versions"] = {
            "current": "v1",
            "supported": ["v1"],
            "deprecated": []
        }

        return health_data

    except Exception as e:
        # Fallback health check
        return {
            "status": "unhealthy",
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e),
            "message": "Health check failed"
        }


# Detailed health check for monitoring systems
@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check for monitoring systems"""
    from datetime import datetime, timezone
    from typing import Dict, Any

    health_checks: Dict[str, Any] = {
        "overall_status": "healthy",
        "checks": {}
    }
    
    # Database health
    try:
        from app.services.dynamodb_cricket_scoring import DynamoDBService
        db_service = DynamoDBService()
        table = db_service.dynamodb.Table(db_service.table_name)
        table.table_status
        health_checks["checks"]["database"] = {
            "status": "healthy",
            "response_time_ms": 100,  # Simplified
            "table_name": db_service.table_name
        }
    except Exception as e:
        health_checks["checks"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_checks["overall_status"] = "unhealthy"
    
    # System health (simplified without psutil)
    try:
        import psutil
        memory = psutil.virtual_memory()
        health_checks["checks"]["memory"] = {
            "status": "healthy" if memory.percent < 90 else "warning",
            "used_percent": memory.percent,
            "available_mb": memory.available / 1024 / 1024
        }
        
        cpu_percent = psutil.cpu_percent(interval=0.1)
        health_checks["checks"]["cpu"] = {
            "status": "healthy" if cpu_percent < 80 else "warning",
            "usage_percent": cpu_percent
        }
        
        disk = psutil.disk_usage('/')
        health_checks["checks"]["disk"] = {
            "status": "healthy" if disk.percent < 90 else "warning",
            "used_percent": disk.percent,
            "free_mb": disk.free / 1024 / 1024
        }
    except ImportError:
        # System monitoring not available
        health_checks["checks"]["system_monitoring"] = {
            "status": "warning",
            "message": "psutil not available - system monitoring disabled"
        }
    
    return health_checks


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Kreeda Backend",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health"
    }


# Startup event
@app.on_event("startup")
async def startup_event():
    """Application startup"""
    logger.info(f"🏏 Starting {settings.APP_NAME} v{settings.APP_VERSION}")

    # Run database migrations
    try:
        from app.services.dynamodb_migrations import run_database_migrations
        if run_database_migrations():
            logger.info("✅ Database migrations completed successfully")
        else:
            logger.warning("⚠️  Some database migrations failed")
    except Exception as e:
        logger.error(f"❌ Database migration error: {e}")
        # Don't fail startup if migrations fail

    # Initialize DynamoDB table for local development
    if settings.DEBUG:
        try:
            from app.services.dynamodb_cricket_scoring import DynamoDBService
            dynamodb_service = DynamoDBService()
            dynamodb_service.create_table_if_not_exists()
            logger.info("✅ DynamoDB table initialized")
        except Exception as e:
            logger.warning(f"⚠️  DynamoDB initialization failed: {e}")

    logger.info(f"🚀 Ready for cricket scoring at: http://localhost:8000")
    logger.info(f"📚 API Documentation: http://localhost:8000/docs")
    logger.info(f"🐛 Debug mode: {'ON' if settings.DEBUG else 'OFF'}")
    logger.info(f"🌍 Environment: {settings.ENVIRONMENT}")


# Shutdown event  
@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown"""
    logger.info("👋 Shutting down Kreeda Backend...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )
