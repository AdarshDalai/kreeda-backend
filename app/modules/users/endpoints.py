"""
User Management API Endpoints

API routes for user management operations
"""

import math
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.modules.users.models import User, SportProfile
from app.modules.users.schemas import (
    User as UserSchema, UserCreate, UserUpdate, UserSummary, UserListResponse,
    UserWithProfile, SportProfile as SportProfileSchema, SportProfileCreate, 
    SportProfileUpdate
)
from app.modules.users.service import UserService

router = APIRouter(prefix="/users", tags=["users"])


# User CRUD endpoints
@router.post("", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """Create a new user account"""
    
    # Check if email already exists
    existing_email = await UserService.get_user_by_email(db, user_data.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if username already exists
    existing_username = await UserService.get_user_by_username(db, user_data.username)
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    user = await UserService.create_user(db, user_data)
    return user


@router.get("", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    sport_type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db_session)
):
    """List users with filtering and pagination"""
    
    users, total = await UserService.list_users(
        db, page, per_page, search, is_active, sport_type
    )
    
    return {
        "items": users,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": math.ceil(total / per_page) if total > 0 else 1
    }


@router.get("/{user_id}", response_model=UserWithProfile)
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Get a specific user by ID"""
    
    user = await UserService.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


@router.put("/{user_id}", response_model=UserSchema)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db_session)
):
    """Update user information"""
    
    # Check if email is being changed and already exists
    if user_data.email:
        existing_email = await UserService.get_user_by_email(db, user_data.email)
        if existing_email and existing_email.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    # Check if username is being changed and already exists
    if user_data.username:
        existing_username = await UserService.get_user_by_username(db, user_data.username)
        if existing_username and existing_username.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
    
    user = await UserService.update_user(db, user_id, user_data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Delete a user (soft delete)"""
    
    success = await UserService.delete_user(db, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )


# Sport Profile endpoints
@router.post("/{user_id}/sport-profiles", response_model=SportProfileSchema, status_code=status.HTTP_201_CREATED)
async def create_sport_profile(
    user_id: str,
    sport_data: SportProfileCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """Create a sport profile for a user"""
    
    sport_profile = await UserService.create_sport_profile(db, user_id, sport_data)
    if not sport_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found or sport profile already exists"
        )
    
    return sport_profile


@router.get("/{user_id}/sport-profiles/{sport_type}", response_model=SportProfileSchema)
async def get_sport_profile(
    user_id: str,
    sport_type: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Get sport profile for user and sport type"""
    
    sport_profile = await UserService.get_sport_profile(db, user_id, sport_type)
    if not sport_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sport profile not found"
        )
    
    return sport_profile


@router.put("/{user_id}/sport-profiles/{sport_type}", response_model=SportProfileSchema)
async def update_sport_profile(
    user_id: str,
    sport_type: str,
    sport_data: SportProfileUpdate,
    db: AsyncSession = Depends(get_db_session)
):
    """Update sport profile"""
    
    sport_profile = await UserService.update_sport_profile(db, user_id, sport_type, sport_data)
    if not sport_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sport profile not found"
        )
    
    return sport_profile


# Utility endpoints
@router.get("/check/email/{email}")
async def check_email_availability(
    email: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Check if email is available"""
    
    existing = await UserService.get_user_by_email(db, email)
    return {"available": existing is None}


@router.get("/check/username/{username}")
async def check_username_availability(
    username: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Check if username is available"""
    
    existing = await UserService.get_user_by_username(db, username)
    return {"available": existing is None}