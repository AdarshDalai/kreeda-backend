"""
User Management Schemas

Pydantic models for user management API serialization
"""

from datetime import datetime, date
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr, ConfigDict


# Base schemas
class BaseSchema(BaseModel):
    """Base schema with common configuration"""
    model_config = ConfigDict(from_attributes=True)


# User schemas
class UserBase(BaseSchema):
    """Base user schema"""
    email: EmailStr = Field(..., description="User email address")
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")


class UserCreate(UserBase):
    """Schema for creating a user"""
    full_name: Optional[str] = Field(None, max_length=255, description="User's full name")
    bio: Optional[str] = Field(None, description="User biography")
    location: Optional[str] = Field(None, max_length=255, description="User location")
    date_of_birth: Optional[date] = Field(None, description="Date of birth")
    phone_number: Optional[str] = Field(None, max_length=20, description="Phone number")


class UserUpdate(BaseSchema):
    """Schema for updating a user"""
    email: Optional[EmailStr] = Field(None, description="User email address")
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="Unique username")
    full_name: Optional[str] = Field(None, max_length=255, description="User's full name")
    bio: Optional[str] = Field(None, description="User biography")
    location: Optional[str] = Field(None, max_length=255, description="User location")
    date_of_birth: Optional[date] = Field(None, description="Date of birth")
    phone_number: Optional[str] = Field(None, max_length=20, description="Phone number")
    avatar_url: Optional[str] = Field(None, description="Avatar image URL")
    preferences: Optional[Dict[str, Any]] = Field(None, description="User preferences")


class UserProfile(BaseSchema):
    """User profile schema"""
    user_id: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    date_of_birth: Optional[date] = None
    phone_number: Optional[str] = None
    emergency_contact: Optional[Dict[str, Any]] = None
    preferences: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class User(UserBase):
    """Complete user schema"""
    id: str
    is_active: bool
    is_verified: bool
    last_login: Optional[datetime] = None
    supabase_user_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    profile: Optional[UserProfile] = None


class UserSummary(BaseSchema):
    """User summary for listings"""
    id: str
    username: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: bool


# Sport Profile schemas
class SportProfileBase(BaseSchema):
    """Base sport profile schema"""
    sport_type: str = Field(..., max_length=50, description="Type of sport")
    skill_level: str = Field(default="BEGINNER", description="Skill level")
    primary_position: Optional[str] = Field(None, max_length=50, description="Primary playing position")
    secondary_positions: Optional[List[str]] = Field(None, description="Secondary positions")
    playing_style: Optional[str] = Field(None, max_length=100, description="Playing style")


class SportProfileCreate(SportProfileBase):
    """Schema for creating a sport profile"""
    achievements: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="Achievements")


class SportProfileUpdate(BaseSchema):
    """Schema for updating a sport profile"""
    skill_level: Optional[str] = Field(None, description="Skill level")
    primary_position: Optional[str] = Field(None, max_length=50, description="Primary playing position")
    secondary_positions: Optional[List[str]] = Field(None, description="Secondary positions")
    playing_style: Optional[str] = Field(None, max_length=100, description="Playing style")
    achievements: Optional[List[Dict[str, Any]]] = Field(None, description="Achievements")
    is_active: Optional[bool] = Field(None, description="Active status")


class SportProfile(SportProfileBase):
    """Complete sport profile schema"""
    id: str
    user_id: str
    career_stats: Dict[str, Any] = Field(default_factory=dict)
    achievements: List[Dict[str, Any]] = Field(default_factory=list)
    is_active: bool
    created_at: datetime
    updated_at: datetime


# API Response schemas
class PaginatedResponse(BaseSchema):
    """Paginated response wrapper"""
    total: int
    page: int
    per_page: int
    pages: int


class UserListResponse(PaginatedResponse):
    """Paginated user list response"""
    items: List[UserSummary]


class UserWithProfile(User):
    """User with profile information"""
    sport_profiles: List[SportProfile] = Field(default_factory=list)