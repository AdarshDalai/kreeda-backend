from fastapi import FastAPI
from src.routers.auth import router as auth_router
from src.routers.user_profile import router as user_profile_router
from src.routers.cricket.profile import router as cricket_profile_router

app = FastAPI(
    title="Kreeda Backend", 
    version="1.0.0",
    description="Digital scorekeeping app backend with Supabase-compatible auth"
)

# Include routers
app.include_router(auth_router)
app.include_router(user_profile_router)
app.include_router(cricket_profile_router)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}