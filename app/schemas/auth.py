"""
Authentication schemas for user registration, login, and token responses
"""
from typing import Optional
from pydantic import BaseModel, Field, EmailStr


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)
    full_name: Optional[str] = Field(None, max_length=100)


class UserLogin(BaseModel):
    username: str = Field(..., min_length=3, max_length=50) 
    password: str = Field(..., min_length=1, max_length=100)


class UserResponse(BaseModel):
    id: str  # Changed from int to str to support UUID
    username: str
    email: str
    full_name: Optional[str]
    is_active: bool = True  # Default value
    created_at: str  # Add created_at field
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class TokenData(BaseModel):
    username: Optional[str] = None
