from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, teams, matches, tournaments, scores, oauth2

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(oauth2.router, prefix="/auth/oauth2", tags=["oauth2"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(teams.router, prefix="/teams", tags=["teams"])
api_router.include_router(matches.router, prefix="/matches", tags=["matches"])
api_router.include_router(tournaments.router, prefix="/tournaments", tags=["tournaments"])
api_router.include_router(scores.router, prefix="/scores", tags=["scores"])
