from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import logging

from app.utils.database import get_db
from app.auth.middleware import get_current_user
from app.models.user import User
from app.services.user_profile_service import UserProfileService
from app.schemas.user_profile import (
    UserProfileUpdate,
    UserPasswordChange,
    UserPrivacySettings,
    UserNotificationSettings,
    UserPreferencesSettings,
    UserSportsProfile,
    UserProfileResponse,
    UserDashboardStats,
    UserActivityLog,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/profile", tags=["User Profile"])
security = HTTPBearer()


@router.get("/", response_model=UserProfileResponse)
async def get_profile(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """Get complete user profile with all settings"""
    try:
        profile = await UserProfileService.get_complete_profile(
            db, str(current_user.id)
        )

        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found"
            )

        return profile

    except Exception as e:
        logger.error(f"Error getting profile for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get profile",
        )


@router.put("/", response_model=UserProfileResponse)
async def update_profile(
    profile_update: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update user profile information"""
    try:
        updated_user = await UserProfileService.update_profile(
            db, str(current_user.id), profile_update
        )

        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Get complete profile
        profile = await UserProfileService.get_complete_profile(
            db, str(current_user.id)
        )
        return profile

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating profile for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile",
        )


@router.post("/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload and set user avatar"""
    try:
        avatar_url = await UserProfileService.upload_avatar(
            db, str(current_user.id), file
        )

        return {"message": "Avatar uploaded successfully", "avatar_url": avatar_url}

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error uploading avatar for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload avatar",
        )


@router.put("/privacy")
async def update_privacy_settings(
    privacy_settings: UserPrivacySettings,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update user privacy settings"""
    try:
        success = await UserProfileService.update_privacy_settings(
            db, str(current_user.id), privacy_settings
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update privacy settings",
            )

        return {"message": "Privacy settings updated successfully"}

    except Exception as e:
        logger.error(f"Error updating privacy settings for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update privacy settings",
        )


@router.put("/notifications")
async def update_notification_settings(
    notification_settings: UserNotificationSettings,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update user notification settings"""
    try:
        success = await UserProfileService.update_notification_settings(
            db, str(current_user.id), notification_settings
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update notification settings",
            )

        return {"message": "Notification settings updated successfully"}

    except Exception as e:
        logger.error(
            f"Error updating notification settings for user {current_user.id}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update notification settings",
        )


@router.put("/password")
async def change_password(
    password_change: UserPasswordChange,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    authorization: HTTPAuthorizationCredentials = Depends(security),
):
    """Change user password"""
    try:
        # Extract token from Authorization header
        access_token = authorization.credentials

        success = await UserProfileService.change_password(
            db, str(current_user.id), password_change, access_token
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to change password",
            )

        return {"message": "Password changed successfully"}

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error changing password for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password",
        )


@router.get("/dashboard", response_model=UserDashboardStats)
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """Get user dashboard statistics"""
    try:
        stats = await UserProfileService.get_dashboard_stats(db, str(current_user.id))
        return stats

    except Exception as e:
        logger.error(f"Error getting dashboard stats for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get dashboard stats",
        )


@router.get("/activity", response_model=List[UserActivityLog])
async def get_activity_logs(
    limit: int = Query(50, ge=1, le=100),
    activity_type: Optional[str] = Query(None, description="Filter by activity type"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user activity logs"""
    try:
        logs = await UserProfileService.get_activity_logs(
            db, str(current_user.id), limit, activity_type
        )

        return logs

    except Exception as e:
        logger.error(f"Error getting activity logs for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get activity logs",
        )


@router.delete("/")
async def delete_account(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """Soft delete user account (GDPR compliance)"""
    try:
        success = await UserProfileService.delete_account(db, str(current_user.id))

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to delete account",
            )

        return {"message": "Account deleted successfully"}

    except Exception as e:
        logger.error(f"Error deleting account for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete account",
        )


@router.get("/completion")
async def get_profile_completion(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """Get profile completion percentage and suggestions"""
    try:
        profile = await UserProfileService.get_complete_profile(
            db, str(current_user.id)
        )

        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found"
            )

        # Calculate what's missing for completion suggestions
        suggestions = []

        if not profile.avatar_url:
            suggestions.append("Upload a profile picture")

        if not profile.bio:
            suggestions.append("Add a bio to tell others about yourself")

        if not profile.location:
            suggestions.append("Add your location")

        if not profile.birth_date:
            suggestions.append("Add your birth date")

        # Fix sports profile check
        sports_profile = profile.sports_profile or {}
        if not sports_profile or not (
            isinstance(sports_profile, dict) and sports_profile.get("favorite_sports")
        ):
            suggestions.append("Add your favorite sports")

        return {
            "completion_percentage": 0,  # Will be calculated properly in service
            "suggestions": suggestions,
            "completed_sections": {
                "basic_info": bool(
                    profile.full_name and profile.email and profile.username
                ),
                "profile_details": bool(profile.bio and profile.location),
                "avatar": bool(profile.avatar_url),
                "sports_profile": bool(
                    sports_profile
                    and isinstance(sports_profile, dict)
                    and sports_profile.get("favorite_sports")
                ),
                "privacy_settings": bool(profile.privacy_settings),
                "notification_settings": bool(profile.notification_settings),
            },
        }

    except Exception as e:
        logger.error(
            f"Error getting profile completion for user {current_user.id}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get profile completion",
        )
