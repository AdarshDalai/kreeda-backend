import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class NotificationPreference(str, Enum):
    ALL = "all"
    IMPORTANT = "important"
    NONE = "none"


class PrivacyLevel(str, Enum):
    PUBLIC = "public"
    FRIENDS = "friends"
    PRIVATE = "private"


class Theme(str, Enum):
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"


class Language(str, Enum):
    EN = "en"
    ES = "es"
    FR = "fr"
    DE = "de"
    HI = "hi"


# Enhanced User Profile Schemas
class UserProfileSettings(BaseModel):
    """Comprehensive user profile settings"""

    # Basic Profile Information
    display_name: Optional[str] = Field(
        None, max_length=50, description="Public display name"
    )
    bio: Optional[str] = Field(None, max_length=500, description="User biography")
    location: Optional[str] = Field(None, max_length=100, description="User location")
    website: Optional[str] = Field(None, description="Personal website URL")
    birth_date: Optional[datetime] = Field(None, description="Date of birth")

    # Contact Information
    phone_number: Optional[str] = Field(None, description="Phone number")
    emergency_contact: Optional[str] = Field(None, description="Emergency contact")

    # Privacy Settings
    profile_visibility: PrivacyLevel = Field(
        PrivacyLevel.PUBLIC, description="Profile visibility level"
    )
    email_visibility: PrivacyLevel = Field(
        PrivacyLevel.PRIVATE, description="Email visibility"
    )
    show_online_status: bool = Field(True, description="Show online status to others")
    allow_friend_requests: bool = Field(True, description="Allow friend requests")

    # Notification Preferences
    email_notifications: NotificationPreference = Field(
        NotificationPreference.IMPORTANT, description="Email notification level"
    )
    push_notifications: NotificationPreference = Field(
        NotificationPreference.ALL, description="Push notification level"
    )
    match_notifications: bool = Field(
        True, description="Notifications for match updates"
    )
    team_notifications: bool = Field(
        True, description="Notifications for team activities"
    )

    # App Preferences
    preferred_theme: Theme = Field(Theme.AUTO, description="UI theme preference")
    preferred_language: Language = Field(Language.EN, description="Language preference")
    timezone: Optional[str] = Field(None, description="User timezone")

    # Sports Preferences
    favorite_sports: List[str] = Field(
        default_factory=list, description="List of favorite sports"
    )
    playing_position: Optional[str] = Field(
        None, description="Primary playing position"
    )
    skill_level: Optional[str] = Field(None, description="Self-assessed skill level")


class UserSecuritySettings(BaseModel):
    """User security and authentication settings"""

    two_factor_enabled: bool = Field(
        False, description="Two-factor authentication status"
    )
    email_verification_required: bool = Field(
        True, description="Require email verification"
    )
    login_notifications: bool = Field(True, description="Notify on new login")
    active_sessions_limit: int = Field(
        5, ge=1, le=10, description="Maximum active sessions"
    )
    password_last_changed: Optional[datetime] = Field(
        None, description="Last password change date"
    )


class UserAvatarUpdate(BaseModel):
    """Schema for avatar upload"""

    avatar_file: bytes = Field(..., description="Avatar image data")
    filename: str = Field(..., description="Original filename")
    content_type: str = Field(..., description="MIME type of the image")


class UserProfileUpdate(BaseModel):
    """Schema for updating user profile"""

    # Basic fields (from existing UserUpdate)
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=20)
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    avatar_url: Optional[str] = None

    # Enhanced profile fields
    display_name: Optional[str] = Field(None, max_length=50)
    bio: Optional[str] = Field(None, max_length=500)
    location: Optional[str] = Field(None, max_length=100)
    website: Optional[str] = None
    birth_date: Optional[datetime] = None
    phone_number: Optional[str] = None

    # Privacy settings
    profile_visibility: Optional[PrivacyLevel] = None
    email_visibility: Optional[PrivacyLevel] = None
    show_online_status: Optional[bool] = None

    # Preferences
    preferred_theme: Optional[Theme] = None
    preferred_language: Optional[Language] = None
    timezone: Optional[str] = None
    favorite_sports: Optional[List[str]] = None


class UserPasswordChange(BaseModel):
    """Schema for password change"""

    current_password: str = Field(..., min_length=8, description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")
    confirm_password: str = Field(..., min_length=8, description="Confirm new password")


class UserPrivacySettings(BaseModel):
    """Privacy settings schema"""

    profile_visibility: PrivacyLevel
    email_visibility: PrivacyLevel
    show_online_status: bool
    allow_friend_requests: bool
    search_visibility: bool = Field(
        True, description="Allow profile to appear in search results"
    )


class UserNotificationSettings(BaseModel):
    """Notification settings schema"""

    email_notifications: NotificationPreference
    push_notifications: NotificationPreference
    match_notifications: bool
    team_notifications: bool
    message_notifications: bool = Field(
        True, description="Direct message notifications"
    )
    marketing_emails: bool = Field(False, description="Marketing email preferences")


class UserPreferencesSettings(BaseModel):
    """User app preferences"""

    preferred_theme: Theme
    preferred_language: Language
    timezone: Optional[str]
    date_format: str = Field("DD/MM/YYYY", description="Preferred date format")
    time_format: str = Field("24h", description="12h or 24h time format")
    auto_save: bool = Field(True, description="Auto-save preferences")


class UserSportsProfile(BaseModel):
    """Sports-specific profile information"""

    favorite_sports: List[str]
    playing_position: Optional[str]
    skill_level: Optional[str]
    years_playing: Optional[int] = Field(None, ge=0, le=50)
    achievements: List[str] = Field(default_factory=list)
    preferred_role: Optional[str] = None  # Captain, Player, Coach, etc.


class UserProfileResponse(BaseModel):
    """Complete user profile response"""

    model_config = ConfigDict(from_attributes=True)

    # Basic info
    id: uuid.UUID
    email: EmailStr
    username: str
    full_name: str
    display_name: Optional[str]
    avatar_url: Optional[str]

    # Profile details
    bio: Optional[str]
    location: Optional[str]
    website: Optional[str]
    birth_date: Optional[datetime]

    # System fields
    created_at: datetime
    updated_at: datetime
    is_active: bool
    last_login: Optional[datetime] = None

    # Settings
    profile_settings: Optional[UserProfileSettings] = None
    privacy_settings: Optional[UserPrivacySettings] = None
    notification_settings: Optional[UserNotificationSettings] = None
    sports_profile: Optional[UserSportsProfile] = None


class UserDashboardStats(BaseModel):
    """User dashboard statistics"""

    total_matches: int = 0
    total_teams: int = 0
    matches_won: int = 0
    matches_lost: int = 0
    current_streak: int = 0
    favorite_position: Optional[str] = None
    skill_rating: Optional[float] = None


class UserActivityLog(BaseModel):
    """User activity tracking"""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    activity_type: str  # login, profile_update, match_join, etc.
    description: str
    ip_address: Optional[str]
    user_agent: Optional[str]
    timestamp: datetime


class UserExportData(BaseModel):
    """Schema for user data export (GDPR compliance)"""

    profile_data: UserProfileResponse
    activity_logs: List[UserActivityLog]
    team_memberships: List[Dict[str, Any]]
    match_history: List[Dict[str, Any]]
    uploaded_files: List[str]
    export_date: datetime
