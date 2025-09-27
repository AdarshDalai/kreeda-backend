"""
Team Management Models

SQLAlchemy models for team management system
"""

from datetime import datetime
from typing import Optional, List
from uuid import uuid4
from sqlalchemy import String, Boolean, DateTime, Text, ForeignKey, Integer, CheckConstraint, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.models.base import BaseModel


class TeamType(str, enum.Enum):
    """Team types supported by the platform"""
    CRICKET = "cricket"
    FOOTBALL = "football"
    BASKETBALL = "basketball"
    HOCKEY = "hockey"
    VOLLEYBALL = "volleyball"
    BADMINTON = "badminton"
    TENNIS = "tennis"


class TeamStatus(str, enum.Enum):
    """Team status options"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DISBANDED = "disbanded"
    PENDING = "pending"


class MemberRole(str, enum.Enum):
    """Team member roles"""
    CAPTAIN = "captain"
    VICE_CAPTAIN = "vice_captain"
    PLAYER = "player"
    COACH = "coach"
    MANAGER = "manager"
    ADMIN = "admin"


class MemberStatus(str, enum.Enum):
    """Team member status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"
    LEFT = "left"


class Team(BaseModel):
    """Team model for team management system"""
    __tablename__ = "user_teams"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()), index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    short_name: Mapped[Optional[str]] = mapped_column(String(10))
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Team configuration
    team_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    
    # Team details
    logo_url: Mapped[Optional[str]] = mapped_column(String(500))
    home_ground: Mapped[Optional[str]] = mapped_column(String(200))
    founded_year: Mapped[Optional[int]] = mapped_column(Integer)
    website: Mapped[Optional[str]] = mapped_column(String(200))
    
    # Location info
    city: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    state: Mapped[Optional[str]] = mapped_column(String(100))
    country: Mapped[str] = mapped_column(String(100), default="India")
    
    # Privacy and settings
    is_public: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    auto_accept_members: Mapped[bool] = mapped_column(Boolean, default=False)
    max_members: Mapped[int] = mapped_column(Integer, default=50)
    
    # Contact information
    contact_email: Mapped[Optional[str]] = mapped_column(String(255))
    contact_phone: Mapped[Optional[str]] = mapped_column(String(20))
    
    # Additional metadata
    settings: Mapped[dict] = mapped_column(JSONB, default=dict)
    tags: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    
    # Relationships
    members = relationship("TeamMember", back_populates="team", cascade="all, delete-orphan")
    
    # Table constraints
    __table_args__ = (
        Index('ix_teams_name_type', 'name', 'team_type'),
        Index('ix_teams_location', 'city', 'state'),
        UniqueConstraint('name', 'team_type', 'city', name='uq_team_name_type_city'),
        CheckConstraint("team_type IN ('cricket', 'football', 'basketball', 'hockey', 'volleyball', 'badminton', 'tennis')", name="valid_team_type"),
        CheckConstraint("status IN ('active', 'inactive', 'disbanded', 'pending')", name="valid_team_status"),
    )


class TeamMember(BaseModel):
    """Team member model for managing team memberships"""
    __tablename__ = "team_members"
    
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()), index=True)
    
    # Foreign keys
    team_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("user_teams.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Member details
    role: Mapped[str] = mapped_column(String(20), default="player", index=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    
    # Membership metadata
    jersey_number: Mapped[Optional[int]] = mapped_column(Integer)
    position: Mapped[Optional[str]] = mapped_column(String(50))
    joined_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    left_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Member permissions and settings
    permissions: Mapped[dict] = mapped_column(JSONB, default=dict)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    stats: Mapped[dict] = mapped_column(JSONB, default=dict)
    
    # Relationships
    team = relationship("Team", back_populates="members")
    user = relationship("User", back_populates="team_memberships")
    
    # Table constraints
    __table_args__ = (
        UniqueConstraint('team_id', 'user_id', name='uq_team_user'),
        UniqueConstraint('team_id', 'jersey_number', name='uq_team_jersey'),
        Index('ix_team_members_team_role', 'team_id', 'role'),
        Index('ix_team_members_status', 'status'),
        CheckConstraint("role IN ('captain', 'vice_captain', 'player', 'coach', 'manager', 'admin')", name="valid_member_role"),
        CheckConstraint("status IN ('active', 'inactive', 'suspended', 'pending', 'left')", name="valid_member_status"),
    )


class TeamInvitation(BaseModel):
    """Team invitation model for managing team join requests"""
    __tablename__ = "team_invitations"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()), index=True)
    
    # Foreign keys
    team_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("user_teams.id", ondelete="CASCADE"), nullable=False, index=True)
    invited_user_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    invited_by_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="SET NULL"), index=True)
    
    # Invitation details
    email: Mapped[Optional[str]] = mapped_column(String(255))
    proposed_role: Mapped[str] = mapped_column(String(20), default="player")
    message: Mapped[Optional[str]] = mapped_column(Text)
    
    # Status and timing
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    responded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    team = relationship("Team")
    invited_user = relationship("User", foreign_keys=[invited_user_id])
    invited_by = relationship("User", foreign_keys=[invited_by_id])
    
    # Table constraints
    __table_args__ = (
        Index('ix_team_invitations_team_email', 'team_id', 'email'),
        Index('ix_team_invitations_status_expires', 'status', 'expires_at'),
        CheckConstraint("status IN ('pending', 'accepted', 'declined', 'expired')", name="valid_invitation_status"),
        CheckConstraint("proposed_role IN ('captain', 'vice_captain', 'player', 'coach', 'manager', 'admin')", name="valid_proposed_role"),
    )