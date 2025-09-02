from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def auth_health():
    return {"success": True, "message": "Auth service healthy"}
