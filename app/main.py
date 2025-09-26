"""
Kreeda Backend - Main FastAPI Application

Digital Sports Scorekeeping Platform with focus on Cricket MVP
"""

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from app.core.config import settings
from app.api.v1.api import api_router
from app.core.events import startup_handler, shutdown_handler


def create_application() -> FastAPI:
    """Create and configure the FastAPI application"""
    
    # Create FastAPI app with metadata
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Digital Sports Scorekeeping Platform with Progressive Scoring Integrity",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        openapi_url="/openapi.json" if settings.DEBUG else None,
    )

    # CORS Configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["*"],
    )

    # Event handlers
    app.add_event_handler("startup", startup_handler)
    app.add_event_handler("shutdown", shutdown_handler)

    # Health check endpoint
    @app.get("/health", tags=["Health"])
    async def health_check():
        """Health check endpoint for monitoring"""
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "healthy",
                "service": settings.APP_NAME,
                "version": settings.APP_VERSION,
                "environment": settings.ENVIRONMENT
            }
        )

    # Root endpoint
    @app.get("/", tags=["Root"])
    async def root():
        """Root endpoint with API information"""
        return {
            "message": f"Welcome to {settings.APP_NAME}",
            "version": settings.APP_VERSION,
            "docs": "/docs" if settings.DEBUG else "Documentation disabled in production",
            "health": "/health"
        }

    # Include API router
    app.include_router(api_router, prefix="/api/v1")

    return app


# Create the FastAPI app instance
app = create_application()


if __name__ == "__main__":
    # Development server configuration
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info",
    )