from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routers.auth import router as auth_router
from src.routers.user_profile import router as user_profile_router
from src.utils.logger import setup_logging, logger

# Setup logging
setup_logging()

app = FastAPI(
    title="Kreeda Backend", 
    version="1.0.0",
    description="Digital scorekeeping app backend with Supabase-compatible auth",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(user_profile_router)

@app.on_event("startup")
async def startup_event():
    logger.info("Starting Kreeda Backend API")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Kreeda Backend API")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "kreeda-backend"}
