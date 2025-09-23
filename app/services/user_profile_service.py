import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy import and_, delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import supabase_auth
from app.models.user import User
from app.models.user_profile import (
    UserAchievement,
    UserActivityLog,
    UserProfile,
    UserSecuritySettings,
    UserSession,
)
from app.schemas.user_profile import UserActivityLog as ActivityLogSchema
from app.schemas.user_profile import (
    UserDashboardStats,
    UserNotificationSettings,
    UserPasswordChange,
    UserPreferencesSettings,
    UserPrivacySettings,
    UserProfileResponse,
    UserProfileUpdate,
    UserSportsProfile,
)
from app.utils.file_upload import FileUploadService

logger = logging.getLogger(__name__)


class UserProfileService:
    """Comprehensive user profile management service"""

    @staticmethod
    async def get_complete_profile(
        db: AsyncSession, user_id: str
    ) -> Optional[UserProfileResponse]:
        """Get complete user profile with all settings"""
        try:
            # Convert string UUID to UUID object for database query
            user_uuid = UUID(user_id)
            result = await db.execute(
                select(User)
                .options(
                    selectinload(User.profile), selectinload(User.security_settings)
                )
                .where(User.id == user_uuid)
            )
            user = result.scalar_one_or_none()

            if not user:
                return None

            # Check if profile exists
            has_profile = user.profile is not None
            
            # Re-query to get the complete user with profile
            if not has_profile:
                await UserProfileService.create_default_profile(db, user_id)
                # Re-query to get the complete user with profile
                result = await db.execute(
                    select(User)
                    .options(
                        selectinload(User.profile), selectinload(User.security_settings)
                    )
                    .where(User.id == user_uuid)
                )
                user = result.scalar_one_or_none()
                
                if not user:
                    return None

            # Now capture all data while we have proper session context
            user_data = {
                'id': user.id,
                'email': user.email, 
                'username': user.username,
                'full_name': user.full_name,
                'avatar_url': user.avatar_url,
                'created_at': user.created_at,
                'updated_at': user.updated_at,
                'is_active': user.is_active,
            }

            profile_data = {}
            if user.profile:
                profile_data = {
                    'display_name': user.profile.display_name,
                    'bio': user.profile.bio,
                    'location': user.profile.location,
                    'website': user.profile.website,
                    'birth_date': user.profile.birth_date,
                    'last_login': user.profile.last_login,
                    'app_preferences': user.profile.app_preferences,
                    'privacy_settings': user.profile.privacy_settings,
                    'notification_settings': user.profile.notification_settings,
                    'sports_profile': user.profile.sports_profile,
                }

            return UserProfileResponse(
                id=user_data['id'],
                email=user_data['email'],
                username=user_data['username'],
                full_name=user_data['full_name'],
                display_name=profile_data.get('display_name'),
                avatar_url=user_data['avatar_url'],
                bio=profile_data.get('bio'),
                location=profile_data.get('location'),
                website=profile_data.get('website'),
                birth_date=profile_data.get('birth_date'),
                created_at=user_data['created_at'],
                updated_at=user_data['updated_at'],
                is_active=user_data['is_active'],
                last_login=profile_data.get('last_login'),
                profile_settings=profile_data.get('app_preferences'),
                privacy_settings=profile_data.get('privacy_settings'),
                notification_settings=profile_data.get('notification_settings'),
                sports_profile=profile_data.get('sports_profile'),
            )

        except Exception as e:
            logger.error(f"Error getting complete profile for user {user_id}: {e}")
            raise Exception(f"Failed to get profile: {str(e)}")

    @staticmethod
    async def create_default_profile(db: AsyncSession, user_id: str) -> UserProfile:
        """Create default profile for new user"""
        try:
            # Convert string UUID to UUID object for database operations
            user_uuid = UUID(user_id)
            profile = UserProfile(
                user_id=user_uuid,
                profile_completion_percentage=30.0,  # Basic info completed
            )

            db.add(profile)
            await db.commit()
            await db.refresh(profile)

            # Create default security settings
            security_settings = UserSecuritySettings(user_id=user_uuid)
            db.add(security_settings)
            await db.commit()

            logger.info(f"Created default profile for user {user_id}")
            return profile

        except Exception as e:
            logger.error(f"Error creating default profile for user {user_id}: {e}")
            await db.rollback()
            raise Exception(f"Failed to create default profile: {str(e)}")

    @staticmethod
    async def update_profile(
        db: AsyncSession, user_id: str, profile_update: UserProfileUpdate
    ) -> Optional[User]:
        """Update user profile information"""
        try:
            # Convert string UUID to UUID object for database query
            user_uuid = UUID(user_id)
            # Get user and profile
            result = await db.execute(
                select(User)
                .options(selectinload(User.profile))
                .where(User.id == user_uuid)
            )
            user = result.scalar_one_or_none()

            if not user:
                return None

            # Capture ALL needed data immediately after query to avoid greenlet issues
            user_data = {
                'email': user.email,
                'username': user.username,
                'full_name': user.full_name,
                'avatar_url': user.avatar_url,
            }
            
            profile_data = {}
            has_profile = user.profile is not None
            if has_profile:
                profile_data = {
                    'display_name': user.profile.display_name,
                    'bio': user.profile.bio,
                    'location': user.profile.location,
                    'website': user.profile.website,
                    'birth_date': user.profile.birth_date,
                    'phone_number': user.profile.phone_number,
                    'privacy_settings': user.profile.privacy_settings,
                    'app_preferences': user.profile.app_preferences,
                    'sports_profile': user.profile.sports_profile,
                    'notification_settings': user.profile.notification_settings,
                }

            # Update user basic fields
            update_data = profile_update.model_dump(exclude_unset=True)

            # Update User model fields
            user_fields = ["email", "username", "full_name", "avatar_url"]
            for field in user_fields:
                if field in update_data:
                    setattr(user, field, update_data[field])

            # Get or create profile
            if not has_profile:
                await UserProfileService.create_default_profile(db, user_id)
                # Flush the current session to ensure the profile is saved
                await db.flush()
                
                # Re-query to get the profile with fresh session
                result = await db.execute(
                    select(User)
                    .options(selectinload(User.profile))
                    .where(User.id == user_uuid)
                )
                user = result.scalar_one_or_none()
                
                if not user:
                    return None
                    
                if not user.profile:
                    # Try refresh if selectinload didn't work
                    await db.refresh(user, ['profile'])
                    
                if not user.profile:
                    return None
                
                # Capture new profile data
                profile_data = {
                    'display_name': user.profile.display_name,
                    'bio': user.profile.bio,
                    'location': user.profile.location,
                    'website': user.profile.website,
                    'birth_date': user.profile.birth_date,
                    'phone_number': user.profile.phone_number,
                    'privacy_settings': user.profile.privacy_settings,
                    'app_preferences': user.profile.app_preferences,
                    'sports_profile': user.profile.sports_profile,
                    'notification_settings': user.profile.notification_settings,
                }

            # Update profile fields
            profile_fields = [
                "display_name",
                "bio",
                "location",
                "website",
                "birth_date",
                "phone_number",
            ]

            for field in profile_fields:
                if field in update_data:
                    setattr(user.profile, field, update_data[field])
                    # Update our captured data too
                    profile_data[field] = update_data[field]

            # Update privacy settings
            if (
                "profile_visibility" in update_data
                or "email_visibility" in update_data
                or "show_online_status" in update_data
            ):
                privacy_settings = profile_data.get('privacy_settings') or {}
                for key in [
                    "profile_visibility",
                    "email_visibility",
                    "show_online_status",
                ]:
                    if key in update_data:
                        privacy_settings[key] = update_data[key]
                user.profile.privacy_settings = privacy_settings
                profile_data['privacy_settings'] = privacy_settings

            # Update app preferences
            if any(
                key in update_data
                for key in ["preferred_theme", "preferred_language", "timezone"]
            ):
                app_prefs = profile_data.get('app_preferences') or {}
                for key in ["preferred_theme", "preferred_language", "timezone"]:
                    if key in update_data:
                        app_prefs[key] = update_data[key]
                user.profile.app_preferences = app_prefs
                profile_data['app_preferences'] = app_prefs

            # Update sports profile
            if "favorite_sports" in update_data:
                sports_profile = profile_data.get('sports_profile') or {}
                sports_profile["favorite_sports"] = update_data["favorite_sports"]
                user.profile.sports_profile = sports_profile
                profile_data['sports_profile'] = sports_profile

            # Update completion percentage using captured data (avoid accessing user attributes)
            # Update user_data with any modified user fields
            user_fields = ["email", "username", "full_name", "avatar_url"]
            for field in user_fields:
                if field in update_data:
                    user_data[field] = update_data[field]
                    
            completion_data = {
                'email': user_data.get('email'),
                'username': user_data.get('username'),
                'full_name': user_data.get('full_name'),
                'avatar_url': user_data.get('avatar_url'),
                'profile': profile_data if profile_data else None
            }
            
            completion_percentage = UserProfileService._calculate_completion_percentage_from_data(completion_data)
            user.profile.profile_completion_percentage = completion_percentage

            await db.commit()

            # Log activity - temporarily disabled for debugging
            # await UserProfileService.log_activity(
            #     db,
            #     user_id,
            #     "profile_update",
            #     f"Profile updated: {', '.join(update_data.keys())}",
            # )

            logger.info(f"Updated profile for user {user_id}")
            return user

        except Exception as e:
            logger.error(f"Error updating profile for user {user_id}: {type(e).__name__}: {e}")
            await db.rollback()
            raise Exception(f"Failed to update profile: {type(e).__name__}: {str(e)}")

    @staticmethod
    async def upload_avatar(
        db: AsyncSession, user_id: str, file: UploadFile
    ) -> Optional[str]:
        """Upload and set user avatar"""
        try:
            # Validate file type
            allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
            if file.content_type not in allowed_types:
                raise ValueError(
                    "Invalid file type. Only JPEG, PNG, GIF, and WebP are allowed."
                )

            # Check file size (5MB limit)
            max_size = 5 * 1024 * 1024  # 5MB
            file_content = await file.read()
            if len(file_content) > max_size:
                raise ValueError("File too large. Maximum size is 5MB.")

            # Upload to file storage
            file_service = FileUploadService()
            file_extension = (
                file.filename.split(".")[-1]
                if file.filename and "." in file.filename
                else "jpg"
            )
            avatar_url = await file_service.upload_file(
                file_content=file_content,
                filename=f"avatar_{user_id}_{datetime.now().timestamp()}.{file_extension}",
                content_type=file.content_type,
                folder="avatars",
            )

            # Update user avatar URL
            user_uuid = UUID(user_id)
            await db.execute(
                update(User).where(User.id == user_uuid).values(avatar_url=avatar_url)
            )

            await db.commit()

            # Log activity
            await UserProfileService.log_activity(
                db, user_id, "avatar_update", "Avatar uploaded"
            )

            logger.info(f"Uploaded avatar for user {user_id}")
            return avatar_url

        except ValueError as e:
            # Re-raise ValueError as-is so API can handle it with proper status code
            logger.error(f"Validation error uploading avatar for user {user_id}: {e}")
            await db.rollback()
            raise
        except Exception as e:
            logger.error(f"Error uploading avatar for user {user_id}: {e}")
            await db.rollback()
            raise Exception(f"Failed to upload avatar: {str(e)}")

    @staticmethod
    async def update_privacy_settings(
        db: AsyncSession, user_id: str, privacy_settings: UserPrivacySettings
    ) -> bool:
        """Update user privacy settings"""
        try:
            # Update privacy settings using SQL update
            await db.execute(
                update(UserProfile)
                .where(UserProfile.user_id == user_id)
                .values(privacy_settings=privacy_settings.model_dump())
            )

            await db.commit()

            # Log activity
            await UserProfileService.log_activity(
                db, user_id, "privacy_update", "Privacy settings updated"
            )

            logger.info(f"Updated privacy settings for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error updating privacy settings for user {user_id}: {e}")
            await db.rollback()
            raise Exception(f"Failed to update privacy settings: {str(e)}")

    @staticmethod
    async def update_notification_settings(
        db: AsyncSession, user_id: str, notification_settings: UserNotificationSettings
    ) -> bool:
        """Update user notification settings"""
        try:
            # Update notification settings using SQL update
            await db.execute(
                update(UserProfile)
                .where(UserProfile.user_id == user_id)
                .values(notification_settings=notification_settings.model_dump())
            )

            await db.commit()

            # Log activity
            await UserProfileService.log_activity(
                db, user_id, "notification_update", "Notification settings updated"
            )

            logger.info(f"Updated notification settings for user {user_id}")
            return True

        except Exception as e:
            logger.error(
                f"Error updating notification settings for user {user_id}: {e}"
            )
            await db.rollback()
            raise Exception(f"Failed to update notification settings: {str(e)}")

    @staticmethod
    async def change_password(
        db: AsyncSession,
        user_id: str,
        password_change: UserPasswordChange,
        access_token: str,
    ) -> bool:
        """Change user password"""
        try:
            # Convert user_id to UUID if it's a string
            user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
            
            # Validate new password matches confirmation
            if password_change.new_password != password_change.confirm_password:
                raise ValueError("New password and confirmation do not match")

            # Update password in Supabase
            auth_response = supabase_auth.update_user(
                access_token, {"password": password_change.new_password}
            )

            if not auth_response.get("success"):
                raise Exception("Failed to update password in authentication service")

            # Update security settings
            await db.execute(
                update(UserSecuritySettings)
                .where(UserSecuritySettings.user_id == user_uuid)
                .values(
                    password_last_changed=datetime.utcnow(),
                    failed_login_attempts=0,  # Reset failed attempts
                )
            )

            await db.commit()

            # Log activity
            await UserProfileService.log_activity(
                db, user_id, "password_change", "Password changed successfully"
            )

            logger.info(f"Password changed for user {user_id}")
            return True

        except ValueError as e:
            # Re-raise ValueError as-is so API can handle it with proper status code
            logger.error(f"Validation error changing password for user {user_id}: {e}")
            await db.rollback()
            raise
        except Exception as e:
            logger.error(f"Error changing password for user {user_id}: {e}")
            await db.rollback()
            raise Exception(f"Failed to change password: {str(e)}")

    @staticmethod
    async def get_dashboard_stats(db: AsyncSession, user_id: str) -> UserDashboardStats:
        """Get user dashboard statistics"""
        try:
            # This would be expanded with actual match and team queries
            # For now, returning placeholder data
            stats = UserDashboardStats(
                total_matches=0,
                total_teams=0,
                matches_won=0,
                matches_lost=0,
                current_streak=0,
                skill_rating=None,
            )

            # TODO: Add actual queries for:
            # - Total matches from CricketMatch where user is participant
            # - Total teams from TeamMember where user_id = user_id
            # - Win/loss statistics
            # - Current streak calculation
            # - Skill rating calculation

            return stats

        except Exception as e:
            logger.error(f"Error getting dashboard stats for user {user_id}: {e}")
            raise Exception(f"Failed to get dashboard stats: {str(e)}")

    @staticmethod
    async def log_activity(
        db: AsyncSession,
        user_id: str,
        activity_type: str,
        description: str,
        activity_metadata: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        """Log user activity"""
        try:
            # Convert string UUID to UUID object for database operations
            user_uuid = UUID(user_id)
            activity_log = UserActivityLog(
                user_id=user_uuid,
                activity_type=activity_type,
                description=description,
                activity_metadata=activity_metadata,
                ip_address=ip_address,
                user_agent=user_agent,
            )

            db.add(activity_log)
            await db.commit()

        except Exception as e:
            logger.error(f"Error logging activity for user {user_id}: {e}")
            # Don't raise exception for logging failures

    @staticmethod
    async def get_activity_logs(
        db: AsyncSession,
        user_id: str,
        limit: int = 50,
        activity_type: Optional[str] = None,
    ) -> List[ActivityLogSchema]:
        """Get user activity logs"""
        try:
            # Convert string UUID to UUID object for database query
            user_uuid = UUID(user_id)
            query = select(UserActivityLog).where(UserActivityLog.user_id == user_uuid)

            if activity_type:
                query = query.where(UserActivityLog.activity_type == activity_type)

            query = query.order_by(UserActivityLog.timestamp.desc()).limit(limit)

            result = await db.execute(query)
            logs = result.scalars().all()

            return [ActivityLogSchema.model_validate(log) for log in logs]

        except Exception as e:
            logger.error(f"Error getting activity logs for user {user_id}: {e}")
            raise Exception(f"Failed to get activity logs: {str(e)}")

    @staticmethod
    async def delete_account(db: AsyncSession, user_id: str) -> bool:
        """Soft delete user account (GDPR compliance)"""
        try:
            # Convert string UUID to UUID object for database query
            user_uuid = UUID(user_id)
            # Soft delete user
            await db.execute(
                update(User)
                .where(User.id == user_uuid)
                .values(
                    is_active=False,
                    email=f"deleted_{user_id}@deleted.com",
                    username=f"deleted_{user_id}",
                )
            )

            # Log activity
            await UserProfileService.log_activity(
                db, user_id, "account_deleted", "Account deleted by user"
            )

            await db.commit()

            logger.info(f"Soft deleted account for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting account for user {user_id}: {e}")
            await db.rollback()
            raise Exception(f"Failed to delete account: {str(e)}")

    @staticmethod
    async def _calculate_completion_percentage(user: User) -> float:
        """Calculate profile completion percentage"""
        total_fields = 15  # Total number of profile fields
        completed_fields = 0

        # Basic fields (5 fields)
        if user.email is not None and user.email.strip():
            completed_fields += 1
        if user.username is not None and user.username.strip():
            completed_fields += 1
        if user.full_name is not None and user.full_name.strip():
            completed_fields += 1
        if user.avatar_url is not None and user.avatar_url.strip():
            completed_fields += 1

        if user.profile:
            # Profile fields (10 fields)
            if (
                user.profile.display_name is not None
                and user.profile.display_name.strip()
            ):
                completed_fields += 1
            if user.profile.bio is not None and user.profile.bio.strip():
                completed_fields += 1
            if user.profile.location is not None and user.profile.location.strip():
                completed_fields += 1
            if user.profile.birth_date is not None:
                completed_fields += 1
            if (
                user.profile.phone_number is not None
                and user.profile.phone_number.strip()
            ):
                completed_fields += 1

            # Sports profile
            sports_profile = user.profile.sports_profile or {}
            if sports_profile.get("favorite_sports"):
                completed_fields += 1
            if sports_profile.get("playing_position"):
                completed_fields += 1
            if sports_profile.get("skill_level"):
                completed_fields += 1

            # Privacy and notification settings
            if user.profile.privacy_settings:
                completed_fields += 1
            if user.profile.notification_settings:
                completed_fields += 1

        return (completed_fields / total_fields) * 100.0

    @staticmethod
    def _calculate_completion_percentage_from_data(completion_data: dict) -> float:
        """Calculate profile completion percentage from captured data"""
        total_fields = 15  # Total number of profile fields
        completed_fields = 0

        # Basic fields (5 fields)
        if completion_data.get('email') and completion_data['email'].strip():
            completed_fields += 1
        if completion_data.get('username') and completion_data['username'].strip():
            completed_fields += 1
        if completion_data.get('full_name') and completion_data['full_name'].strip():
            completed_fields += 1
        if completion_data.get('avatar_url') and completion_data['avatar_url'].strip():
            completed_fields += 1

        profile_data = completion_data.get('profile')
        if profile_data:
            # Profile fields (10 fields)
            if profile_data.get('display_name') and profile_data['display_name'].strip():
                completed_fields += 1
            if profile_data.get('bio') and profile_data['bio'].strip():
                completed_fields += 1
            if profile_data.get('location') and profile_data['location'].strip():
                completed_fields += 1
            if profile_data.get('birth_date') is not None:
                completed_fields += 1
            if profile_data.get('phone_number') and profile_data['phone_number'].strip():
                completed_fields += 1

            # Sports profile
            sports_profile = profile_data.get('sports_profile') or {}
            if sports_profile.get("favorite_sports"):
                completed_fields += 1
            if sports_profile.get("playing_position"):
                completed_fields += 1
            if sports_profile.get("skill_level"):
                completed_fields += 1

            # Privacy and notification settings
            if profile_data.get('privacy_settings'):
                completed_fields += 1
            if profile_data.get('notification_settings'):
                completed_fields += 1

        return (completed_fields / total_fields) * 100.0
