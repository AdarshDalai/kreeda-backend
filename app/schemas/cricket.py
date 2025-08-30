"""
Cricket API Schemas - Properly defined Pydantic models
Input validation, output serialization, and API documentation
"""
from typing import Optional, List, Literal
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator


# Base schemas
class BaseSchema(BaseModel):
    class Config:
        from_attributes = True


# Team schemas
class TeamCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Team name")
    short_name: str = Field(..., min_length=2, max_length=10, description="Short name for scoreboard")
    city: Optional[str] = Field(None, max_length=100)
    coach: Optional[str] = Field(None, max_length=100)
    home_ground: Optional[str] = Field(None, max_length=200)
    captain_id: Optional[str] = Field(None, description="Captain player ID")  # Changed from int to str


class TeamResponse(BaseSchema):
    id: str  # Changed from int to str for UUID
    name: str
    short_name: str
    created_by: str  # Changed from int to str for UUID
    created_at: str  # Changed from datetime to str for compatibility


class TeamWithPlayers(TeamResponse):
    players: List["PlayerResponse"] = []


# Player schemas
class PlayerCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    jersey_number: Optional[int] = Field(None, ge=1, le=999)


class PlayerUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    jersey_number: Optional[int] = Field(None, ge=1, le=999)
    batting_order: Optional[int] = Field(None, ge=1, le=11)
    is_captain: Optional[bool] = None
    is_wicket_keeper: Optional[bool] = None


class PlayerResponse(BaseSchema):
    id: str  # Changed from int to str for UUID
    name: str
    team_id: str  # Changed from int to str for UUID
    jersey_number: Optional[int]
    batting_order: Optional[int] = None
    is_captain: bool = False
    is_wicket_keeper: bool = False
    created_at: str  # Add created_at field


# Match schemas
class MatchCreate(BaseModel):
    team_a_id: str = Field(..., description="Home team ID")  # Changed from int to str for UUID
    team_b_id: str = Field(..., description="Away team ID")  # Changed from int to str for UUID
    overs_per_side: int = Field(..., ge=1, le=50, description="Overs per innings")
    venue: Optional[str] = Field(None, max_length=200)
    match_type: Optional[str] = Field("Limited Overs", max_length=50)
    
    @field_validator('team_b_id')
    @classmethod
    def teams_must_be_different(cls, v, info):
        if info.data and 'team_a_id' in info.data and v == info.data['team_a_id']:
            raise ValueError('Teams must be different')
        return v


class TossResult(BaseModel):
    toss_winner_id: str = Field(..., description="Team that won the toss")  # Changed from int to str
    batting_first_id: str = Field(..., description="Team that will bat first")  # Changed from int to str


class MatchResponse(BaseSchema):
    id: str  # Changed from int to str for UUID
    team_a_id: str  # Changed from int to str for UUID
    team_b_id: str  # Changed from int to str for UUID
    overs_per_side: int
    venue: Optional[str]
    status: str = "scheduled"
    toss_winner: Optional[str] = None  # Changed field name and type
    batting_first: Optional[str] = None  # Changed field name and type
    created_at: str  # Changed from datetime to str


# Ball scoring schemas
class BallResponse(BaseSchema):
    id: str  # Changed from int to str for UUID
    match_id: str  # Changed from int to str for UUID
    innings: int
    over: int
    ball: int
    batsman_id: str  # Changed from int to str for UUID
    bowler_id: str  # Changed from int to str for UUID
    runs: int
    is_wicket: bool
    wicket_type: Optional[str] = None
    fielder_id: Optional[str] = None  # Changed from int to str for UUID
    is_extra: bool
    extra_type: Optional[str] = None
    extra_runs: int = 0
    timestamp: str  # Changed from datetime to str


class BallCreate(BaseSchema):
    match_id: str  # Changed from int to str for UUID
    innings: int
    over: int
    ball: int
    batsman_id: str  # Changed from int to str for UUID
    bowler_id: str  # Changed from int to str for UUID
    runs: int
    is_wicket: bool
    wicket_type: Optional[str] = None
    fielder_id: Optional[str] = None  # Changed from int to str for UUID
    is_extra: bool
    extra_type: Optional[str] = None
    extra_runs: int = 0


# Live scoring schemas
class BatsmanStats(BaseModel):
    player_id: str  # Changed from int to str for UUID
    name: str
    runs: int
    balls_faced: int
    fours: int
    sixes: int
    strike_rate: float


class BowlerStats(BaseModel):
    player_id: str  # Changed from int to str for UUID
    name: str
    overs: str
    runs_conceded: int
    wickets: int
    economy_rate: float


class InningsStats(BaseModel):
    innings_id: str  # Changed from int to str for UUID
    innings_number: int
    batting_team: str
    bowling_team: str
    total_runs: int
    wickets_lost: int
    overs_completed: str
    run_rate: float
    required_rate: Optional[float]
    balls_remaining: Optional[int]


class LiveScore(BaseModel):
    match_id: str  # Changed from int to str for UUID
    match_status: str
    current_innings: InningsStats
    current_batsmen: List[BatsmanStats]
    current_bowler: BowlerStats
    recent_balls: List[dict]
    target: Optional[int]


# Update forward references
TeamWithPlayers.model_rebuild()
