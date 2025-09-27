"""
Cricket API Schemas

Pydantic models for request/response serialization for cricket data
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from app.models.cricket import MatchFormat, MatchStatus, InningsStatus, DismissalType, ExtraType


# Base schemas
class BaseSchema(BaseModel):
    """Base schema with common configuration"""
    model_config = ConfigDict(from_attributes=True)


# Team schemas
class TeamBase(BaseSchema):
    """Base team schema"""
    name: str = Field(..., min_length=1, max_length=100)
    short_name: str = Field(..., min_length=1, max_length=10)
    logo_url: Optional[str] = Field(None, max_length=500)
    home_ground: Optional[str] = Field(None, max_length=200)


class TeamCreate(TeamBase):
    """Schema for creating a team"""
    captain_id: Optional[int] = None


class TeamUpdate(BaseSchema):
    """Schema for updating a team"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    short_name: Optional[str] = Field(None, min_length=1, max_length=10)
    logo_url: Optional[str] = Field(None, max_length=500)
    home_ground: Optional[str] = Field(None, max_length=200)
    captain_id: Optional[int] = None


class Team(TeamBase):
    """Complete team schema"""
    id: int
    captain_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class TeamSummary(BaseSchema):
    """Team summary for listings"""
    id: int
    name: str
    short_name: str
    logo_url: Optional[str] = None


# Player schemas
class PlayerBase(BaseSchema):
    """Base player schema"""
    name: str = Field(..., min_length=1, max_length=100)
    jersey_number: Optional[int] = Field(None, ge=1, le=99)
    role: Optional[str] = Field(None, max_length=50)
    batting_style: Optional[str] = Field(None, max_length=50)
    bowling_style: Optional[str] = Field(None, max_length=50)
    date_of_birth: Optional[datetime] = None


class PlayerCreate(PlayerBase):
    """Schema for creating a player"""
    team_id: Optional[int] = None


class PlayerUpdate(BaseSchema):
    """Schema for updating a player"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    team_id: Optional[int] = None
    jersey_number: Optional[int] = Field(None, ge=1, le=99)
    role: Optional[str] = Field(None, max_length=50)
    batting_style: Optional[str] = Field(None, max_length=50)
    bowling_style: Optional[str] = Field(None, max_length=50)
    date_of_birth: Optional[datetime] = None


class Player(PlayerBase):
    """Complete player schema"""
    id: int
    team_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class PlayerSummary(BaseSchema):
    """Player summary with team info"""
    id: int
    name: str
    jersey_number: Optional[int] = None
    role: Optional[str] = None
    team: Optional[TeamSummary] = None


# Match schemas
class MatchBase(BaseSchema):
    """Base match schema"""
    title: str = Field(..., min_length=1, max_length=200)
    match_format: MatchFormat
    venue: Optional[str] = Field(None, max_length=200)
    scheduled_start: datetime
    overs_per_innings: int = Field(default=20, ge=1, le=50)
    balls_per_over: int = Field(default=6, ge=4, le=8)
    max_wickets: int = Field(default=10, ge=1, le=11)
    dual_scorer_required: bool = True
    weather_conditions: Optional[str] = Field(None, max_length=200)
    pitch_conditions: Optional[str] = Field(None, max_length=200)
    match_notes: Optional[str] = None


class MatchCreate(MatchBase):
    """Schema for creating a match"""
    home_team_id: int = Field(..., gt=0)
    away_team_id: int = Field(..., gt=0)
    primary_scorer_id: Optional[str] = Field(None, max_length=100)
    secondary_scorer_id: Optional[str] = Field(None, max_length=100)


class MatchUpdate(BaseSchema):
    """Schema for updating a match"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    venue: Optional[str] = Field(None, max_length=200)
    scheduled_start: Optional[datetime] = None
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    status: Optional[MatchStatus] = None
    toss_winner_id: Optional[int] = None
    toss_decision: Optional[str] = Field(None, pattern="^(BAT|BOWL)$")
    winner_id: Optional[int] = None
    result_type: Optional[str] = Field(None, max_length=50)
    margin: Optional[int] = None
    weather_conditions: Optional[str] = Field(None, max_length=200)
    pitch_conditions: Optional[str] = Field(None, max_length=200)
    match_notes: Optional[str] = None


class Match(MatchBase):
    """Complete match schema"""
    id: int
    status: MatchStatus
    home_team_id: int
    away_team_id: int
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    toss_winner_id: Optional[int] = None
    toss_decision: Optional[str] = None
    winner_id: Optional[int] = None
    result_type: Optional[str] = None
    margin: Optional[int] = None
    primary_scorer_id: Optional[str] = None
    secondary_scorer_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class MatchWithTeams(Match):
    """Match schema with team details"""
    home_team: TeamSummary
    away_team: TeamSummary
    toss_winner: Optional[TeamSummary] = None
    winner: Optional[TeamSummary] = None


class MatchSummary(BaseSchema):
    """Match summary for listings"""
    id: int
    title: str
    match_format: MatchFormat
    status: MatchStatus
    venue: Optional[str] = None
    scheduled_start: datetime
    home_team: TeamSummary
    away_team: TeamSummary


# Innings schemas
class InningsBase(BaseSchema):
    """Base innings schema"""
    innings_number: int = Field(..., ge=1, le=4)
    target_runs: Optional[int] = Field(None, ge=1)


class InningsCreate(InningsBase):
    """Schema for creating innings"""
    match_id: int = Field(..., gt=0)
    batting_team_id: int = Field(..., gt=0)
    bowling_team_id: int = Field(..., gt=0)


class InningsUpdate(BaseSchema):
    """Schema for updating innings"""
    status: Optional[InningsStatus] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    target_runs: Optional[int] = Field(None, ge=1)
    is_declared: Optional[bool] = None
    is_forfeited: Optional[bool] = None


class Innings(InningsBase):
    """Complete innings schema"""
    id: int
    match_id: int
    batting_team_id: int
    bowling_team_id: int
    status: InningsStatus
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    total_runs: int = 0
    total_wickets: int = 0
    total_overs: float = 0.0
    total_balls: int = 0
    wides: int = 0
    no_balls: int = 0
    byes: int = 0
    leg_byes: int = 0
    penalties: int = 0
    is_declared: bool = False
    is_forfeited: bool = False
    created_at: datetime
    updated_at: datetime

    @property
    def total_extras(self) -> int:
        """Calculate total extras"""
        return self.wides + self.no_balls + self.byes + self.leg_byes + self.penalties

    @property
    def current_over(self) -> int:
        """Get current over number"""
        return int(self.total_overs) + 1 if self.total_balls % 6 != 0 or self.total_balls == 0 else int(self.total_overs)

    @property
    def current_ball_in_over(self) -> int:
        """Get current ball in over (1-6)"""
        ball_in_over = self.total_balls % 6
        return 6 if ball_in_over == 0 and self.total_balls > 0 else ball_in_over


class InningsWithTeams(Innings):
    """Innings with team information"""
    batting_team: TeamSummary
    bowling_team: TeamSummary


class InningsSummary(BaseSchema):
    """Innings summary for scorecards"""
    id: int
    innings_number: int
    status: InningsStatus
    batting_team: TeamSummary
    total_runs: int = 0
    total_wickets: int = 0
    total_overs: float = 0.0
    total_extras: int = 0


# Ball schemas
class BallBase(BaseSchema):
    """Base ball schema"""
    ball_number: int = Field(..., ge=1)
    runs_scored: int = Field(default=0, ge=0, le=6)
    is_boundary: bool = False
    boundary_type: Optional[int] = Field(None, ge=4, le=6)
    extra_type: Optional[ExtraType] = None
    extra_runs: int = Field(default=0, ge=0)
    is_legal_delivery: bool = True
    is_wicket: bool = False
    dismissal_type: Optional[DismissalType] = None
    ball_speed: Optional[float] = Field(None, ge=0, le=200)
    ball_type: Optional[str] = Field(None, max_length=50)


class BallCreate(BallBase):
    """Schema for creating a ball"""
    over_id: int = Field(..., gt=0)
    bowler_id: int = Field(..., gt=0)
    batsman_id: int = Field(..., gt=0)
    non_striker_id: int = Field(..., gt=0)
    dismissed_player_id: Optional[int] = Field(None, gt=0)
    fielder_id: Optional[int] = Field(None, gt=0)


class BallUpdate(BaseSchema):
    """Schema for updating a ball"""
    runs_scored: Optional[int] = Field(None, ge=0, le=6)
    is_boundary: Optional[bool] = None
    boundary_type: Optional[int] = Field(None, ge=4, le=6)
    extra_type: Optional[ExtraType] = None
    extra_runs: Optional[int] = Field(None, ge=0)
    is_legal_delivery: Optional[bool] = None
    is_wicket: Optional[bool] = None
    dismissal_type: Optional[DismissalType] = None
    dismissed_player_id: Optional[int] = Field(None, gt=0)
    fielder_id: Optional[int] = Field(None, gt=0)
    ball_speed: Optional[float] = Field(None, ge=0, le=200)
    ball_type: Optional[str] = Field(None, max_length=50)


class Ball(BallBase):
    """Complete ball schema"""
    id: int
    over_id: int
    bowler_id: int
    batsman_id: int
    non_striker_id: int
    dismissed_player_id: Optional[int] = None
    fielder_id: Optional[int] = None
    primary_scorer_confirmed: bool = False
    secondary_scorer_confirmed: bool = False
    has_dispute: bool = False
    dispute_resolved: bool = True
    created_at: datetime
    updated_at: datetime

    @property
    def total_runs(self) -> int:
        """Total runs for this ball"""
        return self.runs_scored + self.extra_runs


class BallWithPlayers(Ball):
    """Ball schema with player information"""
    bowler: PlayerSummary
    batsman: PlayerSummary
    non_striker: PlayerSummary
    dismissed_player: Optional[PlayerSummary] = None
    fielder: Optional[PlayerSummary] = None


# Batting performance schemas
class BattingPerformanceBase(BaseSchema):
    """Base batting performance schema"""
    batting_position: int = Field(..., ge=1, le=11)
    came_in_at_over: Optional[float] = Field(None, ge=0)
    went_out_at_over: Optional[float] = Field(None, ge=0)


class BattingPerformanceCreate(BattingPerformanceBase):
    """Schema for creating batting performance"""
    innings_id: int = Field(..., gt=0)
    player_id: int = Field(..., gt=0)


class BattingPerformanceUpdate(BaseSchema):
    """Schema for updating batting performance"""
    runs_scored: Optional[int] = Field(None, ge=0)
    balls_faced: Optional[int] = Field(None, ge=0)
    fours: Optional[int] = Field(None, ge=0)
    sixes: Optional[int] = Field(None, ge=0)
    is_out: Optional[bool] = None
    dismissal_type: Optional[DismissalType] = None
    bowler_id: Optional[int] = Field(None, gt=0)
    fielder_id: Optional[int] = Field(None, gt=0)
    went_out_at_over: Optional[float] = Field(None, ge=0)


class BattingPerformance(BattingPerformanceBase):
    """Complete batting performance schema"""
    id: int
    innings_id: int
    player_id: int
    runs_scored: int = 0
    balls_faced: int = 0
    fours: int = 0
    sixes: int = 0
    is_out: bool = False
    dismissal_type: Optional[DismissalType] = None
    bowler_id: Optional[int] = None
    fielder_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    @property
    def strike_rate(self) -> Optional[float]:
        """Calculate strike rate"""
        if self.balls_faced == 0:
            return None
        return (self.runs_scored / self.balls_faced) * 100


class BattingPerformanceWithPlayer(BattingPerformance):
    """Batting performance with player information"""
    player: PlayerSummary
    bowler: Optional[PlayerSummary] = None
    fielder: Optional[PlayerSummary] = None


# Bowling performance schemas
class BowlingPerformanceBase(BaseSchema):
    """Base bowling performance schema"""
    pass


class BowlingPerformanceCreate(BowlingPerformanceBase):
    """Schema for creating bowling performance"""
    innings_id: int = Field(..., gt=0)
    player_id: int = Field(..., gt=0)


class BowlingPerformanceUpdate(BaseSchema):
    """Schema for updating bowling performance"""
    overs_bowled: Optional[float] = Field(None, ge=0)
    runs_conceded: Optional[int] = Field(None, ge=0)
    wickets_taken: Optional[int] = Field(None, ge=0)
    maidens: Optional[int] = Field(None, ge=0)
    wides: Optional[int] = Field(None, ge=0)
    no_balls: Optional[int] = Field(None, ge=0)
    dots: Optional[int] = Field(None, ge=0)
    boundaries_conceded: Optional[int] = Field(None, ge=0)
    sixes_conceded: Optional[int] = Field(None, ge=0)


class BowlingPerformance(BowlingPerformanceBase):
    """Complete bowling performance schema"""
    id: int
    innings_id: int
    player_id: int
    overs_bowled: float = 0.0
    runs_conceded: int = 0
    wickets_taken: int = 0
    maidens: int = 0
    wides: int = 0
    no_balls: int = 0
    dots: int = 0
    boundaries_conceded: int = 0
    sixes_conceded: int = 0
    created_at: datetime
    updated_at: datetime

    @property
    def economy_rate(self) -> Optional[float]:
        """Calculate economy rate"""
        if self.overs_bowled == 0:
            return None
        return self.runs_conceded / self.overs_bowled

    @property
    def bowling_average(self) -> Optional[float]:
        """Calculate bowling average"""
        if self.wickets_taken == 0:
            return None
        return self.runs_conceded / self.wickets_taken

    @property
    def strike_rate(self) -> Optional[float]:
        """Calculate bowling strike rate"""
        if self.wickets_taken == 0:
            return None
        balls_bowled = self.overs_bowled * 6
        return balls_bowled / self.wickets_taken


class BowlingPerformanceWithPlayer(BowlingPerformance):
    """Bowling performance with player information"""
    player: PlayerSummary


# Scorecard schemas
class Scorecard(BaseSchema):
    """Complete match scorecard"""
    match: MatchWithTeams
    innings: List[InningsSummary]
    current_innings: Optional[InningsWithTeams] = None
    batting_performances: List[BattingPerformanceWithPlayer] = []
    bowling_performances: List[BowlingPerformanceWithPlayer] = []


# Live scoring schemas
class LiveScore(BaseSchema):
    """Live scoring update"""
    match_id: int
    current_innings: Optional[InningsWithTeams] = None
    last_ball: Optional[BallWithPlayers] = None
    recent_balls: List[BallWithPlayers] = []
    current_partnership: Optional[dict] = None
    required_run_rate: Optional[float] = None
    current_run_rate: Optional[float] = None


# API Response schemas
class PaginatedResponse(BaseSchema):
    """Paginated response wrapper"""
    items: List[BaseSchema]
    total: int
    page: int
    per_page: int
    pages: int


class MatchListResponse(PaginatedResponse):
    """Paginated match list response"""
    items: List[MatchSummary]


class TeamListResponse(PaginatedResponse):
    """Paginated team list response"""
    items: List[Team]


class PlayerListResponse(PaginatedResponse):
    """Paginated player list response"""
    items: List[PlayerSummary]