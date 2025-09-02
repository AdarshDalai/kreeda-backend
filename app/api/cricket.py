from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def cricket_health():
    return {"success": True, "message": "Cricket service healthy"}
