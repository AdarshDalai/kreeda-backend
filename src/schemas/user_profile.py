from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
from datetime import datetime, date
from uuid import UUID

# User Profile Request schemas
class UserProfileCreateRequest(BaseModel):
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    location: Optional[str] = None
    date_of_birth: Optional[date] = None
    bio: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None
    roles: Optional[Dict[str, Any]] = None

class UserProfileUpdateRequest(BaseModel):
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    location: Optional[str] = None
    date_of_birth: Optional[date] = None
    bio: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None
    roles: Optional[Dict[str, Any]] = None

# User Profile Response schemas
class UserProfileResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: Optional[str]
    avatar_url: Optional[str]
    location: Optional[str]
    date_of_birth: Optional[date]
    bio: Optional[str]
    preferences: Optional[Dict[str, Any]]
    roles: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True