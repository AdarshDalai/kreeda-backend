"""
Kreeda Backend API Router

Main API router aggregating all endpoint modules
"""

from fastapi import APIRouter

from app.api.v1.endpoints import health, auth

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

# Additional routers will be added as we implement them:
# api_router.include_router(users.router, prefix="/users", tags=["Users"])
# api_router.include_router(teams.router, prefix="/teams", tags=["Teams"])  
# api_router.include_router(matches.router, prefix="/matches", tags=["Matches"])
# api_router.include_router(cricket.router, prefix="/cricket", tags=["Cricket"])