from fastapi import FastAPI
from src.routers.auth import router as auth_router
from src.routers.user_profile import router as user_profile_router
from src.routers.cricket.profile import router as cricket_profile_router
from src.routers.cricket.team import router as cricket_team_router
from src.routers.cricket.match import router as cricket_match_router
from src.middleware.error_handler import register_exception_handlers

app = FastAPI(
    title="Kreeda Backend", 
    version="1.0.0",
    description="Digital scorekeeping app backend with Supabase-compatible auth"
)

# Register global exception handlers
register_exception_handlers(app)

# Include routers
app.include_router(auth_router)
app.include_router(user_profile_router)
app.include_router(cricket_profile_router)
app.include_router(cricket_team_router, prefix="/api/v1/cricket")
app.include_router(cricket_match_router, prefix="/api/v1/cricket")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}