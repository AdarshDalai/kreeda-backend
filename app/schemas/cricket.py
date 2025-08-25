"""
Cricket API Schemas - Properly defined Pydantic models
Input validation, output serialization, and API documentation
"""
from typing import Optional, List, Literal
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, validator


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
    captain_id: Optional[int] = Field(None, description="Captain player ID")


class TeamResponse(BaseSchema):
    id: int
    name: str
    short_name: str
    created_by: int
    created_at: datetime


class TeamWithPlayers(TeamResponse):
    players: List["PlayerResponse"] = []


# Player schemas
class PlayerCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    jersey_number: Optional[int] = Field(None, ge=1, le=999)
    position: Optional[str] = Field(None, max_length=50)
    batting_style: Optional[str] = Field(None, max_length=50)
    bowling_style: Optional[str] = Field(None, max_length=50)


class PlayerUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    jersey_number: Optional[int] = Field(None, ge=1, le=999)
    batting_order: Optional[int] = Field(None, ge=1, le=11)
    is_captain: Optional[bool] = None
    is_wicket_keeper: Optional[bool] = None


class PlayerResponse(BaseSchema):
    id: int
    name: str
    team_id: int
    jersey_number: Optional[int]
    batting_order: Optional[int]
    is_captain: bool
    is_wicket_keeper: bool


# Match schemas
class MatchCreate(BaseModel):
    team_a_id: int = Field(..., description="Home team ID")
    team_b_id: int = Field(..., description="Away team ID") 
    overs_per_side: int = Field(..., ge=1, le=50, description="Overs per innings")
    venue: Optional[str] = Field(None, max_length=200)
    match_type: Optional[str] = Field("Limited Overs", max_length=50)
    
    @validator('team_b_id')
    def teams_must_be_different(cls, v, values):
        if 'team_a_id' in values and v == values['team_a_id']:
            raise ValueError('Teams must be different')
        return v


class TossResult(BaseModel):
    toss_winner_id: int = Field(..., description="Team that won the toss")
    batting_first_id: int = Field(..., description="Team that will bat first")


class MatchResponse(BaseSchema):
    id: int
    team_a_id: int
    team_b_id: int
    overs_per_side: int
    venue: Optional[str]
    match_date: Optional[datetime]
    current_innings: int
    status: str
    toss_winner_id: Optional[int]
    batting_first_id: Optional[int]
    winner_id: Optional[int]
    win_margin: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]


# Ball scoring schemas
class BallCreate(BaseModel):
    batsman_id: int = Field(..., description="Batsman on strike")
    bowler_id: int = Field(..., description="Bowler")
    non_striker_id: Optional[int] = Field(None, description="Non-striker batsman")
    
    runs: int = Field(..., ge=0, le=6, description="Runs scored by batsman")
    extras: int = Field(0, ge=0, le=10, description="Extra runs (wides, byes, etc)")
    extra_type: Optional[Literal["wide", "noball", "bye", "legbye"]] = None
    
    ball_type: Optional[str] = Field("normal", max_length=20)
    is_wicket: bool = Field(False, description="Was there a wicket?")
    wicket_type: Optional[Literal["bowled", "caught", "lbw", "run_out", "stumped", "hit_wicket"]] = None
    wicket_player_id: Optional[int] = Field(None, description="Player who got out")
    fielder_id: Optional[int] = Field(None, description="Fielder involved")
    
    @validator('wicket_type')
    def wicket_type_required_if_wicket(cls, v, values):
        if values.get('is_wicket') and not v:
            raise ValueError('Wicket type required when is_wicket is True')
        return v
    
    @validator('extra_type')
    def validate_extras(cls, v, values):
        if values.get('extras', 0) > 0 and not v:
            raise ValueError('Extra type required when extras > 0')
        return v


# Live scoring schemas
class BatsmanStats(BaseModel):
    player_id: int
    name: str
    runs: int
    balls_faced: int
    fours: int
    sixes: int
    strike_rate: float


class BowlerStats(BaseModel):
    player_id: int
    name: str
    overs: str
    runs_conceded: int
    wickets: int
    economy_rate: float


class InningsStats(BaseModel):
    innings_id: int
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
    match_id: int
    match_status: str
    current_innings: InningsStats
    current_batsmen: List[BatsmanStats]
    current_bowler: BowlerStats
    recent_balls: List[dict]
    target: Optional[int]


# Update forward references
TeamWithPlayers.model_rebuild()
