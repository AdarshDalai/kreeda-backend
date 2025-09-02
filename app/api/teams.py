from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def teams_health():
    return {"success": True, "message": "Teams service healthy"}
