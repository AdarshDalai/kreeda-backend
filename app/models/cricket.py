"""
Kreeda Cricket Database Models
Built for MVP: Teams, Players, Matches, Innings, Balls
Focus: Fast scoring, accurate calculations, real-time updates
"""
from sqlalchemy import (
    Column, Integer, String, Boolean, DECIMAL, DateTime, 
    ForeignKey, Text, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class User(Base):
    """User management for captains and scorers"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    teams_created = relationship("Team", back_populates="creator")


class Team(Base):
    """Cricket teams - keep it simple for MVP"""
    __tablename__ = "teams"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    short_name = Column(String(20))  # For scoreboard display
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    creator = relationship("User", back_populates="teams_created")
    players = relationship("Player", back_populates="team", cascade="all, delete-orphan")
    home_matches = relationship("Match", foreign_keys="Match.team_a_id", back_populates="team_a")
    away_matches = relationship("Match", foreign_keys="Match.team_b_id", back_populates="team_b")


class Player(Base):
    """Players within teams"""
    __tablename__ = "players"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    batting_order = Column(Integer)  # 1-11, can be null initially
    is_captain = Column(Boolean, default=False)
    is_wicket_keeper = Column(Boolean, default=False)
    jersey_number = Column(Integer)
    
    # Relationships
    team = relationship("Team", back_populates="players")
    
    # Indexes for fast lookups during scoring
    __table_args__ = (
        Index('idx_team_batting_order', 'team_id', 'batting_order'),
    )


class Match(Base):
    """Cricket matches - limited overs only for MVP"""
    __tablename__ = "matches"
    
    id = Column(Integer, primary_key=True, index=True)
    team_a_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    team_b_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    
    # Match settings
    overs_per_side = Column(Integer, nullable=False)  # 10, 15, 20, etc.
    venue = Column(String(200))
    match_date = Column(DateTime(timezone=True))
    
    # Toss and innings
    toss_winner_id = Column(Integer, ForeignKey("teams.id"))
    batting_first_id = Column(Integer, ForeignKey("teams.id"))
    current_innings = Column(Integer, default=1)  # 1 or 2
    
    # Match state
    status = Column(String(20), default='not_started')  # not_started, innings_1, innings_2, completed, abandoned
    winner_id = Column(Integer, ForeignKey("teams.id"))
    win_margin = Column(String(50))  # "5 wickets", "23 runs", etc.
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    
    # Relationships
    team_a = relationship("Team", foreign_keys=[team_a_id])
    team_b = relationship("Team", foreign_keys=[team_b_id])
    toss_winner = relationship("Team", foreign_keys=[toss_winner_id])
    batting_first = relationship("Team", foreign_keys=[batting_first_id])
    winner = relationship("Team", foreign_keys=[winner_id])
    innings_list = relationship("Innings", back_populates="match", cascade="all, delete-orphan")


class Innings(Base):
    """Individual innings within a match"""
    __tablename__ = "innings"
    
    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)
    innings_number = Column(Integer, nullable=False)  # 1 or 2
    batting_team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    bowling_team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    
    # Live scoring stats
    total_runs = Column(Integer, default=0)
    wickets_lost = Column(Integer, default=0)
    overs_completed = Column(DECIMAL(3,1), default=0.0)  # 15.4 means 15 overs 4 balls
    extras = Column(Integer, default=0)
    
    # Status
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime(timezone=True))
    
    # Relationships
    match = relationship("Match", back_populates="innings_list")
    batting_team = relationship("Team", foreign_keys=[batting_team_id])
    bowling_team = relationship("Team", foreign_keys=[bowling_team_id])
    balls = relationship("Ball", back_populates="innings", cascade="all, delete-orphan")
    
    # Fast lookups for live scoring
    __table_args__ = (
        Index('idx_match_innings', 'match_id', 'innings_number'),
    )


class Ball(Base):
    """Individual ball records - the heart of cricket scoring"""
    __tablename__ = "balls"
    
    id = Column(Integer, primary_key=True, index=True)
    innings_id = Column(Integer, ForeignKey("innings.id"), nullable=False)
    
    # Ball position
    over_number = Column(Integer, nullable=False)  # 1-based
    ball_number = Column(Integer, nullable=False)  # 1-6
    
    # Players involved
    batsman_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    non_striker_id = Column(Integer, ForeignKey("players.id"))
    bowler_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    
    # Ball outcome
    runs = Column(Integer, default=0)  # Runs scored by batsman
    extras = Column(Integer, default=0)  # Wides, byes, leg-byes, no-balls
    extra_type = Column(String(20))  # 'wide', 'noball', 'bye', 'legbye'
    
    # Wicket information
    is_wicket = Column(Boolean, default=False)
    wicket_type = Column(String(20))  # 'bowled', 'caught', 'lbw', 'run_out', 'stumped'
    wicket_player_id = Column(Integer, ForeignKey("players.id"))  # Player who got out
    fielder_id = Column(Integer, ForeignKey("players.id"))  # Catcher/fielder
    
    # Metadata
    is_valid_ball = Column(Boolean, default=True)  # False for wides/no-balls
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    innings = relationship("Innings", back_populates="balls")
    batsman = relationship("Player", foreign_keys=[batsman_id])
    non_striker = relationship("Player", foreign_keys=[non_striker_id])
    bowler = relationship("Player", foreign_keys=[bowler_id])
    wicket_player = relationship("Player", foreign_keys=[wicket_player_id])
    fielder = relationship("Player", foreign_keys=[fielder_id])
    
    # Critical indexes for fast scoring
    __table_args__ = (
        Index('idx_innings_ball_sequence', 'innings_id', 'over_number', 'ball_number'),
        Index('idx_batsman_balls', 'batsman_id'),
        Index('idx_bowler_balls', 'bowler_id'),
    )
