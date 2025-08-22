"""
User Profile and Management Endpoints

Comprehensive user profile endpoints including:
- Public user profiles
- Admin user management 
- User search and discovery
- Bulk operations
- User statistics and activity
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
import math
from uuid import UUID

from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user, get_current_active_user
from app.repositories.user import user_repository
from app.models.user import User, UserRole
from app.schemas.users import (
    PublicUserProfile, DetailedUserProfile, UserSearchFilters,
    PaginatedUsersResponse, UserSearchResult, AdminUserUpdate,
    BulkUserActionRequest, BulkActionResult, UserActivityResponse,
    UserPreferences, UpdateUserPreferencesRequest
)
from app.schemas.auth import UserResponse, UserRole as SchemaUserRole

router = APIRouter()


def require_admin_role(current_user: User = Depends(get_current_active_user)) -> User:
    """Dependency to require admin role."""
    if current_user.role not in [UserRole.ADMIN, UserRole.ORGANIZER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or organizer privileges required"
        )
    return current_user


# Public User Profile Endpoints

@router.get("/{user_id}/profile", response_model=PublicUserProfile)
async def get_user_public_profile(
    user_id: UUID = Path(..., description="User ID"),
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a user's public profile."""
    user = await user_repository.get_user_by_id(db, str(user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Note: We'll use model_validate to properly handle SQLAlchemy models
    # This automatically converts Column types to Python values
    return PublicUserProfile.model_validate(user)


@router.get("/{user_id}/detailed", response_model=DetailedUserProfile) 
async def get_user_detailed_profile(
    user_id: UUID = Path(..., description="User ID"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed user profile (own profile or admin only)."""
    # Check if user is viewing their own profile or is admin
    if str(current_user.id) != str(user_id) and current_user.role not in [UserRole.ADMIN, UserRole.ORGANIZER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only view your own detailed profile"
        )
    
    user = await user_repository.get_user_by_id(db, str(user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return DetailedUserProfile.model_validate(user)


# User Search and Discovery

@router.get("/search", response_model=PaginatedUsersResponse)
async def search_users(
    query: Optional[str] = Query(None, description="Search query"),
    role: Optional[SchemaUserRole] = Query(None, description="Filter by role"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    email_verified: Optional[bool] = Query(None, description="Filter by email verification"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    order_by: str = Query("created_at", description="Order by field"),
    order_dir: str = Query("desc", regex="^(asc|desc)$", description="Order direction"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Search users with filters and pagination."""
    
    # Convert schema role to model role if provided
    model_role = None
    if role:
        try:
            model_role = UserRole(role.value)
        except ValueError:
            model_role = None
    
    # Build search filters
    filters = UserSearchFilters(
        query=query,
        role=model_role,
        is_active=is_active,
        email_verified=email_verified
    )
    
    # Search users
    users, total = await user_repository.search_users(
        db, filters, page, size, order_by, order_dir
    )
    
    # Calculate pagination info
    pages = math.ceil(total / size) if total > 0 else 1
    has_next = page < pages
    has_prev = page > 1
    
    # Convert to search results using model_validate for proper type conversion
    user_results = [UserSearchResult.model_validate(user) for user in users]
    
    return PaginatedUsersResponse(
        users=user_results,
        total=total,
        page=page,
        size=size,
        pages=pages,
        has_next=has_next,
        has_prev=has_prev
    )


@router.get("/", response_model=PaginatedUsersResponse)
async def get_users(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    role: Optional[SchemaUserRole] = Query(None, description="Filter by role"),
    current_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db)
):
    """Get all users (admin only)."""
    
    # Convert schema role to model role if provided
    model_role = None
    if role:
        try:
            model_role = UserRole(role.value)
        except ValueError:
            model_role = None
    
    filters = UserSearchFilters(
        query=None,
        is_active=is_active,
        role=model_role
    )
    
    users, total = await user_repository.search_users(db, filters, page, size)
    
    # Calculate pagination info
    pages = math.ceil(total / size) if total > 0 else 1
    has_next = page < pages
    has_prev = page > 1
    
    # Convert to search results using model_validate for proper type conversion
    user_results = [UserSearchResult.model_validate(user) for user in users]
    
    return PaginatedUsersResponse(
        users=user_results,
        total=total,
        page=page,
        size=size,
        pages=pages,
        has_next=has_next,
        has_prev=has_prev
    )


# Individual User Management

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID = Path(..., description="User ID"),
    current_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db)
):
    """Get user by ID (admin only)."""
    user = await user_repository.get_user_by_id(db, str(user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse.model_validate(user)


@router.put("/{user_id}", response_model=UserResponse)
async def admin_update_user(
    user_id: UUID,
    update_data: AdminUserUpdate,
    current_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db)
):
    """Update user (admin only)."""
    
    # Check if user exists
    existing_user = await user_repository.get_user_by_id(db, str(user_id))
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Perform update
    updated_user = await user_repository.admin_update_user(
        db, str(user_id), update_data.dict(exclude_unset=True)
    )
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )
    
    return UserResponse.model_validate(updated_user)


@router.delete("/{user_id}", status_code=status.HTTP_200_OK)
async def admin_deactivate_user(
    user_id: UUID = Path(..., description="User ID"),
    current_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db)
):
    """Deactivate user (admin only)."""
    
    # Check if user exists
    user = await user_repository.get_user_by_id(db, str(user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Don't allow deactivating self
    if str(current_user.id) == str(user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )
    
    # Deactivate user
    await user_repository.deactivate_user(db, str(user_id))
    
    return {"message": "User deactivated successfully"}


# Bulk Operations

@router.post("/bulk-action", response_model=BulkActionResult)
async def bulk_user_action(
    action_request: BulkUserActionRequest,
    current_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db)
):
    """Perform bulk action on multiple users (admin only)."""
    
    # Validate user IDs exist
    users = await user_repository.get_users_by_ids(db, [str(uid) for uid in action_request.user_ids])
    if len(users) != len(action_request.user_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or more user IDs not found"
        )
    
    # Don't allow bulk actions on self
    if current_user.id in action_request.user_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot perform bulk actions on your own account"
        )
    
    # Perform bulk action
    result = await user_repository.bulk_action_users(
        db, [str(uid) for uid in action_request.user_ids], action_request.action
    )
    
    action_messages = {
        "activate": "users activated",
        "deactivate": "users deactivated", 
        "verify_email": "user emails verified",
        "reset_failed_attempts": "user login attempts reset",
        "delete": "users deleted"
    }
    
    message = f"{result['success_count']} {action_messages.get(action_request.action.value, 'users processed')}"
    if result['failed_count'] > 0:
        message += f", {result['failed_count']} failed"
    
    return BulkActionResult(
        success_count=result["success_count"],
        failed_count=result["failed_count"],
        failed_users=result["failed_users"],
        message=message
    )


# User Statistics and Analytics

@router.get("/analytics/summary")
async def get_user_analytics_summary(
    days: int = Query(30, ge=1, le=365, description="Number of days for analysis"),
    current_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db)
):
    """Get user analytics summary (admin only)."""
    
    summary = await user_repository.get_user_activity_summary(db, days)
    return summary


# User Preferences and Settings (for future implementation)

@router.get("/{user_id}/preferences", response_model=UserPreferences)
async def get_user_preferences(
    user_id: UUID = Path(..., description="User ID"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user preferences."""
    
    # Check if user is viewing their own preferences or is admin
    if str(current_user.id) != str(user_id) and current_user.role not in [UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only view your own preferences"
        )
    
    # TODO: Implement preferences storage and retrieval
    # For now, return default preferences
    return UserPreferences()


@router.put("/{user_id}/preferences", response_model=UserPreferences)
async def update_user_preferences(
    user_id: UUID,
    preferences: UpdateUserPreferencesRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user preferences."""
    
    # Check if user is updating their own preferences
    if str(current_user.id) != str(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only update your own preferences"
        )
    
    # TODO: Implement preferences storage and update
    # For now, return default preferences
    return UserPreferences()
