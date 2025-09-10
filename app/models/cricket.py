from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Float, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.utils.database import Base


class CricketMatch(Base):
    __tablename__ = "cricket_matches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Match basics
    team_a_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)
    team_b_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)
    overs_per_innings = Column(Integer, default=20)
    
    # Match setup
    venue = Column(String(200), nullable=False)
    match_date = Column(DateTime(timezone=True), nullable=False)
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Match state
    status = Column(String(20), default="upcoming")  # upcoming, live, completed
    current_innings = Column(Integer, default=1)
    
    # Toss details
    toss_winner_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=True)
    toss_decision = Column(String(10), nullable=True)  # "bat" or "bowl"
    
    # Live score (denormalized for quick access)
    team_a_score = Column(Integer, default=0)
    team_a_wickets = Column(Integer, default=0)
    team_a_overs = Column(Float, default=0.0)
    
    team_b_score = Column(Integer, default=0)
    team_b_wickets = Column(Integer, default=0)
    team_b_overs = Column(Float, default=0.0)
    
    # Match result
    winner_team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=True)
    result_description = Column(Text, nullable=True)
    
    # System fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    team_a = relationship("Team", foreign_keys=[team_a_id], back_populates="home_matches")
    team_b = relationship("Team", foreign_keys=[team_b_id], back_populates="away_matches")
    creator = relationship("User", foreign_keys=[created_by_id], back_populates="created_matches")
    toss_winner = relationship("Team", foreign_keys=[toss_winner_id])
    winner_team = relationship("Team", foreign_keys=[winner_team_id])
    balls = relationship("CricketBall", back_populates="match")
    player_stats = relationship("MatchPlayerStats", back_populates="match")
    
    @property
    def team_a_overs_display(self) -> str:
        """Display overs in cricket format (e.g., 18.4)"""
        if not self.team_a_overs:
            return "0.0"
        overs = int(self.team_a_overs)
        balls = int((self.team_a_overs - overs) * 10)
        return f"{overs}.{balls}"
    
    @property
    def team_b_overs_display(self) -> str:
        """Display overs in cricket format (e.g., 18.4)"""
        if not self.team_b_overs:
            return "0.0"
        overs = int(self.team_b_overs)
        balls = int((self.team_b_overs - overs) * 10)
        return f"{overs}.{balls}"
    
    @property
    def current_run_rate(self) -> float:
        """Calculate current run rate for batting team"""
        if self.current_innings == 1:
            overs = self.team_a_overs or 0.1
            return round(self.team_a_score / overs, 2) if overs > 0 else 0.0
        else:
            overs = self.team_b_overs or 0.1
            return round(self.team_b_score / overs, 2) if overs > 0 else 0.0
    
    @property
    def required_run_rate(self) -> float:
        """Calculate required run rate for chasing team"""
        if self.current_innings == 1:
            return 0.0  # First innings
        
        target = self.team_a_score + 1
        scored = self.team_b_score
        remaining_runs = target - scored
        remaining_overs = self.overs_per_innings - (self.team_b_overs or 0)
        
        if remaining_overs <= 0:
            return 0.0
        
        return round(remaining_runs / remaining_overs, 2)


class CricketBall(Base):
    __tablename__ = "cricket_balls"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    match_id = Column(UUID(as_uuid=True), ForeignKey("cricket_matches.id"), nullable=False, index=True)
    
    # Ball position
    innings = Column(Integer, nullable=False)
    over_number = Column(Integer, nullable=False)
    ball_number = Column(Integer, nullable=False)
    
    # Players involved
    bowler_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    batsman_striker_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    batsman_non_striker_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Ball outcome
    runs_scored = Column(Integer, default=0)
    extras = Column(Integer, default=0)
    ball_type = Column(String(20), default="legal")  # legal, wide, no_ball, bye, leg_bye
    
    # Wicket information
    is_wicket = Column(Boolean, default=False)
    wicket_type = Column(String(20), nullable=True)  # bowled, caught, lbw, run_out, stumped
    dismissed_player_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Additional info
    is_boundary = Column(Boolean, default=False)
    boundary_type = Column(String(10), nullable=True)  # "four" or "six"
    
    # System
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    match = relationship("CricketMatch", back_populates="balls")
    bowler = relationship("User", foreign_keys=[bowler_id])
    batsman_striker = relationship("User", foreign_keys=[batsman_striker_id])
    batsman_non_striker = relationship("User", foreign_keys=[batsman_non_striker_id])
    dismissed_player = relationship("User", foreign_keys=[dismissed_player_id])


class MatchPlayerStats(Base):
    __tablename__ = "match_player_stats"

    match_id = Column(UUID(as_uuid=True), ForeignKey("cricket_matches.id"), primary_key=True)
    player_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)
    
    # Batting stats
    batting_runs = Column(Integer, default=0)
    balls_faced = Column(Integer, default=0)
    fours_hit = Column(Integer, default=0)
    sixes_hit = Column(Integer, default=0)
    is_out = Column(Boolean, default=False)
    
    # Bowling stats
    overs_bowled = Column(Float, default=0.0)
    runs_conceded = Column(Integer, default=0)
    wickets_taken = Column(Integer, default=0)
    
    # System
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    match = relationship("CricketMatch", back_populates="player_stats")
    player = relationship("User")
    team = relationship("Team")
