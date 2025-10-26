"""
Team Models
Team entities and memberships
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from src.models.base import Base
from src.models.enums import SportType, TeamType, MembershipStatus


class Team(Base):
    """
    Team entity - flexible for casual and professional teams
    """
    __tablename__ = "teams"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    short_name = Column(String(50), nullable=True)  # e.g., "MI", "CSK"
    sport_type = Column(SQLEnum(SportType, name="sport_type"), nullable=False)
    team_type = Column(SQLEnum(TeamType, name="team_type"), default=TeamType.CASUAL)
    
    # Ownership
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("user_auth.user_id"), nullable=False)
    
    # Branding
    logo_url = Column(String(500), nullable=True)
    team_colors = Column(JSONB, nullable=True)  # {primary: "#FF0000", secondary: "#FFFFFF"}
    
    # Location (for club/franchise teams)
    home_ground = Column(JSONB, nullable=True)  # {name, location: {lat, lng}, city}
    
    # Status
    is_active = Column(Boolean, default=True)
    disbanded_at = Column(DateTime, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    creator = relationship("UserAuth", foreign_keys=[created_by_user_id])
    memberships = relationship("TeamMembership", back_populates="team", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Team(name={self.name}, sport={self.sport_type})>"


class TeamMembership(Base):
    """
    Team rosters - tracks who belongs to which team with what roles
    """
    __tablename__ = "team_memberships"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user_auth.user_id", ondelete="CASCADE"), nullable=False)
    sport_profile_id = Column(UUID(as_uuid=True), ForeignKey("sport_profiles.id"), nullable=False)
    
    # Roles (Player can have multiple roles) - JSONB array: ["player", "captain"]
    roles = Column(JSONB, nullable=False, default=["player"])
    
    # Cricket-specific
    cricket_profile_id = Column(UUID(as_uuid=True), ForeignKey("cricket_player_profiles.id"), nullable=True)
    jersey_number = Column(Integer, nullable=True)
    
    # Status
    status = Column(SQLEnum(MembershipStatus, name="membership_status"), default=MembershipStatus.ACTIVE)
    joined_at = Column(DateTime, default=datetime.utcnow)
    left_at = Column(DateTime, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    team = relationship("Team", back_populates="memberships")
    user = relationship("UserAuth", foreign_keys=[user_id])
    sport_profile = relationship("SportProfile", foreign_keys=[sport_profile_id])
    cricket_profile = relationship("CricketPlayerProfile", foreign_keys=[cricket_profile_id])

    def __repr__(self):
        return f"<TeamMembership(team_id={self.team_id}, user_id={self.user_id})>"
