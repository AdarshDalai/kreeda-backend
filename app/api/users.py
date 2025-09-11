from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import logging

from app.utils.database import get_db
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate, UserSearch
from app.services.user_service import UserService
from app.auth.middleware import get_current_active_user
from app.auth import supabase_auth

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
async def users_health():
    """Health check for users endpoints"""
    return {"success": True, "message": "Users service healthy"}


@router.get("/", response_model=List[UserResponse])
async def get_users(
    skip: int = Query(0, ge=0, description="Number of users to skip"),
    limit: int = Query(50, ge=1, le=100, description="Number of users to retrieve"),
    search: Optional[str] = Query(
        None, description="Search term for username, full name, or email"
    ),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get list of users with optional filters"""
    try:
        users = await UserService.get_users(
            db=db, skip=skip, limit=limit, search=search, is_active=is_active
        )

        return users
    except Exception as e:
        logger.error(f"Error retrieving users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users",
        )


@router.get("/count")
async def get_user_count(
    search: Optional[str] = Query(
        None, description="Search term for username, full name, or email"
    ),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get total count of users with filters"""
    try:
        count = await UserService.get_user_count(
            db=db, search=search, is_active=is_active
        )

        return {"count": count}
    except Exception as e:
        logger.error(f"Error getting user count: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user count",
        )


@router.get("/search", response_model=List[UserSearch])
async def search_users(
    q: str = Query(..., min_length=2, description="Search query for username"),
    limit: int = Query(10, ge=1, le=50, description="Number of results to return"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Search users by username for autocomplete"""
    try:
        users = await UserService.search_users_by_username(
            db=db, username_query=q, limit=limit
        )

        return users
    except Exception as e:
        logger.error(f"Error searching users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search users",
        )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get user by ID"""
    try:
        user = await UserService.get_user_by_id(db=db, user_id=user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user",
        )


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    update_supabase: bool = Query(True, description="Update user in Supabase as well"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update user information"""
    try:
        # Check if user exists
        existing_user = await UserService.get_user_by_id(db=db, user_id=user_id)
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Check if current user can update this user (self or admin)
        if str(current_user.id) != user_id:
            # Here you could add admin role check
            # For now, users can only update themselves
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own profile",
            )

        # Check for username conflicts
        if user_update.username:
            existing_username = await UserService.get_user_by_username(
                db=db, username=user_update.username
            )
            if existing_username and str(existing_username.id) != user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already exists",
                )

        # Check for email conflicts
        if user_update.email:
            existing_email = await UserService.get_user_by_email(
                db=db, email=str(user_update.email)
            )
            if existing_email and str(existing_email.id) != user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already exists",
                )

        # Update user
        updated_user = await UserService.update_user(
            db=db,
            user_id=user_id,
            user_data=user_update,
            update_supabase=update_supabase,
        )

        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update user",
            )

        return updated_user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user",
        )


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    hard_delete: bool = Query(
        False, description="Permanently delete user (default: soft delete)"
    ),
    delete_from_supabase: bool = Query(
        True, description="Delete user from Supabase as well"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete user (soft delete by default, hard delete optional)"""
    try:
        # Check if user exists
        existing_user = await UserService.get_user_by_id(db=db, user_id=user_id)
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Check permissions (users can only delete themselves, or admin required)
        if str(current_user.id) != user_id:
            # Here you could add admin role check
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own account",
            )

        if hard_delete:
            success = await UserService.hard_delete_user(
                db=db, user_id=user_id, delete_from_supabase=delete_from_supabase
            )
            message = "User permanently deleted"
        else:
            success = await UserService.delete_user(db=db, user_id=user_id)
            message = "User deactivated"

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete user",
            )

        return {"message": message}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user",
        )
