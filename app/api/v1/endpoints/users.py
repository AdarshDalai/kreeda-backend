from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_users():
    """Get all users."""
    return {"message": "Get users endpoint - Coming soon!"}

@router.get("/{user_id}")
async def get_user(user_id: str):
    """Get user by ID."""
    return {"message": f"Get user {user_id} endpoint - Coming soon!"}

@router.put("/{user_id}")
async def update_user(user_id: str):
    """Update user profile."""
    return {"message": f"Update user {user_id} endpoint - Coming soon!"}
