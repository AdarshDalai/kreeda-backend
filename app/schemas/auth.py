from typing import Optional, List
from pydantic import BaseModel, EmailStr, validator, ConfigDict
from datetime import datetime
from enum import Enum
from uuid import UUID


class AuthProvider(str, Enum):
    """Authentication providers supported by Kreeda."""
    EMAIL = "email"
    GOOGLE = "google"
    APPLE = "apple"


class UserRole(str, Enum):
    """User roles in the system."""
    PLAYER = "player"
    SCOREKEEPER = "scorekeeper"
    ORGANIZER = "organizer"
    SPECTATOR = "spectator"
    ADMIN = "admin"


# Base schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    role: UserRole = UserRole.PLAYER
    is_active: bool = True

    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters long')
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username can only contain letters, numbers, hyphens and underscores')
        return v.lower()

    @validator('phone', pre=True)
    def validate_phone(cls, v):
        if v and not v.startswith('+'):
            return f'+91{v}' if v.startswith(('6', '7', '8', '9')) else v
        return v


class UserCreate(UserBase):
    password: Optional[str] = None
    auth_provider: AuthProvider = AuthProvider.EMAIL
    provider_id: Optional[str] = None

    @validator('password')
    def validate_password(cls, v, values):
        if values.get('auth_provider') == AuthProvider.EMAIL and not v:
            raise ValueError('Password is required for email authentication')
        if v and len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserInDB(UserBase):
    id: str
    hashed_password: Optional[str] = None
    auth_provider: AuthProvider
    provider_id: Optional[str] = None
    email_verified: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    username: str
    full_name: Optional[str]
    phone: Optional[str]
    avatar_url: Optional[str]
    role: UserRole
    is_active: bool
    auth_provider: AuthProvider
    email_verified: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
    
    @validator('id', pre=True)
    def convert_id(cls, v):
        if isinstance(v, bytes):
            return UUID(v.decode('utf-8'))
        return v
    
    @validator('email', pre=True)
    def convert_email(cls, v):
        if isinstance(v, bytes):
            return v.decode('utf-8')
        return str(v)
    
    @validator('username', pre=True)
    def convert_username(cls, v):
        if isinstance(v, bytes):
            return v.decode('utf-8')
        return str(v)
    
    @validator('role', pre=True)
    def convert_role(cls, v):
        if isinstance(v, bytes):
            v = v.decode('utf-8')
        return UserRole(v) if isinstance(v, str) else v
    
    @validator('auth_provider', pre=True)
    def convert_auth_provider(cls, v):
        if isinstance(v, bytes):
            v = v.decode('utf-8')
        return AuthProvider(v) if isinstance(v, str) else v


# Authentication schemas
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class OAuthLoginRequest(BaseModel):
    provider: AuthProvider
    access_token: str
    id_token: Optional[str] = None  # For Apple Sign-In


class TokenData(BaseModel):
    sub: str
    email: str
    username: str
    role: str
    exp: int
    iat: int
    jti: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v


class EmailVerificationRequest(BaseModel):
    token: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('New password must be at least 8 characters long')
        return v


class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None

    @validator('phone', pre=True)
    def validate_phone(cls, v):
        if v and not v.startswith('+'):
            return f'+91{v}' if v.startswith(('6', '7', '8', '9')) else v
        return v


class DeactivateAccountRequest(BaseModel):
    password: str
    reason: Optional[str] = None


class SessionInfo(BaseModel):
    jti: str
    created_at: datetime
    last_used: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    is_current: bool = False


class UserSessionsResponse(BaseModel):
    sessions: List[SessionInfo]
    total_sessions: int


class RevokeSessionRequest(BaseModel):
    session_jti: str


class AdminUserResponse(UserResponse):
    """Extended user response for admin operations."""
    last_login: Optional[datetime] = None
    failed_login_attempts: int = 0
    is_locked: bool = False
    locked_until: Optional[datetime] = None
