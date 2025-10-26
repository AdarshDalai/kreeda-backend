"""
Innings and Overs Models
Live match progression tracking
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, Boolean, DateTime, ForeignKey, Integer, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from src.models.base import Base


class Innings(Base):
    """
    Each batting innings in a match
    """
    __tablename__ = "innings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    match_id = Column(UUID(as_uuid=True), ForeignKey("matches.id", ondelete="CASCADE"), nullable=False)
    innings_number = Column(Integer, nullable=False)
    
    # Teams
    batting_team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)
    bowling_team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)
    
    # Live State (updated real-time)
    current_over_number = Column(Integer, default=0)
    current_ball_in_over = Column(Integer, default=0)
    total_runs = Column(Integer, default=0)
    wickets_fallen = Column(Integer, default=0)
    extras = Column(Integer, default=0)
    
    # Innings Status
    is_completed = Column(Boolean, default=False)
    all_out = Column(Boolean, default=False)
    declared = Column(Boolean, default=False)
    
    # Target (for second innings)
    target_runs = Column(Integer, nullable=True)
    
    # Current Players (nullable if not started)
    striker_user_id = Column(UUID(as_uuid=True), ForeignKey("user_auth.user_id"), nullable=True)
    non_striker_user_id = Column(UUID(as_uuid=True), ForeignKey("user_auth.user_id"), nullable=True)
    current_bowler_user_id = Column(UUID(as_uuid=True), ForeignKey("user_auth.user_id"), nullable=True)
    next_batsman_user_id = Column(UUID(as_uuid=True), ForeignKey("user_auth.user_id"), nullable=True)
    
    # Timing
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    match = relationship("Match", back_populates="innings")
    batting_team = relationship("Team", foreign_keys=[batting_team_id])
    bowling_team = relationship("Team", foreign_keys=[bowling_team_id])
    striker = relationship("UserAuth", foreign_keys=[striker_user_id])
    non_striker = relationship("UserAuth", foreign_keys=[non_striker_user_id])
    current_bowler = relationship("UserAuth", foreign_keys=[current_bowler_user_id])
    next_batsman = relationship("UserAuth", foreign_keys=[next_batsman_user_id])
    
    overs = relationship("Over", back_populates="innings", cascade="all, delete-orphan")
    balls = relationship("Ball", back_populates="innings", cascade="all, delete-orphan")
    
    __table_args__ = (
        CheckConstraint('innings_number > 0', name='innings_number_positive'),
    )

    def __repr__(self):
        return f"<Innings(match_id={self.match_id}, innings={self.innings_number})>"


class Over(Base):
    """
    Aggregate data for each over
    """
    __tablename__ = "overs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    innings_id = Column(UUID(as_uuid=True), ForeignKey("innings.id", ondelete="CASCADE"), nullable=False)
    over_number = Column(Integer, nullable=False)
    bowler_user_id = Column(UUID(as_uuid=True), ForeignKey("user_auth.user_id"), nullable=False)
    
    # Over Summary (computed after over completes)
    runs_conceded = Column(Integer, default=0)
    wickets_taken = Column(Integer, default=0)
    legal_deliveries = Column(Integer, default=0)  # Usually 6, but can be less if innings ends
    extras_in_over = Column(Integer, default=0)
    is_maiden = Column(Boolean, default=False)
    is_completed = Column(Boolean, default=False)
    
    # Ball-by-ball sequence for UI (e.g., "W 1 4 . 2 6")
    ball_sequence = Column(JSONB, default=[])  # ["W", "1", "4", "0", "2", "6"]
    
    # Timing
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    innings = relationship("Innings", back_populates="overs")
    bowler = relationship("UserAuth", foreign_keys=[bowler_user_id])
    balls = relationship("Ball", back_populates="over", cascade="all, delete-orphan")
    
    __table_args__ = (
        CheckConstraint('over_number > 0', name='over_number_positive'),
    )

    def __repr__(self):
        return f"<Over(innings_id={self.innings_id}, over={self.over_number})>"
