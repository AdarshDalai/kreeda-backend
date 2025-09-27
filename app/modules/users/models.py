"""
User Management Models

SQLAlchemy models for user management system
"""

from datetime import datetime
from typing import Optional, List
from uuid import uuid4
from sqlalchemy import String, Boolean, DateTime, Text, Date, Integer, CheckConstraint, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class User(BaseModel):
    """User model for authentication and basic user data"""
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()), index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    supabase_user_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), unique=True, index=True)
    
    # Relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    sport_profiles = relationship("SportProfile", back_populates="user", cascade="all, delete-orphan")
    team_memberships = relationship("TeamMember", back_populates="user", cascade="all, delete-orphan")
    
    # Table constraints
    __table_args__ = (
        CheckConstraint("email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$'", name="valid_email"),
        CheckConstraint("LENGTH(username) >= 3", name="username_length"),
    )


class UserProfile(BaseModel):
    """Extended user profile information"""
    __tablename__ = "user_profiles"

    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, index=True)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(Text)
    bio: Mapped[Optional[str]] = mapped_column(Text)
    location: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    date_of_birth: Mapped[Optional[datetime]] = mapped_column(Date)
    phone_number: Mapped[Optional[str]] = mapped_column(String(20))
    emergency_contact: Mapped[Optional[dict]] = mapped_column(JSONB)  # {name, phone, relation}
    preferences: Mapped[dict] = mapped_column(JSONB, default=dict)
    
    # Relationships
    user = relationship("User", back_populates="profile")
    
    # Table constraints
    __table_args__ = (
        CheckConstraint("phone_number ~ '^\\+?[1-9]\\d{1,14}$'", name="valid_phone"),
    )


class SportProfile(BaseModel):
    """Sport-specific user profiles"""
    __tablename__ = "sport_profiles"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()), index=True)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    sport_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    skill_level: Mapped[str] = mapped_column(String(20), default="BEGINNER")
    primary_position: Mapped[Optional[str]] = mapped_column(String(50))
    secondary_positions: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String))
    playing_style: Mapped[Optional[str]] = mapped_column(String(100))
    career_stats: Mapped[dict] = mapped_column(JSONB, default=dict)
    achievements: Mapped[List[dict]] = mapped_column(JSONB, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="sport_profiles")
    
    # Table constraints
    __table_args__ = (
        CheckConstraint("skill_level IN ('BEGINNER', 'INTERMEDIATE', 'ADVANCED', 'PROFESSIONAL')", name="valid_skill_level"),
    )