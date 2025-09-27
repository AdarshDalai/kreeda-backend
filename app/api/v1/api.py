"""
Kreeda Backend API Router

Main API router aggregating all endpoint modules
"""

from fastapi import APIRouter

from app.api.v1.endpoints import health, auth
from app.modules.users import user_router
from app.modules.teams import team_router
from app.modules.cricket import cricket_router

# Create main API router
api_router = APIRouter()

# Include endpoint routers
api_router.include_router(
    health.router,
    prefix="/health",
    tags=["Health Check"]
)

api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"]
)

api_router.include_router(
    cricket_router,
    prefix="/api/v1",
    tags=["Cricket"]
)

# Include modular routers
api_router.include_router(
    user_router,
    prefix="/api/v1",
    tags=["User Management"]
)

api_router.include_router(
    team_router,
    prefix="/api/v1",
    tags=["Team Management"]
)