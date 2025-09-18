"""
Tournament schemas for API request/response models
Integrates with Phase 1 team and match schemas
"""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, validator

from app.schemas.team import TeamSimpleResponse
from app.schemas.user import UserResponse


class TournamentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    tournament_type: str = Field(..., pattern="^(knockout|league|round_robin)$")
    start_date: datetime
    end_date: Optional[datetime] = None
    registration_deadline: Optional[datetime] = None
    max_teams: int = Field(8, ge=2, le=32)
    min_teams: int = Field(4, ge=2, le=16)
    entry_fee: Decimal = Field(Decimal('0'), ge=0)
    prize_money: Decimal = Field(Decimal('0'), ge=0)
    overs_per_innings: int = Field(20, ge=5, le=50)
    venue_details: Optional[str] = Field(None, max_length=500)
    organizer_contact: Optional[str] = Field(None, max_length=255)
    is_public: bool = True

    @validator('end_date')
    def end_date_after_start_date(cls, v, values):
        if v and 'start_date' in values and v <= values['start_date']:
            raise ValueError('End date must be after start date')
        return v

    @validator('registration_deadline')
    def registration_deadline_before_start(cls, v, values):
        if v and 'start_date' in values and v >= values['start_date']:
            raise ValueError('Registration deadline must be before start date')
        return v

    @validator('min_teams')
    def min_teams_less_than_max(cls, v, values):
        if 'max_teams' in values and v > values['max_teams']:
            raise ValueError('Minimum teams cannot exceed maximum teams')
        return v


class TournamentCreate(TournamentBase):
    pass


class TournamentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    registration_deadline: Optional[datetime] = None
    max_teams: Optional[int] = Field(None, ge=2, le=32)
    entry_fee: Optional[Decimal] = Field(None, ge=0)
    prize_money: Optional[Decimal] = Field(None, ge=0)
    venue_details: Optional[str] = Field(None, max_length=500)
    organizer_contact: Optional[str] = Field(None, max_length=255)
    is_public: Optional[bool] = None


class TournamentTeamRegistration(BaseModel):
    team_id: uuid.UUID
    payment_reference: Optional[str] = Field(None, max_length=100)


class TournamentTeamResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    tournament_id: uuid.UUID
    team_id: uuid.UUID
    registered_at: datetime
    registration_fee_paid: bool
    payment_reference: Optional[str]
    seed_number: Optional[int]
    group_name: Optional[str]
    status: str
    team: TeamSimpleResponse
    registered_by: UserResponse


class TournamentStandingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    tournament_id: uuid.UUID
    team_id: uuid.UUID
    matches_played: int
    matches_won: int
    matches_lost: int
    matches_tied: int
    matches_no_result: int
    points: int
    runs_scored: int
    runs_conceded: int
    overs_faced: Decimal
    overs_bowled: Decimal
    net_run_rate: Decimal
    current_position: Optional[int]
    previous_position: Optional[int]
    last_updated: datetime
    team: TeamSimpleResponse


class TournamentMatchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    tournament_id: uuid.UUID
    match_id: uuid.UUID
    round_number: int
    match_number: int
    stage: Optional[str]
    group_name: Optional[str]
    scheduled_date: Optional[datetime]
    venue: Optional[str]
    is_knockout: bool
    importance_level: int
    created_at: datetime


class TournamentResponse(TournamentBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    status: str
    current_round: int
    created_by_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    creator: UserResponse
    
    # Optional detailed relationships
    teams: Optional[List[TournamentTeamResponse]] = []
    standings: Optional[List[TournamentStandingResponse]] = []
    matches: Optional[List[TournamentMatchResponse]] = []


class TournamentSummaryResponse(BaseModel):
    """Lightweight tournament response for listings"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    name: str
    tournament_type: str
    start_date: datetime
    end_date: Optional[datetime]
    status: str
    max_teams: int
    entry_fee: Decimal
    prize_money: Decimal
    created_by_id: uuid.UUID
    created_at: datetime
    
    # Computed fields
    registered_teams_count: Optional[int] = None
    is_registration_open: Optional[bool] = None


class TournamentFixtureGeneration(BaseModel):
    """Request model for generating tournament fixtures"""
    randomize_fixtures: bool = Field(True, description="Randomize team pairings")
    respect_seeding: bool = Field(False, description="Respect team seeding in fixtures")
    start_date: Optional[datetime] = Field(None, description="When to start the tournament matches")
    match_interval_hours: int = Field(24, ge=1, le=168, description="Hours between matches")
    venues: Optional[List[str]] = Field(None, description="Available venues for matches")


class TournamentStatsResponse(BaseModel):
    """Tournament statistics response"""
    tournament_id: uuid.UUID
    total_teams: int
    total_matches: int
    completed_matches: int
    total_runs_scored: int
    total_wickets_taken: int
    highest_team_score: Optional[int]
    lowest_team_score: Optional[int]
    most_runs_by_player: Optional[dict]  # {player_name, runs, team}
    most_wickets_by_player: Optional[dict]  # {player_name, wickets, team}
    average_runs_per_match: Optional[float]
    

class TournamentRuleCreate(BaseModel):
    rule_type: str = Field(..., max_length=50)
    rule_name: str = Field(..., max_length=100)
    rule_description: str = Field(..., max_length=1000)
    rule_value: Optional[str] = Field(None, max_length=500)
    applies_to_stage: Optional[str] = Field(None, pattern="^(group|knockout|all)$")


class TournamentRuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    tournament_id: uuid.UUID
    rule_type: str
    rule_name: str
    rule_description: str
    rule_value: Optional[str]
    applies_to_stage: Optional[str]
    is_active: bool
    created_at: datetime