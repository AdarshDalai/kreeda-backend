from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any, Literal
from datetime import datetime
import uuid


# Authentication Schemas
class UserRegister(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=20, pattern="^[a-zA-Z0-9_]+$")
    full_name: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class GoogleLogin(BaseModel):
    token: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenData(BaseModel):
    user_id: Optional[str] = None
    supabase_id: Optional[str] = None


class PasswordResetRequest(BaseModel):
    email: EmailStr
    redirect_to: Optional[str] = None


class OTPVerification(BaseModel):
    email: EmailStr
    token: str
    type: Literal[
        "signup",
        "invite",
        "magiclink",
        "recovery",
        "email_change_current",
        "email_change_new",
        "phone_change",
    ] = "signup"


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8)
    phone: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class OAuthProvider(BaseModel):
    provider: Literal[
        "google",
        "github",
        "discord",
        "facebook",
        "apple",
        "azure",
        "bitbucket",
        "gitlab",
        "linkedin",
        "spotify",
        "twitch",
        "twitter",
    ]
    redirect_to: Optional[str] = None


# Supabase User Response Models
class SupabaseUserMetadata(BaseModel):
    username: Optional[str] = None
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None


class SupabaseUser(BaseModel):
    id: str
    email: Optional[str] = None
    phone: Optional[str] = None
    email_confirmed_at: Optional[datetime] = None
    phone_confirmed_at: Optional[datetime] = None
    user_metadata: Optional[Dict[str, Any]] = None
    app_metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_sign_in_at: Optional[datetime] = None


class SupabaseSession(BaseModel):
    access_token: str
    refresh_token: str
    expires_at: int
    token_type: str = "bearer"


class AuthResponse(BaseModel):
    user: SupabaseUser
    session: Optional[SupabaseSession] = None


class OAuthResponse(BaseModel):
    url: str
