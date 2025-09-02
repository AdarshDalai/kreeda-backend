from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def auth_health():
    return {"message": "Auth service is healthy"}

