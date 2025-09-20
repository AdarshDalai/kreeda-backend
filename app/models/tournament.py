"""
Tournament and competition management models
Builds on Phase 1 team and match infrastructure
"""
import uuid
from sqlalchemy import (
    Boolean, 
    Column, 
    DateTime, 
    ForeignKey, 
    Integer, 
    Numeric,
    String, 
    Text,
    UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.utils.database import Base


class Tournament(Base):
    __tablename__ = "tournaments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    tournament_type = Column(String(50), nullable=False, index=True)  # 'knockout', 'league', 'round_robin'
    
    # Tournament scheduling
    start_date = Column(DateTime(timezone=True), nullable=False, index=True)
    end_date = Column(DateTime(timezone=True), nullable=True)
    registration_deadline = Column(DateTime(timezone=True), nullable=True)
    
    # Tournament configuration
    max_teams = Column(Integer, default=8)
    min_teams = Column(Integer, default=4)
    entry_fee = Column(Numeric(10, 2), default=0)
    prize_money = Column(Numeric(10, 2), default=0)
    overs_per_innings = Column(Integer, default=20)
    
    # Tournament state
    status = Column(String(20), default="upcoming", index=True)  # 'upcoming', 'registration_open', 'ongoing', 'completed', 'cancelled'
    current_round = Column(Integer, default=0)
    
    # Organization
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    organizer_contact = Column(String(255), nullable=True)
    venue_details = Column(Text, nullable=True)
    
    # System fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    is_public = Column(Boolean, default=True)
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by_id])
    teams = relationship("TournamentTeam", back_populates="tournament")
    matches = relationship("TournamentMatch", back_populates="tournament")
    standings = relationship("TournamentStanding", back_populates="tournament")


class TournamentTeam(Base):
    __tablename__ = "tournament_teams"
    
    tournament_id = Column(UUID(as_uuid=True), ForeignKey("tournaments.id"), primary_key=True)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), primary_key=True)
    
    # Registration details
    registered_at = Column(DateTime(timezone=True), server_default=func.now())
    registered_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    registration_fee_paid = Column(Boolean, default=False)
    payment_reference = Column(String(100), nullable=True)
    
    # Tournament specific team details
    seed_number = Column(Integer, nullable=True)  # For seeded tournaments
    group_name = Column(String(10), nullable=True)  # For group stage tournaments
    
    # Status
    status = Column(String(20), default="registered")  # 'registered', 'confirmed', 'withdrawn'
    
    # Relationships
    tournament = relationship("Tournament", back_populates="teams")
    team = relationship("Team")
    registered_by = relationship("User", foreign_keys=[registered_by_id])


class TournamentMatch(Base):
    __tablename__ = "tournament_matches"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tournament_id = Column(UUID(as_uuid=True), ForeignKey("tournaments.id"), nullable=False)
    match_id = Column(UUID(as_uuid=True), ForeignKey("cricket_matches.id"), nullable=False)
    
    # Tournament match details
    round_number = Column(Integer, nullable=False, index=True)
    match_number = Column(Integer, nullable=False)
    stage = Column(String(50), nullable=True, index=True)  # 'group', 'quarter_final', 'semi_final', 'final'
    group_name = Column(String(10), nullable=True)  # For group stage matches
    
    # Scheduling
    scheduled_date = Column(DateTime(timezone=True), nullable=True)
    venue = Column(String(200), nullable=True)
    
    # Match importance
    is_knockout = Column(Boolean, default=False)
    importance_level = Column(Integer, default=1)  # 1-5 scale, 5 being final
    
    # System fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    tournament = relationship("Tournament", back_populates="matches")
    match = relationship("CricketMatch")
    
    # Unique constraint to prevent duplicate tournament-match pairs
    __table_args__ = (UniqueConstraint('tournament_id', 'match_id', name='_tournament_match_uc'),)


class TournamentStanding(Base):
    __tablename__ = "tournament_standings"
    
    tournament_id = Column(UUID(as_uuid=True), ForeignKey("tournaments.id"), primary_key=True)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), primary_key=True)
    
    # Match statistics
    matches_played = Column(Integer, default=0)
    matches_won = Column(Integer, default=0)
    matches_lost = Column(Integer, default=0)
    matches_tied = Column(Integer, default=0)
    matches_no_result = Column(Integer, default=0)
    
    # Points system
    points = Column(Integer, default=0)
    
    # Cricket specific stats
    runs_scored = Column(Integer, default=0)
    runs_conceded = Column(Integer, default=0)
    overs_faced = Column(Numeric(5, 1), default=0)
    overs_bowled = Column(Numeric(5, 1), default=0)
    net_run_rate = Column(Numeric(5, 2), default=0)
    
    # Position tracking
    current_position = Column(Integer, nullable=True)
    previous_position = Column(Integer, nullable=True)
    
    # System fields
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    tournament = relationship("Tournament", back_populates="standings")
    team = relationship("Team")


class TournamentRule(Base):
    __tablename__ = "tournament_rules"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tournament_id = Column(UUID(as_uuid=True), ForeignKey("tournaments.id"), nullable=False)
    
    # Rule details
    rule_type = Column(String(50), nullable=False)  # 'points_system', 'tiebreaker', 'powerplay', etc.
    rule_name = Column(String(100), nullable=False)
    rule_description = Column(Text, nullable=False)
    rule_value = Column(String(500), nullable=True)  # JSON-like string for complex rules
    
    # Rule application
    applies_to_stage = Column(String(50), nullable=True)  # 'group', 'knockout', 'all'
    is_active = Column(Boolean, default=True)
    
    # System fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    tournament = relationship("Tournament")


# Add relationship to existing CricketMatch model (this will be imported in the cricket model file)
# We'll need to add this to the CricketMatch model:
# tournament_matches = relationship("TournamentMatch", back_populates="match")