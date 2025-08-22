"""
User Profile and Management Schemas

Extended schemas for user profile management, public profiles,
admin operations, and user discovery features.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, validator, Field, constr
from datetime import datetime
from enum import Enum
from uuid import UUID

from app.schemas.auth import UserRole, AuthProvider


class UserPrivacySettings(BaseModel):
    """User privacy settings."""
    show_email: bool = False
    show_phone: bool = False
    show_real_name: bool = True
    show_last_seen: bool = False
    allow_direct_messages: bool = True
    show_activity: bool = False


class UserProfileStats(BaseModel):
    """User profile statistics."""
    teams_count: int = 0
    tournaments_count: int = 0
    matches_played: int = 0
    matches_won: int = 0
    total_score: int = 0
    win_rate: float = 0.0
    last_activity: Optional[datetime] = None


class PublicUserProfile(BaseModel):
    """Public user profile (limited information)."""
    id: UUID
    username: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    role: UserRole
    created_at: datetime
    last_login: Optional[datetime] = None
    stats: Optional[UserProfileStats] = None
    
    # Privacy-controlled fields (only shown if user allows)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    
    model_config = {"from_attributes": True}


class DetailedUserProfile(BaseModel):
    """Detailed user profile (for profile owner or admin)."""
    id: UUID
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    role: UserRole
    is_active: bool
    email_verified: bool
    auth_provider: AuthProvider
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
    privacy_settings: Optional[UserPrivacySettings] = None
    stats: Optional[UserProfileStats] = None
    
    model_config = {"from_attributes": True}


class UserSearchFilters(BaseModel):
    """Filters for user search."""
    query: Optional[str] = Field(None, description="Search in username, full name, or email")
    role: Optional[Any] = None  # Can be either model or schema UserRole
    is_active: Optional[bool] = None
    email_verified: Optional[bool] = None
    auth_provider: Optional[AuthProvider] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    last_login_after: Optional[datetime] = None
    last_login_before: Optional[datetime] = None


class UserSearchResult(BaseModel):
    """User search result item."""
    id: UUID
    username: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    role: UserRole
    is_active: bool
    email_verified: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    
    model_config = {"from_attributes": True}


class PaginatedUsersResponse(BaseModel):
    """Paginated users response."""
    users: List[UserSearchResult]
    total: int
    page: int
    size: int
    pages: int
    has_next: bool
    has_prev: bool


class AdminUserUpdate(BaseModel):
    """Admin-level user update schema."""
    full_name: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    email_verified: Optional[bool] = None
    failed_login_attempts: Optional[int] = None
    locked_until: Optional[datetime] = None
    
    @validator('phone', pre=True)
    def validate_phone(cls, v):
        if v and not v.startswith('+'):
            return f'+91{v}' if v.startswith(('6', '7', '8', '9')) else v
        return v


class UserActivityLog(BaseModel):
    """User activity log entry."""
    id: str
    user_id: UUID
    action: str
    description: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime
    
    model_config = {"from_attributes": True}


class UserActivityResponse(BaseModel):
    """User activity response."""
    activities: List[UserActivityLog]
    total: int
    page: int
    size: int


class UserBulkAction(str, Enum):
    """Bulk actions for users."""
    ACTIVATE = "activate"
    DEACTIVATE = "deactivate"
    VERIFY_EMAIL = "verify_email"
    RESET_FAILED_ATTEMPTS = "reset_failed_attempts"
    DELETE = "delete"


class BulkUserActionRequest(BaseModel):
    """Bulk user action request."""
    user_ids: List[UUID] = Field(..., min_length=1, max_length=100)
    action: UserBulkAction
    reason: Optional[str] = None


class BulkActionResult(BaseModel):
    """Result of bulk action."""
    success_count: int
    failed_count: int
    failed_users: List[Dict[str, str]]  # user_id -> error_message
    message: str


class UserExportRequest(BaseModel):
    """User data export request."""
    filters: Optional[UserSearchFilters] = None
    fields: Optional[List[str]] = None  # Specific fields to export
    format: str = "csv"
    
    @validator('format')
    def validate_format(cls, v):
        if v not in ['csv', 'json', 'xlsx']:
            raise ValueError('Format must be one of: csv, json, xlsx')
        return v


class UserImportRequest(BaseModel):
    """User data import request."""
    users: List[Dict[str, Any]]
    update_existing: bool = False
    send_welcome_email: bool = False


class UserPreferences(BaseModel):
    """User application preferences."""
    theme: str = "light"
    language: str = "en"
    timezone: str = "UTC"
    notifications_email: bool = True
    notifications_push: bool = True
    notifications_sms: bool = False
    auto_join_tournaments: bool = False
    privacy_settings: Optional[UserPrivacySettings] = None


class UpdateUserPreferencesRequest(BaseModel):
    """Update user preferences request."""
    theme: Optional[str] = None
    language: Optional[str] = None
    timezone: Optional[str] = None
    notifications_email: Optional[bool] = None
    notifications_push: Optional[bool] = None
    notifications_sms: Optional[bool] = None
    auto_join_tournaments: Optional[bool] = None
    privacy_settings: Optional[UserPrivacySettings] = None
