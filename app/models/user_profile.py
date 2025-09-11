from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, JSON, Integer, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.utils.database import Base


class UserProfile(Base):
    """Extended user profile with comprehensive settings"""
    __tablename__ = "user_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    
    # Extended Profile Information
    display_name = Column(String(50), nullable=True)
    bio = Column(Text, nullable=True)
    location = Column(String(100), nullable=True)
    website = Column(Text, nullable=True)
    birth_date = Column(DateTime(timezone=True), nullable=True)
    phone_number = Column(String(20), nullable=True)
    emergency_contact = Column(String(100), nullable=True)
    
    # Privacy Settings (stored as JSON for flexibility)
    privacy_settings = Column(JSON, nullable=True, default={
        "profile_visibility": "public",
        "email_visibility": "private", 
        "show_online_status": True,
        "allow_friend_requests": True,
        "search_visibility": True
    })
    
    # Notification Settings
    notification_settings = Column(JSON, nullable=True, default={
        "email_notifications": "important",
        "push_notifications": "all",
        "match_notifications": True,
        "team_notifications": True,
        "message_notifications": True,
        "marketing_emails": False
    })
    
    # App Preferences
    app_preferences = Column(JSON, nullable=True, default={
        "preferred_theme": "auto",
        "preferred_language": "en",
        "timezone": None,
        "date_format": "DD/MM/YYYY",
        "time_format": "24h",
        "auto_save": True
    })
    
    # Sports Profile
    sports_profile = Column(JSON, nullable=True, default={
        "favorite_sports": [],
        "playing_position": None,
        "skill_level": None,
        "years_playing": None,
        "achievements": [],
        "preferred_role": None
    })
    
    # Statistics and Activity
    last_login = Column(DateTime(timezone=True), nullable=True)
    login_count = Column(Integer, default=0)
    profile_completion_percentage = Column(Float, default=0.0)
    
    # System fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="profile")


class UserSecuritySettings(Base):
    """User security and authentication settings"""
    __tablename__ = "user_security_settings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    
    # Two-factor authentication
    two_factor_enabled = Column(Boolean, default=False)
    two_factor_secret = Column(String(255), nullable=True)  # Encrypted TOTP secret
    backup_codes = Column(JSON, nullable=True)  # Encrypted backup codes
    
    # Security preferences
    email_verification_required = Column(Boolean, default=True)
    login_notifications = Column(Boolean, default=True)
    active_sessions_limit = Column(Integer, default=5)
    
    # Security tracking
    password_last_changed = Column(DateTime(timezone=True), nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    account_locked_until = Column(DateTime(timezone=True), nullable=True)
    
    # System fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="security_settings")


class UserActivityLog(Base):
    """User activity tracking for security and analytics"""
    __tablename__ = "user_activity_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Activity details
    activity_type = Column(String(50), nullable=False)  # login, logout, profile_update, etc.
    description = Column(Text, nullable=False)
    activity_metadata = Column(JSON, nullable=True)  # Additional context data
    
    # Request information
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(Text, nullable=True)
    location = Column(String(100), nullable=True)  # Geolocation if available
    
    # System fields
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="activity_logs")


class UserSession(Base):
    """Active user sessions tracking"""
    __tablename__ = "user_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Session details
    session_token = Column(String(255), unique=True, nullable=False)
    device_info = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    location = Column(String(100), nullable=True)
    
    # Session management
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_activity = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="sessions")


class UserAchievement(Base):
    """User achievements and badges"""
    __tablename__ = "user_achievements"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Achievement details
    achievement_type = Column(String(50), nullable=False)  # matches_won, teams_joined, etc.
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    icon_url = Column(Text, nullable=True)
    
    # Achievement data
    criteria_met = Column(JSON, nullable=True)  # What criteria were met
    earned_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Display settings
    is_visible = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    
    # Relationships
    user = relationship("User", back_populates="achievements")


# Update the existing User model to include relationships
"""
Add these relationships to the existing User model in user.py:

# Profile and settings relationships
profile = relationship("UserProfile", back_populates="user", uselist=False)
security_settings = relationship("UserSecuritySettings", back_populates="user", uselist=False)
activity_logs = relationship("UserActivityLog", back_populates="user")
sessions = relationship("UserSession", back_populates="user")
achievements = relationship("UserAchievement", back_populates="user")
"""
