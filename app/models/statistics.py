"""
Statistics and analytics models for tracking player and team performance
Provides comprehensive career stats, trends, and comparative analytics
"""
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.utils.database import Base


class PlayerCareerStats(Base):
    """Comprehensive career statistics for a player"""
    __tablename__ = "player_career_stats"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)
    
    # Batting Statistics
    total_matches = Column(Integer, default=0)
    innings_batted = Column(Integer, default=0)
    runs_scored = Column(Integer, default=0)
    highest_score = Column(Integer, default=0)
    balls_faced = Column(Integer, default=0)
    fours_hit = Column(Integer, default=0)
    sixes_hit = Column(Integer, default=0)
    times_out = Column(Integer, default=0)
    times_not_out = Column(Integer, default=0)
    
    # Bowling Statistics  
    innings_bowled = Column(Integer, default=0)
    overs_bowled = Column(Numeric(5, 1), default=0)
    runs_conceded = Column(Integer, default=0)
    wickets_taken = Column(Integer, default=0)
    best_bowling_figures = Column(String(10), nullable=True)  # e.g., "5/23"
    maidens_bowled = Column(Integer, default=0)
    
    # Fielding Statistics
    catches_taken = Column(Integer, default=0)
    stumpings_made = Column(Integer, default=0)
    run_outs_effected = Column(Integer, default=0)
    
    # Calculated Metrics (updated periodically)
    batting_average = Column(Numeric(6, 2), default=0)
    batting_strike_rate = Column(Numeric(6, 2), default=0)
    bowling_average = Column(Numeric(6, 2), default=0)
    bowling_strike_rate = Column(Numeric(6, 2), default=0)
    bowling_economy_rate = Column(Numeric(4, 2), default=0)
    
    # Tournament Performance
    tournaments_played = Column(Integer, default=0)
    tournament_wins = Column(Integer, default=0)
    man_of_match_awards = Column(Integer, default=0)
    
    # System fields
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="career_stats")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_career_stats_batting_avg', 'batting_average'),
        Index('idx_career_stats_bowling_avg', 'bowling_average'),
        Index('idx_career_stats_runs', 'runs_scored'),
        Index('idx_career_stats_wickets', 'wickets_taken'),
    )


class PlayerMatchPerformance(Base):
    """Individual match performance for detailed analytics"""
    __tablename__ = "player_match_performances"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    match_id = Column(UUID(as_uuid=True), ForeignKey("cricket_matches.id"), nullable=False)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)
    
    # Match Context
    match_date = Column(DateTime(timezone=True), nullable=False)
    tournament_id = Column(UUID(as_uuid=True), ForeignKey("tournaments.id"), nullable=True)
    venue = Column(String(200), nullable=True)
    match_type = Column(String(50), default="T20")  # T20, ODI, Test, etc.
    
    # Batting Performance
    batted = Column(Boolean, default=False)
    batting_position = Column(Integer, nullable=True)
    runs_scored = Column(Integer, default=0)
    balls_faced = Column(Integer, default=0)
    fours_hit = Column(Integer, default=0)
    sixes_hit = Column(Integer, default=0)
    dismissal_type = Column(String(50), nullable=True)  # bowled, caught, lbw, etc.
    dismissed_by_player_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Bowling Performance
    bowled = Column(Boolean, default=False)
    overs_bowled = Column(Numeric(3, 1), default=0)
    runs_conceded = Column(Integer, default=0)
    wickets_taken = Column(Integer, default=0)
    maidens_bowled = Column(Integer, default=0)
    wides_bowled = Column(Integer, default=0)
    no_balls_bowled = Column(Integer, default=0)
    
    # Fielding Performance
    catches_taken = Column(Integer, default=0)
    stumpings_made = Column(Integer, default=0)
    run_outs_effected = Column(Integer, default=0)
    
    # Performance Ratings (calculated)
    batting_points = Column(Numeric(5, 2), default=0)
    bowling_points = Column(Numeric(5, 2), default=0)
    fielding_points = Column(Numeric(5, 2), default=0)
    overall_rating = Column(Numeric(5, 2), default=0)
    
    # Awards and Recognition
    man_of_match = Column(Boolean, default=False)
    
    # System fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")
    match = relationship("CricketMatch")
    team = relationship("Team")
    tournament = relationship("Tournament", foreign_keys=[tournament_id])
    dismissed_by = relationship("User", foreign_keys=[dismissed_by_player_id])
    
    # Indexes for analytics queries
    __table_args__ = (
        Index('idx_performance_user_match', 'user_id', 'match_id'),
        Index('idx_performance_tournament', 'tournament_id', 'match_date'),
        Index('idx_performance_ratings', 'overall_rating', 'match_date'),
        Index('idx_performance_user_date', 'user_id', 'match_date'),
    )


class TeamSeasonStats(Base):
    """Team performance statistics for a specific season/tournament"""
    __tablename__ = "team_season_stats"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)
    tournament_id = Column(UUID(as_uuid=True), ForeignKey("tournaments.id"), nullable=True)
    season_year = Column(Integer, nullable=False)
    
    # Match Statistics
    matches_played = Column(Integer, default=0)
    matches_won = Column(Integer, default=0)
    matches_lost = Column(Integer, default=0)
    matches_tied = Column(Integer, default=0)
    matches_no_result = Column(Integer, default=0)
    
    # Batting Team Statistics
    total_runs_scored = Column(Integer, default=0)
    total_balls_faced = Column(Integer, default=0)
    highest_team_score = Column(Integer, default=0)
    lowest_team_score = Column(Integer, default=0)
    total_fours_hit = Column(Integer, default=0)
    total_sixes_hit = Column(Integer, default=0)
    
    # Bowling Team Statistics
    total_runs_conceded = Column(Integer, default=0)
    total_overs_bowled = Column(Numeric(6, 1), default=0)
    total_wickets_taken = Column(Integer, default=0)
    best_bowling_figures = Column(String(10), nullable=True)
    total_maidens = Column(Integer, default=0)
    
    # Fielding Statistics
    total_catches = Column(Integer, default=0)
    total_stumpings = Column(Integer, default=0)
    total_run_outs = Column(Integer, default=0)
    
    # Performance Metrics
    team_batting_average = Column(Numeric(6, 2), default=0)
    team_bowling_average = Column(Numeric(6, 2), default=0)
    team_strike_rate = Column(Numeric(6, 2), default=0)
    team_economy_rate = Column(Numeric(4, 2), default=0)
    win_percentage = Column(Numeric(5, 2), default=0)
    
    # Tournament specific
    tournament_position = Column(Integer, nullable=True)
    points_earned = Column(Integer, default=0)
    
    # System fields
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    team = relationship("Team")
    tournament = relationship("Tournament")
    
    # Indexes
    __table_args__ = (
        Index('idx_team_season_lookup', 'team_id', 'season_year'),
        Index('idx_team_tournament_stats', 'tournament_id', 'win_percentage'),
        Index('idx_team_performance_ranking', 'season_year', 'win_percentage'),
    )


class PlayerPerformanceTrend(Base):
    """Track player performance trends over time"""
    __tablename__ = "player_performance_trends"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Time Period
    period_type = Column(String(20), nullable=False)  # monthly, quarterly, yearly
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    
    # Aggregated Statistics for Period
    matches_played = Column(Integer, default=0)
    runs_scored = Column(Integer, default=0)
    wickets_taken = Column(Integer, default=0)
    batting_average = Column(Numeric(6, 2), default=0)
    bowling_average = Column(Numeric(6, 2), default=0)
    strike_rate = Column(Numeric(6, 2), default=0)
    
    # Performance Indicators
    form_rating = Column(Numeric(4, 2), default=0)  # 0-10 scale
    consistency_score = Column(Numeric(4, 2), default=0)  # 0-10 scale
    improvement_factor = Column(Numeric(5, 2), default=0)  # % change from previous period
    
    # Milestone Achievements
    centuries_scored = Column(Integer, default=0)
    half_centuries_scored = Column(Integer, default=0)
    five_wicket_hauls = Column(Integer, default=0)
    
    # System fields
    calculated_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")
    
    # Indexes
    __table_args__ = (
        Index('idx_trends_user_period', 'user_id', 'period_type', 'period_start'),
        Index('idx_trends_form_rating', 'form_rating', 'period_end'),
    )


class Leaderboard(Base):
    """Dynamic leaderboards for various statistical categories"""
    __tablename__ = "leaderboards"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Leaderboard Configuration
    category = Column(String(50), nullable=False)  # batting_avg, bowling_avg, runs, wickets, etc.
    scope = Column(String(50), nullable=False)  # all_time, season, tournament, monthly
    scope_id = Column(UUID(as_uuid=True), nullable=True)  # tournament_id for tournament scope
    
    # Leaderboard Entry
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    position = Column(Integer, nullable=False)
    value = Column(Numeric(10, 2), nullable=False)
    
    # Additional Context
    matches_qualification = Column(Integer, default=0)  # minimum matches for qualification
    last_match_date = Column(DateTime(timezone=True), nullable=True)
    
    # System fields
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")
    
    # Indexes for leaderboard queries
    __table_args__ = (
        Index('idx_leaderboard_category_scope', 'category', 'scope', 'position'),
        Index('idx_leaderboard_user_category', 'user_id', 'category'),
        Index('idx_leaderboard_scope_ranking', 'scope', 'scope_id', 'position'),
    )


class PlayerComparison(Base):
    """Store player comparison data for analytics"""
    __tablename__ = "player_comparisons"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Players being compared
    player1_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    player2_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Comparison Scope
    comparison_type = Column(String(50), nullable=False)  # head_to_head, career, tournament
    scope_id = Column(UUID(as_uuid=True), nullable=True)  # tournament_id if tournament comparison
    
    # Head-to-Head Statistics
    player1_wins = Column(Integer, default=0)
    player2_wins = Column(Integer, default=0)
    matches_together = Column(Integer, default=0)
    
    # Performance Metrics Comparison
    player1_avg_score = Column(Numeric(6, 2), default=0)
    player2_avg_score = Column(Numeric(6, 2), default=0)
    player1_avg_wickets = Column(Numeric(4, 2), default=0)
    player2_avg_wickets = Column(Numeric(4, 2), default=0)
    
    # Additional Analytics
    dominance_factor = Column(Numeric(4, 2), default=0)  # which player performs better
    performance_gap = Column(Numeric(6, 2), default=0)  # statistical difference
    
    # System fields
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    player1 = relationship("User", foreign_keys=[player1_id])
    player2 = relationship("User", foreign_keys=[player2_id])
    
    # Indexes
    __table_args__ = (
        Index('idx_comparison_players', 'player1_id', 'player2_id'),
        Index('idx_comparison_type_scope', 'comparison_type', 'scope_id'),
    )