from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

# Request schemas
class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str
    phone_number: Optional[str] = None
    data: Optional[Dict[str, Any]] = None  # User metadata

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserAnonymousRequest(BaseModel):
    options: Optional[Dict[str, Any]] = None

class UserOTPRequest(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    options: Optional[Dict[str, Any]] = None

class UserOTPVerifyRequest(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    token: str
    type: str  # 'email', 'sms', 'phone_change', etc.

class UserUpdateRequest(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    phone: Optional[str] = None
    data: Optional[Dict[str, Any]] = None  # User metadata

class PasswordResetRequest(BaseModel):
    email: EmailStr
    options: Optional[Dict[str, Any]] = None

class RefreshTokenRequest(BaseModel):
    refresh_token: str

# Response schemas mimicking Supabase
class UserIdentity(BaseModel):
    id: str
    user_id: str
    identity_data: Dict[str, Any]
    provider: str
    created_at: datetime
    last_sign_in_at: datetime
    updated_at: datetime

class UserMetadata(BaseModel):
    provider: str
    providers: List[str]

class UserResponse(BaseModel):
    id: UUID
    app_metadata: UserMetadata
    user_metadata: Dict[str, Any] = {}
    aud: str = "authenticated"
    confirmation_sent_at: Optional[datetime] = None
    recovery_sent_at: Optional[datetime] = None
    email_change_sent_at: Optional[datetime] = None
    new_email: Optional[EmailStr] = None
    invited_at: Optional[datetime] = None
    action_link: Optional[str] = None
    email: EmailStr
    phone: str = ""
    created_at: datetime
    confirmed_at: Optional[datetime] = None
    email_confirmed_at: Optional[datetime] = None
    phone_confirmed_at: Optional[datetime] = None
    last_sign_in_at: Optional[datetime] = None
    role: str = "authenticated"
    updated_at: datetime
    identities: List[UserIdentity]
    factors: Optional[List[Any]] = None

class SessionResponse(BaseModel):
    provider_token: Optional[str] = None
    provider_refresh_token: Optional[str] = None
    access_token: str
    refresh_token: str
    expires_in: int
    expires_at: int
    token_type: str = "bearer"
    user: UserResponse

class AuthResponse(BaseModel):
    user: UserResponse
    session: SessionResponse