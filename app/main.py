from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from app.config import settings
from app.utils.database import init_db
from app.api import auth, users, teams, cricket, stats, user_profile
from app.api import cricket_integrity


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting up Kreeda API...")
    await init_db()
    yield
    # Shutdown
    logger.info("Shutting down Kreeda API...")


# Create FastAPI app
app = FastAPI(
    title=settings.project_name,
    version=settings.project_version,
    description="Kreeda - Digital Cricket Scorekeeping Platform",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": exc.detail,
            },
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An internal server error occurred",
            },
        },
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "success": True,
        "data": {
            "status": "healthy",
            "environment": settings.environment,
            "version": settings.project_version,
        },
    }


# Include API routers
app.include_router(auth.router, prefix=f"{settings.api_v1_str}/auth", tags=["auth"])
app.include_router(users.router, prefix=f"{settings.api_v1_str}/users", tags=["users"])
app.include_router(user_profile.router, prefix=f"{settings.api_v1_str}/user", tags=["user-profile"])
app.include_router(teams.router, prefix=f"{settings.api_v1_str}/teams", tags=["teams"])
app.include_router(cricket.router, prefix=f"{settings.api_v1_str}/matches", tags=["cricket"])
app.include_router(cricket_integrity.router, prefix=f"{settings.api_v1_str}/matches", tags=["cricket-integrity"])
app.include_router(stats.router, prefix=f"{settings.api_v1_str}/stats", tags=["statistics"])


# WebSocket endpoint for live match updates
@app.websocket("/ws/matches/{match_id}")
async def websocket_endpoint(websocket: WebSocket, match_id: str):
    from app.utils.websocket import websocket_manager
    
    await websocket_manager.connect_to_match(websocket, match_id)
    try:
        while True:
            # Keep connection alive and listen for disconnection
            await websocket.receive_text()
    except Exception as e:
        logger.info(f"WebSocket connection closed: {e}")
    finally:
        websocket_manager.disconnect_from_match(websocket, match_id)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
