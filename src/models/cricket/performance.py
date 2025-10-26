"""
Player Performance Models
Individual batting and bowling performance in an innings
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, Boolean, DateTime, ForeignKey, Integer, Numeric, CheckConstraint, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from src.models.base import Base


class BattingInnings(Base):
    """
    Individual batsman's performance in an innings
    """
    __tablename__ = "batting_innings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    innings_id = Column(UUID(as_uuid=True), ForeignKey("innings.id", ondelete="CASCADE"), nullable=False)
    batsman_user_id = Column(UUID(as_uuid=True), ForeignKey("user_auth.user_id"), nullable=False)
    cricket_profile_id = Column(UUID(as_uuid=True), ForeignKey("cricket_player_profiles.id"), nullable=True)
    batting_position = Column(Integer, nullable=True)
    
    # Performance (updated real-time)
    runs_scored = Column(Integer, default=0)
    balls_faced = Column(Integer, default=0)
    fours = Column(Integer, default=0)
    sixes = Column(Integer, default=0)
    strike_rate = Column(Numeric(5, 2), nullable=True)  # Computed: (runs_scored / balls_faced) * 100
    
    # Dismissal
    is_out = Column(Boolean, default=False)
    wicket_id = Column(UUID(as_uuid=True), ForeignKey("wickets.id"), nullable=True)
    
    # Special Cases
    is_not_out = Column(Boolean, default=False)  # Stayed till end
    did_not_bat = Column(Boolean, default=False)  # Didn't get chance
    retired_hurt = Column(Boolean, default=False)
    retired_hurt_at_runs = Column(Integer, nullable=True)
    returned_to_bat_after_wicket = Column(Integer, nullable=True)
    
    # Milestones
    achieved_fifty = Column(Boolean, default=False)
    achieved_hundred = Column(Boolean, default=False)
    
    # Timing
    started_batting_at = Column(DateTime, nullable=True)
    ended_batting_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    innings = relationship("Innings")
    batsman = relationship("UserAuth", foreign_keys=[batsman_user_id])
    cricket_profile = relationship("CricketPlayerProfile", foreign_keys=[cricket_profile_id])
    wicket = relationship("Wicket", foreign_keys=[wicket_id])
    
    __table_args__ = (
        CheckConstraint('batting_position IS NULL OR (batting_position BETWEEN 1 AND 11)', 
                       name='batting_pos_check'),
    )

    def __repr__(self):
        return f"<BattingInnings(innings_id={self.innings_id}, batsman={self.batsman_user_id})>"


class BowlingFigures(Base):
    """
    Individual bowler's performance in an innings
    """
    __tablename__ = "bowling_figures"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    innings_id = Column(UUID(as_uuid=True), ForeignKey("innings.id", ondelete="CASCADE"), nullable=False)
    bowler_user_id = Column(UUID(as_uuid=True), ForeignKey("user_auth.user_id"), nullable=False)
    cricket_profile_id = Column(UUID(as_uuid=True), ForeignKey("cricket_player_profiles.id"), nullable=True)
    
    # Bowling Figures (the famous "4-0-23-2" format)
    overs_bowled = Column(Numeric(4, 1), default=0.0)  # 4.2 means 4 overs + 2 balls
    maidens = Column(Integer, default=0)
    runs_conceded = Column(Integer, default=0)
    wickets_taken = Column(Integer, default=0)
    economy_rate = Column(Numeric(4, 2), nullable=True)  # Computed: runs_conceded / overs_bowled
    
    # Extras Conceded
    wides_conceded = Column(Integer, default=0)
    no_balls_conceded = Column(Integer, default=0)
    
    # Milestones
    is_five_wicket_haul = Column(Boolean, default=False)
    is_hat_trick = Column(Boolean, default=False)
    
    # Which Overs Bowled (for analytics)
    overs_list = Column(ARRAY(Integer), default=[])  # [1, 3, 5, 7, ...]
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    innings = relationship("Innings")
    bowler = relationship("UserAuth", foreign_keys=[bowler_user_id])
    cricket_profile = relationship("CricketPlayerProfile", foreign_keys=[cricket_profile_id])

    def __repr__(self):
        return f"<BowlingFigures(innings_id={self.innings_id}, bowler={self.bowler_user_id})>"


class Partnership(Base):
    """
    Batting partnerships between two batsmen
    """
    __tablename__ = "partnerships"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    innings_id = Column(UUID(as_uuid=True), ForeignKey("innings.id", ondelete="CASCADE"), nullable=False)
    batsman1_user_id = Column(UUID(as_uuid=True), ForeignKey("user_auth.user_id"), nullable=False)
    batsman2_user_id = Column(UUID(as_uuid=True), ForeignKey("user_auth.user_id"), nullable=False)
    
    # Partnership Details
    partnership_number = Column(Integer, nullable=False)  # 1st wicket, 2nd wicket, etc.
    partnership_runs = Column(Integer, default=0)
    balls_faced = Column(Integer, default=0)
    
    # Individual Contributions
    batsman1_runs = Column(Integer, default=0)
    batsman2_runs = Column(Integer, default=0)
    
    # How It Ended
    ended_by_wicket_id = Column(UUID(as_uuid=True), ForeignKey("wickets.id"), nullable=True)
    ended_at_team_score = Column(Integer, nullable=True)
    
    # Milestones
    is_fifty_partnership = Column(Boolean, default=False)
    is_hundred_partnership = Column(Boolean, default=False)
    
    # Timing
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    innings = relationship("Innings")
    batsman1 = relationship("UserAuth", foreign_keys=[batsman1_user_id])
    batsman2 = relationship("UserAuth", foreign_keys=[batsman2_user_id])
    ended_by_wicket = relationship("Wicket", foreign_keys=[ended_by_wicket_id])

    def __repr__(self):
        return f"<Partnership(innings_id={self.innings_id}, partnership={self.partnership_number})>"
