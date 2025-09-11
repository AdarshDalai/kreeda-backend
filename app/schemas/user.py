from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime
import uuid


class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=20)
    full_name: str = Field(..., min_length=1, max_length=100)


class UserCreate(UserBase):
    supabase_id: str
    avatar_url: Optional[str] = None


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=20)
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    avatar_url: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8)
    phone: Optional[str] = None


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    avatar_url: Optional[str] = None
    created_at: datetime
    is_active: bool


class UserSearch(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    username: str
    full_name: str
    avatar_url: Optional[str] = None
