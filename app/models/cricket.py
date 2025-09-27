"""
Cricket Models

Core models for cricket scoring system including matches, innings, overs, balls, and players
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List
from sqlalchemy import (
    String, Integer, Boolean, DateTime, Text, ForeignKey, 
    Numeric, JSON, CheckConstraint, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.hybrid import hybrid_property

from .base import BaseModel


class MatchFormat(str, Enum):
    """Cricket match formats"""
    T20 = "T20"
    ODI = "ODI"
    TEST = "TEST"
    T10 = "T10"
    HUNDRED = "HUNDRED"


class MatchStatus(str, Enum):
    """Match status enumeration"""
    SCHEDULED = "SCHEDULED"
    LIVE = "LIVE"
    COMPLETED = "COMPLETED"
    ABANDONED = "ABANDONED"
    CANCELLED = "CANCELLED"
    SUSPENDED = "SUSPENDED"


class InningsStatus(str, Enum):
    """Innings status enumeration"""
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    DECLARED = "DECLARED"
    FORFEITED = "FORFEITED"


class DismissalType(str, Enum):
    """Types of dismissals in cricket"""
    BOWLED = "BOWLED"
    CAUGHT = "CAUGHT"
    LBW = "LBW"
    RUN_OUT = "RUN_OUT"
    STUMPED = "STUMPED"
    HIT_WICKET = "HIT_WICKET"
    OBSTRUCTING_FIELD = "OBSTRUCTING_FIELD"
    HANDLING_BALL = "HANDLING_BALL"
    TIMED_OUT = "TIMED_OUT"
    RETIRED_HURT = "RETIRED_HURT"
    RETIRED_OUT = "RETIRED_OUT"


class ExtraType(str, Enum):
    """Types of extras in cricket"""
    WIDE = "WIDE"
    NO_BALL = "NO_BALL"
    BYE = "BYE"  
    LEG_BYE = "LEG_BYE"
    PENALTY = "PENALTY"


class Team(BaseModel):
    """Cricket team model"""
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    short_name: Mapped[str] = mapped_column(String(10), nullable=False)
    logo_url: Mapped[Optional[str]] = mapped_column(String(500))
    home_ground: Mapped[Optional[str]] = mapped_column(String(200))
    captain_id: Mapped[Optional[int]] = mapped_column(ForeignKey("players.id"))
    
    # Relationships
    players = relationship("Player", foreign_keys="Player.team_id", back_populates="team")
    captain = relationship("Player", foreign_keys="Team.captain_id", post_update=True)
    home_matches = relationship("Match", foreign_keys="Match.home_team_id", back_populates="home_team")
    away_matches = relationship("Match", foreign_keys="Match.away_team_id", back_populates="away_team")


class Player(BaseModel):
    """Cricket player model"""
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    team_id: Mapped[Optional[int]] = mapped_column(ForeignKey("teams.id"))
    jersey_number: Mapped[Optional[int]] = mapped_column(Integer)
    role: Mapped[Optional[str]] = mapped_column(String(50))  # Batsman, Bowler, All-rounder, Wicket-keeper
    batting_style: Mapped[Optional[str]] = mapped_column(String(50))  # Right-handed, Left-handed
    bowling_style: Mapped[Optional[str]] = mapped_column(String(50))  # Right-arm fast, Left-arm spin, etc.
    date_of_birth: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    team = relationship("Team", foreign_keys="Player.team_id", back_populates="players")
    batting_performances = relationship("BattingPerformance", foreign_keys="BattingPerformance.player_id", back_populates="player")
    bowling_performances = relationship("BowlingPerformance", foreign_keys="BowlingPerformance.player_id", back_populates="player")


class Match(BaseModel):
    """Cricket match model"""
    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    match_format: Mapped[MatchFormat] = mapped_column(String(20), nullable=False)
    status: Mapped[MatchStatus] = mapped_column(String(20), default=MatchStatus.SCHEDULED)
    
    # Teams
    home_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    away_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False) 
    
    # Match details
    venue: Mapped[Optional[str]] = mapped_column(String(200))
    scheduled_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    actual_start: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    actual_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Match configuration
    overs_per_innings: Mapped[int] = mapped_column(Integer, default=20)
    balls_per_over: Mapped[int] = mapped_column(Integer, default=6)
    max_wickets: Mapped[int] = mapped_column(Integer, default=10)
    
    # Toss details
    toss_winner_id: Mapped[Optional[int]] = mapped_column(ForeignKey("teams.id"))
    toss_decision: Mapped[Optional[str]] = mapped_column(String(10))  # BAT, BOWL
    
    # Match result
    winner_id: Mapped[Optional[int]] = mapped_column(ForeignKey("teams.id"))
    result_type: Mapped[Optional[str]] = mapped_column(String(50))  # Won by X runs, Won by X wickets, Tie, No Result
    margin: Mapped[Optional[int]] = mapped_column(Integer)  # Runs or wickets margin
    
    # Dual scoring integrity
    dual_scorer_required: Mapped[bool] = mapped_column(Boolean, default=True)
    primary_scorer_id: Mapped[Optional[str]] = mapped_column(String(100))  # User ID
    secondary_scorer_id: Mapped[Optional[str]] = mapped_column(String(100))  # User ID
    
    # Additional metadata
    weather_conditions: Mapped[Optional[str]] = mapped_column(String(200))
    pitch_conditions: Mapped[Optional[str]] = mapped_column(String(200))
    match_notes: Mapped[Optional[str]] = mapped_column(Text)
    
    # Relationships
    home_team = relationship("Team", foreign_keys=[home_team_id])
    away_team = relationship("Team", foreign_keys=[away_team_id])
    toss_winner = relationship("Team", foreign_keys=[toss_winner_id])
    winner = relationship("Team", foreign_keys=[winner_id])
    innings = relationship("Innings", back_populates="match", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        CheckConstraint('home_team_id != away_team_id', name='different_teams'),
        CheckConstraint('overs_per_innings > 0', name='positive_overs'),
        CheckConstraint('balls_per_over > 0', name='positive_balls_per_over'),
        CheckConstraint('max_wickets > 0', name='positive_max_wickets'),
    )


class Innings(BaseModel):
    """Cricket innings model"""
    __tablename__ = "innings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id"), nullable=False)
    innings_number: Mapped[int] = mapped_column(Integer, nullable=False)  # 1, 2, 3, 4 for Test matches
    batting_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    bowling_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    
    # Innings status and timing
    status: Mapped[InningsStatus] = mapped_column(String(20), default=InningsStatus.NOT_STARTED)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Scoring summary
    total_runs: Mapped[int] = mapped_column(Integer, default=0)
    total_wickets: Mapped[int] = mapped_column(Integer, default=0)
    total_overs: Mapped[Numeric] = mapped_column(Numeric(4, 1), default=0.0)  # e.g., 18.4 overs
    total_balls: Mapped[int] = mapped_column(Integer, default=0)
    
    # Extras breakdown
    wides: Mapped[int] = mapped_column(Integer, default=0)
    no_balls: Mapped[int] = mapped_column(Integer, default=0)
    byes: Mapped[int] = mapped_column(Integer, default=0)
    leg_byes: Mapped[int] = mapped_column(Integer, default=0)
    penalties: Mapped[int] = mapped_column(Integer, default=0)
    
    # Target and result
    target_runs: Mapped[Optional[int]] = mapped_column(Integer)  # For chasing team
    is_declared: Mapped[bool] = mapped_column(Boolean, default=False)
    is_forfeited: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Relationships
    match = relationship("Match", back_populates="innings")
    batting_team = relationship("Team", foreign_keys=[batting_team_id])
    bowling_team = relationship("Team", foreign_keys=[bowling_team_id])
    overs = relationship("Over", back_populates="innings", cascade="all, delete-orphan")
    batting_performances = relationship("BattingPerformance", back_populates="innings")
    bowling_performances = relationship("BowlingPerformance", back_populates="innings")

    # Constraints
    __table_args__ = (
        UniqueConstraint('match_id', 'innings_number', name='unique_innings_per_match'),
        CheckConstraint('total_runs >= 0', name='non_negative_runs'),
        CheckConstraint('total_wickets >= 0', name='non_negative_wickets'),
        CheckConstraint('total_overs >= 0', name='non_negative_overs'),
        CheckConstraint('innings_number > 0', name='positive_innings_number'),
    )

    @hybrid_property
    def total_extras(self) -> int:
        """Calculate total extras"""
        return self.wides + self.no_balls + self.byes + self.leg_byes + self.penalties

    @hybrid_property
    def current_over(self) -> int:
        """Get current over number"""
        return int(self.total_overs) + 1 if self.total_balls % 6 != 0 or self.total_balls == 0 else int(self.total_overs)

    @hybrid_property
    def current_ball_in_over(self) -> int:
        """Get current ball in over (1-6)"""
        ball_in_over = self.total_balls % 6
        return 6 if ball_in_over == 0 and self.total_balls > 0 else ball_in_over


class Over(BaseModel):
    """Cricket over model"""
    __tablename__ = "overs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    innings_id: Mapped[int] = mapped_column(ForeignKey("innings.id"), nullable=False)
    over_number: Mapped[int] = mapped_column(Integer, nullable=False)
    bowler_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False)
    
    # Over summary
    runs_conceded: Mapped[int] = mapped_column(Integer, default=0)
    wickets_taken: Mapped[int] = mapped_column(Integer, default=0)
    balls_bowled: Mapped[int] = mapped_column(Integer, default=0)  # Excluding wides and no-balls
    legal_balls: Mapped[int] = mapped_column(Integer, default=0)   # Valid deliveries
    
    # Extras in this over
    wides: Mapped[int] = mapped_column(Integer, default=0)
    no_balls: Mapped[int] = mapped_column(Integer, default=0)
    byes: Mapped[int] = mapped_column(Integer, default=0)
    leg_byes: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relationships
    innings = relationship("Innings", back_populates="overs")
    bowler = relationship("Player")
    balls = relationship("Ball", back_populates="over", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        UniqueConstraint('innings_id', 'over_number', name='unique_over_per_innings'),
        CheckConstraint('over_number > 0', name='positive_over_number'),
        CheckConstraint('runs_conceded >= 0', name='non_negative_runs_conceded'),
        CheckConstraint('wickets_taken >= 0', name='non_negative_wickets_taken'),
        CheckConstraint('balls_bowled >= 0', name='non_negative_balls_bowled'),
        CheckConstraint('legal_balls >= 0', name='non_negative_legal_balls'),
    )


class Ball(BaseModel):
    """Individual ball/delivery model"""
    __tablename__ = "balls"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    over_id: Mapped[int] = mapped_column(ForeignKey("overs.id"), nullable=False)
    ball_number: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-6 (or more for extras)
    
    # Ball details
    bowler_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False)
    batsman_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False)
    non_striker_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False)
    
    # Scoring
    runs_scored: Mapped[int] = mapped_column(Integer, default=0)
    is_boundary: Mapped[bool] = mapped_column(Boolean, default=False)
    boundary_type: Mapped[Optional[int]] = mapped_column(Integer)  # 4 or 6
    
    # Extras
    extra_type: Mapped[Optional[ExtraType]] = mapped_column(String(20))
    extra_runs: Mapped[int] = mapped_column(Integer, default=0)
    is_legal_delivery: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Wicket details
    is_wicket: Mapped[bool] = mapped_column(Boolean, default=False)
    dismissal_type: Mapped[Optional[DismissalType]] = mapped_column(String(30))
    dismissed_player_id: Mapped[Optional[int]] = mapped_column(ForeignKey("players.id"))
    fielder_id: Mapped[Optional[int]] = mapped_column(ForeignKey("players.id"))  # For catches, run-outs
    
    # Ball tracking (optional advanced features)
    ball_speed: Mapped[Optional[Numeric]] = mapped_column(Numeric(5, 2))  # km/h
    ball_type: Mapped[Optional[str]] = mapped_column(String(50))  # Fast, Spin, etc.
    
    # Dual scoring verification
    primary_scorer_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    secondary_scorer_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    has_dispute: Mapped[bool] = mapped_column(Boolean, default=False)
    dispute_resolved: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relationships
    over = relationship("Over", back_populates="balls")
    bowler = relationship("Player", foreign_keys=[bowler_id])
    batsman = relationship("Player", foreign_keys=[batsman_id])
    non_striker = relationship("Player", foreign_keys=[non_striker_id])
    dismissed_player = relationship("Player", foreign_keys=[dismissed_player_id])
    fielder = relationship("Player", foreign_keys=[fielder_id])

    # Constraints
    __table_args__ = (
        CheckConstraint('runs_scored >= 0', name='non_negative_runs_scored'),
        CheckConstraint('extra_runs >= 0', name='non_negative_extra_runs'),
        CheckConstraint('ball_number > 0', name='positive_ball_number'),
        CheckConstraint(
            '(is_wicket = false AND dismissal_type IS NULL AND dismissed_player_id IS NULL) OR '
            '(is_wicket = true AND dismissal_type IS NOT NULL)',
            name='consistent_wicket_info'
        ),
        CheckConstraint(
            '(is_boundary = false AND boundary_type IS NULL) OR '
            '(is_boundary = true AND boundary_type IN (4, 6))',
            name='consistent_boundary_info'
        ),
    )

    @hybrid_property
    def total_runs(self) -> int:
        """Total runs for this ball (runs + extras)"""
        return self.runs_scored + self.extra_runs

    def to_score_string(self) -> str:
        """Convert ball to cricket scoring notation"""
        if not self.is_legal_delivery:
            if self.extra_type == ExtraType.WIDE:
                return f"Wd+{self.runs_scored}" if self.runs_scored > 0 else "Wd"
            elif self.extra_type == ExtraType.NO_BALL:
                return f"Nb+{self.runs_scored}" if self.runs_scored > 0 else "Nb"
        
        if self.is_wicket:
            return "W"
        elif self.is_boundary:
            return str(self.boundary_type)
        else:
            return str(self.runs_scored)


class BattingPerformance(BaseModel):
    """Individual batting performance in an innings"""
    __tablename__ = "batting_performances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    innings_id: Mapped[int] = mapped_column(ForeignKey("innings.id"), nullable=False)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False)
    
    # Batting statistics
    runs_scored: Mapped[int] = mapped_column(Integer, default=0)
    balls_faced: Mapped[int] = mapped_column(Integer, default=0)
    fours: Mapped[int] = mapped_column(Integer, default=0)
    sixes: Mapped[int] = mapped_column(Integer, default=0)
    
    # Dismissal details
    is_out: Mapped[bool] = mapped_column(Boolean, default=False)
    dismissal_type: Mapped[Optional[DismissalType]] = mapped_column(String(30))
    bowler_id: Mapped[Optional[int]] = mapped_column(ForeignKey("players.id"))  # Bowler who took wicket
    fielder_id: Mapped[Optional[int]] = mapped_column(ForeignKey("players.id"))  # Fielder involved
    
    # Batting order
    batting_position: Mapped[int] = mapped_column(Integer, nullable=False)
    came_in_at_over: Mapped[Optional[Numeric]] = mapped_column(Numeric(4, 1))
    went_out_at_over: Mapped[Optional[Numeric]] = mapped_column(Numeric(4, 1))
    
    # Relationships
    innings = relationship("Innings", back_populates="batting_performances")
    player = relationship("Player", foreign_keys=[player_id], back_populates="batting_performances")
    bowler = relationship("Player", foreign_keys=[bowler_id])
    fielder = relationship("Player", foreign_keys=[fielder_id])
    fielder = relationship("Player", foreign_keys=[fielder_id])

    # Constraints
    __table_args__ = (
        UniqueConstraint('innings_id', 'player_id', name='unique_batting_performance'),
        UniqueConstraint('innings_id', 'batting_position', name='unique_batting_position'),
        CheckConstraint('runs_scored >= 0', name='non_negative_runs_scored'),
        CheckConstraint('balls_faced >= 0', name='non_negative_balls_faced'),
        CheckConstraint('fours >= 0', name='non_negative_fours'),
        CheckConstraint('sixes >= 0', name='non_negative_sixes'),
        CheckConstraint('batting_position > 0', name='positive_batting_position'),
    )

    @hybrid_property
    def strike_rate(self) -> Optional[float]:
        """Calculate strike rate"""
        if self.balls_faced == 0:
            return None
        return (self.runs_scored / self.balls_faced) * 100


class BowlingPerformance(BaseModel):
    """Individual bowling performance in an innings"""
    __tablename__ = "bowling_performances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    innings_id: Mapped[int] = mapped_column(ForeignKey("innings.id"), nullable=False)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False)
    
    # Bowling statistics
    overs_bowled: Mapped[Numeric] = mapped_column(Numeric(4, 1), default=0.0)
    runs_conceded: Mapped[int] = mapped_column(Integer, default=0)
    wickets_taken: Mapped[int] = mapped_column(Integer, default=0)
    maidens: Mapped[int] = mapped_column(Integer, default=0)
    
    # Extras conceded
    wides: Mapped[int] = mapped_column(Integer, default=0)
    no_balls: Mapped[int] = mapped_column(Integer, default=0)
    
    # Additional stats
    dots: Mapped[int] = mapped_column(Integer, default=0)  # Dot balls
    boundaries_conceded: Mapped[int] = mapped_column(Integer, default=0)
    sixes_conceded: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relationships
    innings = relationship("Innings", back_populates="bowling_performances")
    player = relationship("Player", foreign_keys=[player_id], back_populates="bowling_performances")

    # Constraints
    __table_args__ = (
        UniqueConstraint('innings_id', 'player_id', name='unique_bowling_performance'),
        CheckConstraint('overs_bowled >= 0', name='non_negative_overs_bowled'),
        CheckConstraint('runs_conceded >= 0', name='non_negative_runs_conceded'),
        CheckConstraint('wickets_taken >= 0', name='non_negative_wickets_taken'),
        CheckConstraint('maidens >= 0', name='non_negative_maidens'),
        CheckConstraint('wides >= 0', name='non_negative_wides'),
        CheckConstraint('no_balls >= 0', name='non_negative_no_balls'),
    )

    @hybrid_property
    def economy_rate(self) -> Optional[float]:
        """Calculate economy rate"""
        if self.overs_bowled == 0:
            return None
        return self.runs_conceded / float(self.overs_bowled)

    @hybrid_property
    def bowling_average(self) -> Optional[float]:
        """Calculate bowling average"""
        if self.wickets_taken == 0:
            return None
        return self.runs_conceded / self.wickets_taken

    @hybrid_property
    def strike_rate(self) -> Optional[float]:
        """Calculate bowling strike rate (balls per wicket)"""
        if self.wickets_taken == 0:
            return None
        balls_bowled = float(self.overs_bowled) * 6
        return balls_bowled / self.wickets_taken