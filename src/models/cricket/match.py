"""
Match Models
Core match entity and related tables
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, Text, CheckConstraint, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from src.models.base import Base
from src.models.enums import (
    SportType, MatchType, MatchCategory, MatchStatus, MatchVisibility,
    ResultType, ElectedTo, OfficialRole, OfficialAssignment
)


class Match(Base):
    """
    The core match entity - highly configurable for all match types
    """
    __tablename__ = "matches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sport_type = Column(SQLEnum(SportType, name="sport_type"), default=SportType.CRICKET)
    
    # Match Format
    match_type = Column(SQLEnum(MatchType, name="match_type"), nullable=False)
    match_category = Column(SQLEnum(MatchCategory, name="match_category"), default=MatchCategory.CASUAL)
    
    # Match Rules (JSONB for ultimate flexibility)
    match_rules = Column(JSONB, nullable=False, default={
        "players_per_team": 11,
        "overs_per_side": 20,
        "balls_per_over": 6,
        "wickets_to_fall": 10,
        "powerplay_overs": None,
        "death_overs_start": None,
        "allow_same_bowler_consecutive": False,
        "retire_after_runs": None,
        "mandatory_bowling": False,
        "dls_applicable": False,
        "super_over_if_tie": False,
        "boundary_count_rule": False
    })
    
    # Match Preset (quick setup)
    match_preset = Column(String(50), nullable=True)
    
    # Teams
    team_a_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)
    team_b_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)
    
    # Toss
    toss_won_by_team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=True)
    elected_to = Column(SQLEnum(ElectedTo, name="elected_to"), nullable=True)
    toss_completed_at = Column(DateTime, nullable=True)
    
    # Tournament Context (Phase 2)
    tournament_id = Column(UUID(as_uuid=True), nullable=True)
    round_name = Column(String(100), nullable=True)
    
    # Venue
    venue = Column(JSONB, nullable=False)  # {name, location: {lat, lng}, city, ground_type}
    
    # Schedule
    scheduled_start_time = Column(DateTime(timezone=True), nullable=False)
    actual_start_time = Column(DateTime(timezone=True), nullable=True)
    estimated_end_time = Column(DateTime(timezone=True), nullable=True)
    actual_end_time = Column(DateTime(timezone=True), nullable=True)
    
    # Status
    match_status = Column(SQLEnum(MatchStatus, name="match_status"), default=MatchStatus.SCHEDULED)
    
    # Discovery & Visibility
    visibility = Column(SQLEnum(MatchVisibility, name="match_visibility"), default=MatchVisibility.PUBLIC)
    match_code = Column(String(8), unique=True, nullable=True)  # e.g., "KRD-AB12"
    is_featured = Column(Boolean, default=False)
    
    # Result (populated after match ends)
    winning_team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=True)
    result_type = Column(SQLEnum(ResultType, name="result_type"), nullable=True)
    result_margin = Column(String(100), nullable=True)
    player_of_match_user_id = Column(UUID(as_uuid=True), ForeignKey("user_auth.user_id"), nullable=True)
    
    # Weather/Conditions
    weather_conditions = Column(JSONB, nullable=True)
    pitch_report = Column(Text, nullable=True)
    
    # Metadata
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("user_auth.user_id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    team_a = relationship("Team", foreign_keys=[team_a_id])
    team_b = relationship("Team", foreign_keys=[team_b_id])
    toss_winner = relationship("Team", foreign_keys=[toss_won_by_team_id])
    winning_team = relationship("Team", foreign_keys=[winning_team_id])
    player_of_match = relationship("UserAuth", foreign_keys=[player_of_match_user_id])
    creator = relationship("UserAuth", foreign_keys=[created_by_user_id])
    
    officials = relationship("MatchOfficial", back_populates="match", cascade="all, delete-orphan")
    playing_xi = relationship("MatchPlayingXI", back_populates="match", cascade="all, delete-orphan")
    innings = relationship("Innings", back_populates="match", cascade="all, delete-orphan")
    
    __table_args__ = (
        CheckConstraint('team_a_id != team_b_id', name='different_teams_check'),
    )

    def __repr__(self):
        return f"<Match(id={self.id}, status={self.match_status})>"


class MatchOfficial(Base):
    """
    Scorers, umpires, and other match officials
    """
    __tablename__ = "match_officials"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    match_id = Column(UUID(as_uuid=True), ForeignKey("matches.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user_auth.user_id"), nullable=False)
    
    # Role
    role = Column(SQLEnum(OfficialRole, name="official_role"), nullable=False)
    assignment = Column(SQLEnum(OfficialAssignment, name="official_assignment"), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    joined_at = Column(DateTime, default=datetime.utcnow)
    left_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    match = relationship("Match", back_populates="officials")
    user = relationship("UserAuth", foreign_keys=[user_id])

    def __repr__(self):
        return f"<MatchOfficial(match_id={self.match_id}, role={self.role})>"


class MatchPlayingXI(Base):
    """
    The actual playing 11 (or fewer) for each team in a specific match
    """
    __tablename__ = "match_playing_xi"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    match_id = Column(UUID(as_uuid=True), ForeignKey("matches.id", ondelete="CASCADE"), nullable=False)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user_auth.user_id"), nullable=False)
    cricket_profile_id = Column(UUID(as_uuid=True), ForeignKey("cricket_player_profiles.id"), nullable=True)
    
    # Playing Roles (flexible for gully cricket)
    can_bat = Column(Boolean, default=True)
    can_bowl = Column(Boolean, default=True)
    is_wicket_keeper = Column(Boolean, default=False)
    is_captain = Column(Boolean, default=False)
    
    # Batting/Bowling Order (null if flexible/undecided)
    batting_position = Column(Integer, nullable=True)
    bowling_preference = Column(Integer, nullable=True)
    
    # Fielding
    fielding_position = Column(String(50), nullable=True)
    
    # Status
    played = Column(Boolean, default=True)
    substitute_for_user_id = Column(UUID(as_uuid=True), ForeignKey("user_auth.user_id"), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    match = relationship("Match", back_populates="playing_xi")
    team = relationship("Team", foreign_keys=[team_id])
    user = relationship("UserAuth", foreign_keys=[user_id])
    cricket_profile = relationship("CricketPlayerProfile", foreign_keys=[cricket_profile_id])
    substitute_for = relationship("UserAuth", foreign_keys=[substitute_for_user_id])
    
    __table_args__ = (
        CheckConstraint('batting_position IS NULL OR (batting_position BETWEEN 1 AND 11)', 
                       name='batting_position_check'),
    )

    def __repr__(self):
        return f"<MatchPlayingXI(match_id={self.match_id}, user_id={self.user_id})>"
