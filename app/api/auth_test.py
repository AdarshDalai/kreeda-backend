from fastapi import APIRouter

# Create router
router = APIRouter()

@router.get("/test")
async def test():
    return {"message": "test"}
