from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, update, delete
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime, timedelta
import json
from fastapi import UploadFile

from app.models.user import User
from app.models.user_profile import (
    UserProfile, UserSecuritySettings, UserActivityLog, 
    UserSession, UserAchievement
)
from app.schemas.user_profile import (
    UserProfileUpdate, UserPasswordChange, UserPrivacySettings,
    UserNotificationSettings, UserPreferencesSettings, UserSportsProfile,
    UserProfileResponse, UserDashboardStats, UserActivityLog as ActivityLogSchema
)
from app.utils.file_upload import FileUploadService
from app.auth import supabase_auth

logger = logging.getLogger(__name__)


class UserProfileService:
    """Comprehensive user profile management service"""
    
    @staticmethod
    async def get_complete_profile(db: AsyncSession, user_id: str) -> Optional[UserProfileResponse]:
        """Get complete user profile with all settings"""
        try:
            result = await db.execute(
                select(User)
                .options(
                    selectinload(User.profile),
                    selectinload(User.security_settings)
                )
                .where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                return None
            
            # Get or create profile if it doesn't exist
            if not user.profile:
                await UserProfileService.create_default_profile(db, user_id)
                # Refresh to get the new profile
                await db.refresh(user)
            
            return UserProfileResponse(
                id=user.id,
                email=user.email,
                username=user.username,
                full_name=user.full_name,
                display_name=user.profile.display_name if user.profile else None,
                avatar_url=user.avatar_url,
                bio=user.profile.bio if user.profile else None,
                location=user.profile.location if user.profile else None,
                website=user.profile.website if user.profile else None,
                birth_date=user.profile.birth_date if user.profile else None,
                created_at=user.created_at,
                updated_at=user.updated_at,
                is_active=user.is_active,
                last_login=user.profile.last_login if user.profile else None,
                profile_settings=user.profile.app_preferences if user.profile else None,
                privacy_settings=user.profile.privacy_settings if user.profile else None,
                notification_settings=user.profile.notification_settings if user.profile else None,
                sports_profile=user.profile.sports_profile if user.profile else None
            )
            
        except Exception as e:
            logger.error(f"Error getting complete profile for user {user_id}: {e}")
            raise Exception(f"Failed to get profile: {str(e)}")
    
    @staticmethod
    async def create_default_profile(db: AsyncSession, user_id: str) -> UserProfile:
        """Create default profile for new user"""
        try:
            profile = UserProfile(
                user_id=user_id,
                profile_completion_percentage=30.0  # Basic info completed
            )
            
            db.add(profile)
            await db.commit()
            await db.refresh(profile)
            
            # Create default security settings
            security_settings = UserSecuritySettings(user_id=user_id)
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
        db: AsyncSession, 
        user_id: str, 
        profile_update: UserProfileUpdate
    ) -> Optional[User]:
        """Update user profile information"""
        try:
            # Get user and profile
            result = await db.execute(
                select(User)
                .options(selectinload(User.profile))
                .where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                return None
            
            # Update user basic fields
            update_data = profile_update.model_dump(exclude_unset=True)
            
            # Update User model fields
            user_fields = ['email', 'username', 'full_name', 'avatar_url']
            for field in user_fields:
                if field in update_data:
                    setattr(user, field, update_data[field])
            
            # Get or create profile
            if not user.profile:
                await UserProfileService.create_default_profile(db, user_id)
                await db.refresh(user)
            
            # Update profile fields
            profile_fields = [
                'display_name', 'bio', 'location', 'website', 
                'birth_date', 'phone_number'
            ]
            
            for field in profile_fields:
                if field in update_data:
                    setattr(user.profile, field, update_data[field])
            
            # Update privacy settings
            if 'profile_visibility' in update_data or 'email_visibility' in update_data or 'show_online_status' in update_data:
                privacy_settings = user.profile.privacy_settings or {}
                for key in ['profile_visibility', 'email_visibility', 'show_online_status']:
                    if key in update_data:
                        privacy_settings[key] = update_data[key]
                user.profile.privacy_settings = privacy_settings
            
            # Update app preferences
            if any(key in update_data for key in ['preferred_theme', 'preferred_language', 'timezone']):
                app_prefs = user.profile.app_preferences or {}
                for key in ['preferred_theme', 'preferred_language', 'timezone']:
                    if key in update_data:
                        app_prefs[key] = update_data[key]
                user.profile.app_preferences = app_prefs
            
            # Update sports profile
            if 'favorite_sports' in update_data:
                sports_profile = user.profile.sports_profile or {}
                sports_profile['favorite_sports'] = update_data['favorite_sports']
                user.profile.sports_profile = sports_profile
            
            # Update completion percentage
            user.profile.profile_completion_percentage = await UserProfileService._calculate_completion_percentage(user)
            
            await db.commit()
            await db.refresh(user)
            
            # Log activity
            await UserProfileService.log_activity(
                db, user_id, "profile_update", 
                f"Profile updated: {', '.join(update_data.keys())}"
            )
            
            logger.info(f"Updated profile for user {user_id}")
            return user
            
        except Exception as e:
            logger.error(f"Error updating profile for user {user_id}: {e}")
            await db.rollback()
            raise Exception(f"Failed to update profile: {str(e)}")
    
    @staticmethod
    async def upload_avatar(
        db: AsyncSession, 
        user_id: str, 
        file: UploadFile
    ) -> Optional[str]:
        """Upload and set user avatar"""
        try:
            # Validate file type
            allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
            if file.content_type not in allowed_types:
                raise ValueError("Invalid file type. Only JPEG, PNG, GIF, and WebP are allowed.")
            
            # Check file size (5MB limit)
            max_size = 5 * 1024 * 1024  # 5MB
            file_content = await file.read()
            if len(file_content) > max_size:
                raise ValueError("File too large. Maximum size is 5MB.")
            
            # Upload to file storage
            file_service = FileUploadService()
            file_extension = file.filename.split('.')[-1] if file.filename and '.' in file.filename else 'jpg'
            avatar_url = await file_service.upload_file(
                file_content=file_content,
                filename=f"avatar_{user_id}_{datetime.now().timestamp()}.{file_extension}",
                content_type=file.content_type,
                folder="avatars"
            )
            
            # Update user avatar URL
            await db.execute(
                update(User)
                .where(User.id == user_id)
                .values(avatar_url=avatar_url)
            )
            
            await db.commit()
            
            # Log activity
            await UserProfileService.log_activity(
                db, user_id, "avatar_update", "Avatar uploaded"
            )
            
            logger.info(f"Uploaded avatar for user {user_id}")
            return avatar_url
            
        except Exception as e:
            logger.error(f"Error uploading avatar for user {user_id}: {e}")
            await db.rollback()
            raise Exception(f"Failed to upload avatar: {str(e)}")
    
    @staticmethod
    async def update_privacy_settings(
        db: AsyncSession, 
        user_id: str, 
        privacy_settings: UserPrivacySettings
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
        db: AsyncSession, 
        user_id: str, 
        notification_settings: UserNotificationSettings
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
            logger.error(f"Error updating notification settings for user {user_id}: {e}")
            await db.rollback()
            raise Exception(f"Failed to update notification settings: {str(e)}")
    
    @staticmethod
    async def change_password(
        db: AsyncSession, 
        user_id: str, 
        password_change: UserPasswordChange,
        access_token: str
    ) -> bool:
        """Change user password"""
        try:
            # Validate new password matches confirmation
            if password_change.new_password != password_change.confirm_password:
                raise ValueError("New password and confirmation do not match")
            
            # Update password in Supabase
            auth_response = supabase_auth.update_user(
                access_token, 
                {"password": password_change.new_password}
            )
            
            if not auth_response.get("success"):
                raise Exception("Failed to update password in authentication service")
            
            # Update security settings
            await db.execute(
                update(UserSecuritySettings)
                .where(UserSecuritySettings.user_id == user_id)
                .values(
                    password_last_changed=datetime.utcnow(),
                    failed_login_attempts=0  # Reset failed attempts
                )
            )
            
            await db.commit()
            
            # Log activity
            await UserProfileService.log_activity(
                db, user_id, "password_change", "Password changed successfully"
            )
            
            logger.info(f"Password changed for user {user_id}")
            return True
            
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
                skill_rating=None
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
        user_agent: Optional[str] = None
    ) -> None:
        """Log user activity"""
        try:
            activity_log = UserActivityLog(
                user_id=user_id,
                activity_type=activity_type,
                description=description,
                activity_metadata=activity_metadata,
                ip_address=ip_address,
                user_agent=user_agent
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
        activity_type: Optional[str] = None
    ) -> List[ActivityLogSchema]:
        """Get user activity logs"""
        try:
            query = select(UserActivityLog).where(UserActivityLog.user_id == user_id)
            
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
            # Soft delete user
            await db.execute(
                update(User)
                .where(User.id == user_id)
                .values(
                    is_active=False,
                    email=f"deleted_{user_id}@deleted.com",
                    username=f"deleted_{user_id}"
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
        if user.email is not None and user.email.strip(): completed_fields += 1
        if user.username is not None and user.username.strip(): completed_fields += 1
        if user.full_name is not None and user.full_name.strip(): completed_fields += 1
        if user.avatar_url is not None and user.avatar_url.strip(): completed_fields += 1
        
        if user.profile:
            # Profile fields (10 fields)
            if user.profile.display_name is not None and user.profile.display_name.strip(): completed_fields += 1
            if user.profile.bio is not None and user.profile.bio.strip(): completed_fields += 1
            if user.profile.location is not None and user.profile.location.strip(): completed_fields += 1
            if user.profile.birth_date is not None: completed_fields += 1
            if user.profile.phone_number is not None and user.profile.phone_number.strip(): completed_fields += 1
            
            # Sports profile
            sports_profile = user.profile.sports_profile or {}
            if sports_profile.get('favorite_sports'): completed_fields += 1
            if sports_profile.get('playing_position'): completed_fields += 1
            if sports_profile.get('skill_level'): completed_fields += 1
            
            # Privacy and notification settings
            if user.profile.privacy_settings: completed_fields += 1
            if user.profile.notification_settings: completed_fields += 1
        
        return (completed_fields / total_fields) * 100.0
