"""
Statistics schemas for API request/response models
Provides comprehensive analytics and performance tracking
"""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.user import UserResponse


class PlayerCareerStatsResponse(BaseModel):
    """Player career statistics response"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    user_id: uuid.UUID
    
    # Batting Statistics
    total_matches: int
    innings_batted: int
    runs_scored: int
    highest_score: int
    balls_faced: int
    fours_hit: int
    sixes_hit: int
    times_out: int
    times_not_out: int
    
    # Bowling Statistics
    innings_bowled: int
    overs_bowled: Decimal
    runs_conceded: int
    wickets_taken: int
    best_bowling_figures: Optional[str]
    maidens_bowled: int
    
    # Fielding Statistics
    catches_taken: int
    stumpings_made: int
    run_outs_effected: int
    
    # Calculated Metrics
    batting_average: Decimal
    batting_strike_rate: Decimal
    bowling_average: Decimal
    bowling_strike_rate: Decimal
    bowling_economy_rate: Decimal
    
    # Tournament Performance
    tournaments_played: int
    tournament_wins: int
    man_of_match_awards: int
    
    last_updated: datetime
    user: Optional[UserResponse] = None


class PlayerMatchPerformanceResponse(BaseModel):
    """Individual match performance response"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    user_id: uuid.UUID
    match_id: uuid.UUID
    team_id: uuid.UUID
    match_date: datetime
    venue: Optional[str]
    match_type: str
    
    # Batting Performance
    batted: bool
    batting_position: Optional[int]
    runs_scored: int
    balls_faced: int
    fours_hit: int
    sixes_hit: int
    dismissal_type: Optional[str]
    
    # Bowling Performance
    bowled: bool
    overs_bowled: Decimal
    runs_conceded: int
    wickets_taken: int
    maidens_bowled: int
    
    # Fielding Performance
    catches_taken: int
    stumpings_made: int
    run_outs_effected: int
    
    # Performance Ratings
    batting_points: Decimal
    bowling_points: Decimal
    fielding_points: Decimal
    overall_rating: Decimal
    man_of_match: bool
    
    user: Optional[UserResponse] = None


class TeamSeasonStatsResponse(BaseModel):
    """Team season statistics response"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    team_id: uuid.UUID
    tournament_id: Optional[uuid.UUID]
    season_year: int
    
    # Match Statistics
    matches_played: int
    matches_won: int
    matches_lost: int
    matches_tied: int
    matches_no_result: int
    
    # Performance Metrics
    team_batting_average: Decimal
    team_bowling_average: Decimal
    team_strike_rate: Decimal
    team_economy_rate: Decimal
    win_percentage: Decimal
    
    # Tournament specific
    tournament_position: Optional[int]
    points_earned: int
    
    last_updated: datetime


class PlayerPerformanceTrendResponse(BaseModel):
    """Player performance trend response"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    user_id: uuid.UUID
    period_type: str
    period_start: datetime
    period_end: datetime
    
    # Performance Data
    matches_played: int
    runs_scored: int
    wickets_taken: int
    batting_average: Decimal
    bowling_average: Decimal
    strike_rate: Decimal
    
    # Performance Indicators
    form_rating: Decimal
    consistency_score: Decimal
    improvement_factor: Decimal
    
    # Milestones
    centuries_scored: int
    half_centuries_scored: int
    five_wicket_hauls: int
    
    calculated_at: datetime


class LeaderboardEntry(BaseModel):
    """Leaderboard entry response"""
    model_config = ConfigDict(from_attributes=True)
    
    position: int
    user_id: uuid.UUID
    value: Decimal
    matches_qualification: int
    last_match_date: Optional[datetime]
    user: Optional[UserResponse] = None


class LeaderboardResponse(BaseModel):
    """Complete leaderboard response"""
    category: str
    scope: str
    scope_id: Optional[uuid.UUID]
    last_updated: datetime
    entries: List[LeaderboardEntry]


class PlayerComparisonResponse(BaseModel):
    """Player comparison response"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    player1_id: uuid.UUID
    player2_id: uuid.UUID
    comparison_type: str
    scope_id: Optional[uuid.UUID]
    
    # Head-to-Head
    player1_wins: int
    player2_wins: int
    matches_together: int
    
    # Performance Comparison
    player1_avg_score: Decimal
    player2_avg_score: Decimal
    player1_avg_wickets: Decimal
    player2_avg_wickets: Decimal
    
    # Analytics
    dominance_factor: Decimal
    performance_gap: Decimal
    
    last_updated: datetime
    player1: Optional[UserResponse] = None
    player2: Optional[UserResponse] = None


class StatsFilterRequest(BaseModel):
    """Request model for filtering statistics"""
    tournament_id: Optional[uuid.UUID] = None
    season_year: Optional[int] = None
    team_id: Optional[uuid.UUID] = None
    match_type: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    min_matches: int = Field(default=0, ge=0)


class LeaderboardRequest(BaseModel):
    """Request model for leaderboard queries"""
    category: str = Field(..., pattern="^(batting_avg|bowling_avg|runs|wickets|strike_rate|economy_rate)$")
    scope: str = Field(..., pattern="^(all_time|season|tournament|monthly)$")
    scope_id: Optional[uuid.UUID] = None
    limit: int = Field(default=20, ge=1, le=100)
    min_matches: int = Field(default=5, ge=0)


class PlayerComparisonRequest(BaseModel):
    """Request model for player comparisons"""
    player1_id: uuid.UUID
    player2_id: uuid.UUID
    comparison_type: str = Field(..., pattern="^(head_to_head|career|tournament)$")
    scope_id: Optional[uuid.UUID] = None


class CareerMilestone(BaseModel):
    """Career milestone achievement"""
    milestone_type: str
    description: str
    achieved_date: datetime
    match_id: Optional[uuid.UUID]
    value: Optional[int]


class PlayerCareerSummary(BaseModel):
    """Comprehensive player career summary"""
    user_id: uuid.UUID
    user: UserResponse
    career_stats: PlayerCareerStatsResponse
    recent_form: List[PlayerMatchPerformanceResponse]
    performance_trends: List[PlayerPerformanceTrendResponse]
    milestones: List[CareerMilestone]
    rankings: List[LeaderboardEntry]


class TeamAnalytics(BaseModel):
    """Comprehensive team analytics"""
    team_id: uuid.UUID
    season_stats: List[TeamSeasonStatsResponse]
    top_performers: List[PlayerCareerStatsResponse]
    recent_matches: List[PlayerMatchPerformanceResponse]
    win_loss_trend: List[dict]  # {date, wins, losses}
    performance_metrics: dict