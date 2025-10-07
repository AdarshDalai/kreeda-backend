from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from src.schemas.user_profile import UserProfileCreateRequest, UserProfileUpdateRequest, UserProfileResponse
from src.services.user_profile import UserProfileService
from src.services.auth import AuthService
from src.database.connection import get_db

router = APIRouter(prefix="/user/profile", tags=["user-profile"])

async def get_current_user_id(authorization: Optional[str] = Header(None), db: AsyncSession = Depends(get_db)) -> str:
    """Extract user ID from authorization header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    try:
        token = authorization.split(" ")[1]
        user = await AuthService.get_user_from_token(token, db)
        return str(user.id)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.get("/", response_model=UserProfileResponse, summary="Get user profile")
async def get_profile(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get the current user's profile."""
    try:
        return await UserProfileService.get_profile(user_id, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/", response_model=UserProfileResponse, summary="Create user profile")
async def create_profile(
    request: UserProfileCreateRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Create a profile for the current user."""
    try:
        return await UserProfileService.create_profile(user_id, request, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/", response_model=UserProfileResponse, summary="Update user profile")
async def update_profile(
    request: UserProfileUpdateRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Update the current user's profile."""
    try:
        return await UserProfileService.update_profile(user_id, request, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/", summary="Delete user profile")
async def delete_profile(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Delete the current user's profile."""
    try:
        return await UserProfileService.delete_profile(user_id, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# Additional endpoints for admin or public access
@router.get("/{profile_user_id}", response_model=UserProfileResponse, summary="Get user profile by ID")
async def get_profile_by_id(
    profile_user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a user's profile by their user ID (public access)."""
    try:
        return await UserProfileService.get_profile(profile_user_id, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))