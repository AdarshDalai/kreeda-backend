import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.utils.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    supabase_id = Column(String(255), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(20), unique=True, index=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    avatar_url = Column(Text, nullable=True)

    # System fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    is_active = Column(Boolean, default=True)

    # Relationships
    created_teams = relationship(
        "Team", foreign_keys="Team.created_by_id", back_populates="creator"
    )
    captained_teams = relationship(
        "Team", foreign_keys="Team.captain_id", back_populates="captain"
    )
    team_memberships = relationship("TeamMember", back_populates="user")
    created_matches = relationship(
        "CricketMatch",
        foreign_keys="CricketMatch.created_by_id",
        back_populates="creator",
    )

    # Profile relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    security_settings = relationship(
        "UserSecuritySettings", back_populates="user", uselist=False
    )
    activity_logs = relationship("UserActivityLog", back_populates="user")
    sessions = relationship("UserSession", back_populates="user")
    achievements = relationship("UserAchievement", back_populates="user")


class Team(Base):
    __tablename__ = "teams"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, index=True)
    short_name = Column(String(10), nullable=False)
    logo_url = Column(Text, nullable=True)

    # Team relationships
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    captain_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # System fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)

    # Relationships
    creator = relationship(
        "User", foreign_keys=[created_by_id], back_populates="created_teams"
    )
    captain = relationship(
        "User", foreign_keys=[captain_id], back_populates="captained_teams"
    )
    members = relationship("TeamMember", back_populates="team")
    invitations = relationship("TeamInvitation", back_populates="team")
    home_matches = relationship(
        "CricketMatch", foreign_keys="CricketMatch.team_a_id", back_populates="team_a"
    )
    away_matches = relationship(
        "CricketMatch", foreign_keys="CricketMatch.team_b_id", back_populates="team_b"
    )


class TeamMember(Base):
    __tablename__ = "team_members"

    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)

    # Member details
    role = Column(String(20), default="player")  # player, captain, vice_captain
    jersey_number = Column(String(10), nullable=True)

    joined_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    team = relationship("Team", back_populates="members")
    user = relationship("User", back_populates="team_memberships")


class TeamInvitation(Base):
    __tablename__ = "team_invitations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)
    invited_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    phone = Column(String(20), nullable=True)
    status = Column(String(20), nullable=False, default="pending", index=True)  # pending, accepted, rejected, expired
    token = Column(String(255), nullable=False, unique=True, index=True)
    message = Column(Text, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    team = relationship("Team", back_populates="invitations")
    invited_by = relationship("User", foreign_keys=[invited_by_id])


class MatchPlayingXI(Base):
    __tablename__ = "match_playing_xi"
    
    match_id = Column(UUID(as_uuid=True), ForeignKey("cricket_matches.id"), primary_key=True)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), primary_key=True)  
    player_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    batting_order = Column(Integer, nullable=True)
    is_captain = Column(Boolean, default=False)
    is_wicket_keeper = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    match = relationship("CricketMatch")
    team = relationship("Team")
    player = relationship("User")
