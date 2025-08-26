"""
Kreeda Backend - Main FastAPI Application
Cricket scoring made simple, fast, and reliable
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from websockets.exceptions import ConnectionClosedOK, ConnectionClosedError
import json
from typing import Dict, List
import asyncio
import logging

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.middleware import SecurityHeadersMiddleware, RequestLoggingMiddleware, RateLimitMiddleware
from app.api.cricket import router as cricket_router
from app.api.auth import router as auth_router

# Setup logging
logger = setup_logging()


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Digital cricket scoring and team management API",
    docs_url="/docs" if settings.DEBUG else None,  # Disable docs in production
    redoc_url="/redoc" if settings.DEBUG else None
)

# Add middleware in correct order (last added = first executed)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)

if not settings.DEBUG:
    app.add_middleware(RateLimitMiddleware, calls_per_minute=settings.RATE_LIMIT_PER_MINUTE)

# Security Middleware
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["localhost", "127.0.0.1", "*.kreeda.app"]
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(cricket_router)


# WebSocket Connection Manager for Real-time Scoring
class ConnectionManager:
    """Manage WebSocket connections for live match updates"""
    
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, match_id: int):
        """Connect client to match updates"""
        await websocket.accept()
        if match_id not in self.active_connections:
            self.active_connections[match_id] = []
        self.active_connections[match_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, match_id: int):
        """Disconnect client"""
        if match_id in self.active_connections:
            self.active_connections[match_id].remove(websocket)
            if not self.active_connections[match_id]:
                del self.active_connections[match_id]
    
    async def send_to_match(self, match_id: int, message: dict):
        """Send message to all clients watching a match"""
        if match_id not in self.active_connections:
            return
            
        disconnected = []
        for connection in self.active_connections[match_id]:
            try:
                await connection.send_text(json.dumps(message))
            except ConnectionClosedOK:
                disconnected.append(connection)
            except ConnectionClosedError:
                disconnected.append(connection)
            except WebSocketDisconnect:
                disconnected.append(connection)
            except Exception as e:
                # Log the actual error instead of swallowing it
                logger.warning(
                    f"WebSocket send error for match {match_id}: {e}",
                    extra={"match_id": match_id, "error": str(e)}
                )
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection, match_id)


# Global connection manager
connection_manager = ConnectionManager()


# WebSocket endpoint for live match updates
@app.websocket("/ws/match/{match_id}")
async def websocket_match_updates(websocket: WebSocket, match_id: int):
    """WebSocket endpoint for real-time match updates"""
    await connection_manager.connect(websocket, match_id)
    
    try:
        # Send welcome message
        await websocket.send_text(json.dumps({
            "type": "connection_established",
            "match_id": match_id,
            "message": "Connected to live match updates"
        }))
        
        # Keep connection alive with heartbeat
        while True:
            await asyncio.sleep(settings.WS_HEARTBEAT_INTERVAL)
            await websocket.send_text(json.dumps({
                "type": "heartbeat",
                "timestamp": "2024-01-01T00:00:00Z"  # Use proper timestamp
            }))
    
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket, match_id)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Application health check"""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "message": "Ready for cricket scoring!"
    }


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
