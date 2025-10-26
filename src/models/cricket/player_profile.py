"""
Cricket Player Profile Model
Cricket-specific player data and career statistics
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Numeric, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from src.models.base import Base
from src.models.enums import PlayingRole, BattingStyle, BowlingStyle


class CricketPlayerProfile(Base):
    """
    Cricket-specific player profile with career statistics
    """
    __tablename__ = "cricket_player_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sport_profile_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("sport_profiles.id", ondelete="CASCADE"), 
        unique=True, 
        nullable=False
    )
    
    # Player Type
    playing_role = Column(SQLEnum(PlayingRole, name="playing_role"), nullable=False)
    batting_style = Column(SQLEnum(BattingStyle, name="batting_style"), nullable=True)
    bowling_style = Column(SQLEnum(BowlingStyle, name="bowling_style"), nullable=True)
    
    # Career Statistics (Aggregated from matches)
    matches_played = Column(Integer, default=0)
    total_runs = Column(Integer, default=0)
    total_wickets = Column(Integer, default=0)
    catches = Column(Integer, default=0)
    stumpings = Column(Integer, default=0)
    run_outs = Column(Integer, default=0)
    
    # Batting Stats
    batting_avg = Column(Numeric(5, 2), nullable=True)  # total_runs / times_out
    strike_rate = Column(Numeric(5, 2), nullable=True)  # (total_runs / balls_faced) * 100
    highest_score = Column(Integer, default=0)
    fifties = Column(Integer, default=0)
    hundreds = Column(Integer, default=0)
    balls_faced = Column(Integer, default=0)
    fours = Column(Integer, default=0)
    sixes = Column(Integer, default=0)
    
    # Bowling Stats
    bowling_avg = Column(Numeric(5, 2), nullable=True)  # runs_conceded / total_wickets
    economy_rate = Column(Numeric(4, 2), nullable=True)  # runs_conceded / overs_bowled
    best_bowling = Column(String(10), nullable=True)  # e.g., "5/23"
    five_wickets = Column(Integer, default=0)
    ten_wickets = Column(Integer, default=0)
    balls_bowled = Column(Integer, default=0)
    runs_conceded = Column(Integer, default=0)
    maidens = Column(Integer, default=0)
    
    # Profile Info
    jersey_number = Column(Integer, nullable=True)
    
    # Metadata
    stats_last_updated = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sport_profile = relationship("SportProfile", backref="cricket_profile")

    def __repr__(self):
        return f"<CricketPlayerProfile(id={self.id}, role={self.playing_role})>"
