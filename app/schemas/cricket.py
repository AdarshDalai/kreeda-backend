from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
import uuid

from app.schemas.team import TeamSummary
from app.schemas.user import UserResponse


class CricketMatchBase(BaseModel):
    team_a_id: uuid.UUID
    team_b_id: uuid.UUID
    overs_per_innings: int = Field(20, ge=1, le=50)
    venue: str = Field(..., min_length=1, max_length=200)
    match_date: datetime


class CricketMatchCreate(CricketMatchBase):
    pass


class CricketMatchUpdate(BaseModel):
    venue: Optional[str] = Field(None, min_length=1, max_length=200)
    match_date: Optional[datetime] = None
    overs_per_innings: Optional[int] = Field(None, ge=1, le=50)


class TossResult(BaseModel):
    toss_winner_id: uuid.UUID
    toss_decision: str = Field(..., pattern="^(bat|bowl)$")


class BallRecord(BaseModel):
    over_number: int = Field(..., ge=1)
    ball_number: int = Field(..., ge=1, le=10)  # Can be more due to extras
    bowler_id: uuid.UUID
    batsman_striker_id: uuid.UUID
    batsman_non_striker_id: uuid.UUID
    runs_scored: int = Field(0, ge=0, le=6)
    extras: int = Field(0, ge=0)
    ball_type: str = Field("legal", pattern="^(legal|wide|no_ball|bye|leg_bye)$")
    is_wicket: bool = False
    wicket_type: Optional[str] = Field(None, pattern="^(bowled|caught|lbw|run_out|stumped)$")
    dismissed_player_id: Optional[uuid.UUID] = None
    is_boundary: bool = False
    boundary_type: Optional[str] = Field(None, pattern="^(four|six)$")


class BallResponse(BallRecord):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    match_id: uuid.UUID
    innings: int
    created_at: datetime


class ScorerAssignment(BaseModel):
    """Schema for assigning scorers to a match"""
    team_a_scorer_id: uuid.UUID = Field(..., description="User ID for Team A scorer")
    team_b_scorer_id: uuid.UUID = Field(..., description="User ID for Team B scorer")  
    umpire_id: Optional[uuid.UUID] = Field(None, description="Optional umpire/referee user ID")
    
    id: uuid.UUID
    match_id: uuid.UUID
    innings: int
    created_at: datetime


class PlayerStats(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    player_id: uuid.UUID
    player: UserResponse
    team_id: uuid.UUID
    
    # Batting
    batting_runs: int
    balls_faced: int
    fours_hit: int
    sixes_hit: int
    is_out: bool
    
    # Bowling
    overs_bowled: float
    runs_conceded: int
    wickets_taken: int


class Scorecard(BaseModel):
    team_a: dict
    team_b: dict
    current_partnership: int
    required_run_rate: Optional[float] = None
    balls_remaining: Optional[int] = None


class CricketMatchResponse(CricketMatchBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    created_by_id: uuid.UUID
    status: str
    current_innings: int
    
    # Toss
    toss_winner_id: Optional[uuid.UUID] = None
    toss_decision: Optional[str] = None
    
    # Live scores
    team_a_score: int
    team_a_wickets: int
    team_a_overs: float
    
    team_b_score: int
    team_b_wickets: int
    team_b_overs: float
    
    # Result
    winner_team_id: Optional[uuid.UUID] = None
    result_description: Optional[str] = None
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    
    # Relationships
    team_a: TeamSummary
    team_b: TeamSummary
    creator: UserResponse


class MatchSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    team_a: TeamSummary
    team_b: TeamSummary
    venue: str
    match_date: datetime
    status: str
    
    # Quick scores
    team_a_score: int
    team_a_wickets: int
    team_a_overs: float
    
    team_b_score: int
    team_b_wickets: int
    team_b_overs: float
    
    winner_team_id: Optional[uuid.UUID] = None
    result_description: Optional[str] = None


# Basic response schema for API endpoints without relationship loading
class MatchResponseBasic(BaseModel):
    """Basic match response without relationship data to prevent async loading issues"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    team_a_id: uuid.UUID
    team_b_id: uuid.UUID
    overs_per_innings: int
    venue: str
    match_date: datetime
    created_by_id: uuid.UUID
    status: str
    current_innings: int
    
    # Live scoring data
    team_a_score: int
    team_a_wickets: int
    team_a_overs: float
    team_b_score: int
    team_b_wickets: int
    team_b_overs: float
    
    # Toss data
    toss_winner_id: Optional[uuid.UUID] = None
    toss_decision: Optional[str] = None
    
    # Result data
    winner_team_id: Optional[uuid.UUID] = None
    result_description: Optional[str] = None
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
