from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import time
import logging

from app.core.config import settings
from app.core.database import init_db
from app.core.migrations import run_migrations
from app.api.v1.api import api_router
from app.core.exceptions import setup_exception_handlers

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

def create_application() -> FastAPI:
    """Create and configure FastAPI application."""
    
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=settings.DESCRIPTION,
        openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
        docs_url=f"{settings.API_V1_PREFIX}/docs",
        redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    )

    # Set up CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add trusted host middleware for security
    if settings.ENVIRONMENT == "production":
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.ALLOWED_HOSTS
        )

    # Request timing middleware
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response

    # Include API routes
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    # Setup exception handlers
    setup_exception_handlers(app)

    return app

# Create app instance
app = create_application()

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    logger.info("🏏 Starting Kreeda API...")
    
    # Run database migrations first
    try:
        run_migrations()
        logger.info("✅ Migrations completed successfully")
    except Exception as e:
        logger.warning(f"⚠️ Migration failed, but continuing startup: {e}")
    
    # Initialize database
    await init_db()
    
    logger.info("✅ Kreeda API started successfully!")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown."""
    logger.info("👋 Shutting down Kreeda API...")

@app.get("/")
async def root():
    """Root endpoint for health check."""
    return {
        "message": "Welcome to Kreeda API! 🏏⚽🏑",
        "version": settings.VERSION,
        "docs_url": f"{settings.API_V1_PREFIX}/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "service": "kreeda-api",
        "version": settings.VERSION
    }
