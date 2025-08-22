"""
User Session Management

Session tracking, management, and analytics for user authentication sessions.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from enum import Enum


class SessionDevice(str, Enum):
    """Device types for sessions."""
    WEB = "web"
    MOBILE = "mobile"
    TABLET = "tablet"
    DESKTOP = "desktop"
    API = "api"
    UNKNOWN = "unknown"


class SessionStatus(str, Enum):
    """Session status."""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    SUSPICIOUS = "suspicious"


class UserSession(BaseModel):
    """User session information."""
    id: str
    user_id: UUID
    jti: str  # JWT ID
    device_type: SessionDevice
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    location: Optional[str] = None  # Geographic location
    created_at: datetime
    last_used: datetime
    expires_at: datetime
    status: SessionStatus = SessionStatus.ACTIVE
    is_current: bool = False
    
    # Additional metadata
    browser: Optional[str] = None
    os: Optional[str] = None
    device_name: Optional[str] = None
    
    model_config = {"from_attributes": True}


class CreateSessionRequest(BaseModel):
    """Request to create a new session."""
    user_id: UUID
    jti: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    expires_at: datetime
    metadata: Optional[Dict[str, Any]] = None


class UpdateSessionRequest(BaseModel):
    """Request to update session information."""
    last_used: Optional[datetime] = None
    ip_address: Optional[str] = None
    location: Optional[str] = None
    status: Optional[SessionStatus] = None


class SessionStats(BaseModel):
    """Session statistics."""
    total_sessions: int
    active_sessions: int
    expired_sessions: int
    revoked_sessions: int
    suspicious_sessions: int
    devices: Dict[str, int]
    locations: Dict[str, int]
    recent_activity: List[Dict[str, Any]]


class SessionActivity(BaseModel):
    """Session activity log."""
    id: str
    session_id: str
    action: str  # login, logout, token_refresh, api_call, etc.
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None
    
    model_config = {"from_attributes": True}


class SecurityAlert(BaseModel):
    """Security alert for suspicious activity."""
    id: str
    user_id: UUID
    alert_type: str  # suspicious_login, multiple_locations, unusual_activity
    severity: str  # low, medium, high, critical
    description: str
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    timestamp: datetime
    resolved: bool = False
    
    model_config = {"from_attributes": True}


class DeviceInfo(BaseModel):
    """Parsed device information."""
    device_type: SessionDevice
    browser: Optional[str] = None
    browser_version: Optional[str] = None
    os: Optional[str] = None
    os_version: Optional[str] = None
    device_name: Optional[str] = None
    is_mobile: bool = False
    is_tablet: bool = False
    is_desktop: bool = False
