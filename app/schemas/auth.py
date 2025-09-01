"""
Authentication schemas for user registration, login, and token responses
"""
from typing import Optional, Dict, Any
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


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=6, max_length=100)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=6, max_length=100)


class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None


class VerifyEmailRequest(BaseModel):
    verification_code: str


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class AuthResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
