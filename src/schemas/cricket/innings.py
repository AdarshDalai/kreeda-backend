"""
Pydantic schemas for Cricket Innings and Overs

This module provides request/response schemas for:
- Innings creation and management
- Over tracking
- Live innings state
- Real-time scoring updates

Following event sourcing pattern:
- Current state derived from ball records
- Immutable ball history
- Real-time aggregation updates
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, ConfigDict


# ============================================================================
# NESTED SCHEMAS FOR LIVE STATE
# ============================================================================

class CurrentBatsmanSchema(BaseModel):
    """
    Current batsman details for live innings state
    """
    user_id: UUID = Field(..., description="User ID of the batsman")
    name: str = Field(..., description="Batsman name")
    runs_scored: int = Field(default=0, description="Runs in this innings")
    balls_faced: int = Field(default=0, description="Balls faced in this innings")
    strike_rate: float = Field(default=0.0, description="Strike rate (runs/balls * 100)")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Virat Kohli",
                "runs_scored": 45,
                "balls_faced": 32,
                "strike_rate": 140.63
            }
        }
    )


class CurrentBowlerSchema(BaseModel):
    """
    Current bowler details for live innings state
    """
    user_id: UUID = Field(..., description="User ID of the bowler")
    name: str = Field(..., description="Bowler name")
    overs_bowled: float = Field(default=0.0, description="Overs bowled (e.g., 5.3)")
    runs_conceded: int = Field(default=0, description="Runs conceded")
    wickets_taken: int = Field(default=0, description="Wickets taken")
    economy_rate: float = Field(default=0.0, description="Economy rate (runs per over)")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174001",
                "name": "Jasprit Bumrah",
                "overs_bowled": 5.3,
                "runs_conceded": 28,
                "wickets_taken": 2,
                "economy_rate": 5.14
            }
        }
    )


class InningsStateSchema(BaseModel):
    """
    Live innings state (derived from ball events)
    
    This represents the current state of the innings calculated from:
    - Ball records (runs, wickets, overs)
    - Current players on field
    - Match situation (target, required rate)
    """
    current_score: str = Field(
        ...,
        description="Current score in format '145/4'",
        examples=["145/4", "0/0", "287/10"]
    )
    overs_bowled: float = Field(
        ...,
        description="Overs bowled (e.g., 15.3 = 15 overs + 3 balls)",
        examples=[15.3, 0.0, 20.0]
    )
    run_rate: float = Field(
        ...,
        description="Current run rate (runs per over)",
        examples=[9.35, 0.0, 14.35]
    )
    
    # Current players
    striker: Optional[CurrentBatsmanSchema] = Field(
        None,
        description="Batsman on strike"
    )
    non_striker: Optional[CurrentBatsmanSchema] = Field(
        None,
        description="Batsman at non-striker end"
    )
    current_bowler: Optional[CurrentBowlerSchema] = Field(
        None,
        description="Currently bowling"
    )
    
    # Match situation (for chasing team)
    target_runs: Optional[int] = Field(
        None,
        description="Target to chase (second innings only)"
    )
    required_run_rate: Optional[float] = Field(
        None,
        description="Required run rate to win (second innings only)"
    )
    runs_required: Optional[int] = Field(
        None,
        description="Runs needed to win (second innings only)"
    )
    balls_remaining: Optional[int] = Field(
        None,
        description="Balls left in innings"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "current_score": "145/4",
                "overs_bowled": 15.3,
                "run_rate": 9.35,
                "striker": {
                    "user_id": "123e4567-e89b-12d3-a456-426614174000",
                    "name": "Virat Kohli",
                    "runs_scored": 45,
                    "balls_faced": 32,
                    "strike_rate": 140.63
                },
                "non_striker": {
                    "user_id": "123e4567-e89b-12d3-a456-426614174002",
                    "name": "Rohit Sharma",
                    "runs_scored": 68,
                    "balls_faced": 51,
                    "strike_rate": 133.33
                },
                "current_bowler": {
                    "user_id": "123e4567-e89b-12d3-a456-426614174001",
                    "name": "Jasprit Bumrah",
                    "overs_bowled": 5.3,
                    "runs_conceded": 28,
                    "wickets_taken": 2,
                    "economy_rate": 5.14
                },
                "target_runs": 180,
                "required_run_rate": 7.89,
                "runs_required": 35,
                "balls_remaining": 28
            }
        }
    )


# ============================================================================
# INNINGS REQUEST SCHEMAS
# ============================================================================

class InningsCreateRequest(BaseModel):
    """
    Request schema for starting a new innings
    
    Required: innings_number, batting_team_id, bowling_team_id
    Optional: target_runs (for second innings chase)
    
    Workflow:
        1. Match status must be LIVE or TOSS_PENDING
        2. Innings created with initial state (0/0 in 0.0 overs)
        3. Opening batsmen must be set via separate endpoint
        4. First over created when first ball is bowled
    """
    innings_number: int = Field(
        ...,
        ge=1,
        le=4,
        description="Innings number (1-4, usually 1 or 2)",
        examples=[1, 2]
    )
    batting_team_id: UUID = Field(
        ...,
        description="Team batting in this innings"
    )
    bowling_team_id: UUID = Field(
        ...,
        description="Team bowling in this innings"
    )
    target_runs: Optional[int] = Field(
        None,
        ge=1,
        description="Target to chase (second innings only)",
        examples=[181, 301]
    )
    
    @field_validator('innings_number')
    @classmethod
    def validate_innings_number(cls, v: int) -> int:
        """Ensure innings number is valid"""
        if v < 1 or v > 4:
            raise ValueError("innings_number must be between 1 and 4")
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "innings_number": 2,
                "batting_team_id": "123e4567-e89b-12d3-a456-426614174000",
                "bowling_team_id": "123e4567-e89b-12d3-a456-426614174001",
                "target_runs": 181
            }
        }
    )


class InningsUpdateRequest(BaseModel):
    """
    Request schema for updating innings details
    
    Used for:
    - Ending innings (is_completed=True)
    - Marking all-out (all_out=True)
    - Recording declaration (declared=True)
    """
    is_completed: Optional[bool] = Field(
        None,
        description="Mark innings as completed"
    )
    all_out: Optional[bool] = Field(
        None,
        description="Team is all out (10 wickets fallen)"
    )
    declared: Optional[bool] = Field(
        None,
        description="Batting team declared innings"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "is_completed": True,
                "all_out": True
            }
        }
    )


class SetBatsmenRequest(BaseModel):
    """
    Request schema for setting opening batsmen or new batsman after wicket
    
    Used when:
    - Starting innings (set both opening batsmen)
    - After wicket (set new batsman)
    """
    striker_user_id: UUID = Field(
        ...,
        description="Batsman on strike"
    )
    non_striker_user_id: Optional[UUID] = Field(
        None,
        description="Batsman at non-striker end (required for opening pair)"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "striker_user_id": "123e4567-e89b-12d3-a456-426614174000",
                "non_striker_user_id": "123e4567-e89b-12d3-a456-426614174002"
            }
        }
    )


class SetBowlerRequest(BaseModel):
    """
    Request schema for setting current bowler
    
    Used when:
    - Starting new over
    - Changing bowler mid-match
    """
    bowler_user_id: UUID = Field(
        ...,
        description="Bowler for current/next over"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "bowler_user_id": "123e4567-e89b-12d3-a456-426614174001"
            }
        }
    )


# ============================================================================
# INNINGS RESPONSE SCHEMAS
# ============================================================================

class InningsResponse(BaseModel):
    """
    Response schema for innings details
    
    Includes:
    - Basic innings info (teams, innings number)
    - Current totals (runs, wickets, overs)
    - Status flags (completed, all-out, declared)
    - Target info (for chasing)
    """
    id: UUID = Field(..., description="Innings ID")
    match_id: UUID = Field(..., description="Match ID")
    innings_number: int = Field(..., description="Innings number (1-4)")
    
    # Teams
    batting_team_id: UUID = Field(..., description="Batting team ID")
    bowling_team_id: UUID = Field(..., description="Bowling team ID")
    batting_team_name: Optional[str] = Field(None, description="Batting team name")
    bowling_team_name: Optional[str] = Field(None, description="Bowling team name")
    
    # Current totals
    total_runs: int = Field(..., description="Total runs scored")
    wickets_fallen: int = Field(..., description="Wickets fallen")
    extras: int = Field(..., description="Total extras")
    current_over_number: int = Field(..., description="Current over number")
    current_ball_in_over: int = Field(..., description="Current ball in over (0-5)")
    
    # Status
    is_completed: bool = Field(..., description="Innings completed")
    all_out: bool = Field(..., description="Team all out")
    declared: bool = Field(..., description="Innings declared")
    
    # Target (chase scenario)
    target_runs: Optional[int] = Field(None, description="Target to chase")
    
    # Current players
    striker_user_id: Optional[UUID] = Field(None, description="Striker ID")
    non_striker_user_id: Optional[UUID] = Field(None, description="Non-striker ID")
    current_bowler_user_id: Optional[UUID] = Field(None, description="Bowler ID")
    
    # Timing
    started_at: Optional[datetime] = Field(None, description="Innings start time")
    completed_at: Optional[datetime] = Field(None, description="Innings end time")
    created_at: datetime = Field(..., description="Record creation time")
    updated_at: datetime = Field(..., description="Last update time")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174003",
                "match_id": "123e4567-e89b-12d3-a456-426614174004",
                "innings_number": 1,
                "batting_team_id": "123e4567-e89b-12d3-a456-426614174000",
                "bowling_team_id": "123e4567-e89b-12d3-a456-426614174001",
                "batting_team_name": "Mumbai Indians",
                "bowling_team_name": "Chennai Super Kings",
                "total_runs": 145,
                "wickets_fallen": 4,
                "extras": 12,
                "current_over_number": 15,
                "current_ball_in_over": 3,
                "is_completed": False,
                "all_out": False,
                "declared": False,
                "target_runs": None,
                "striker_user_id": "123e4567-e89b-12d3-a456-426614174000",
                "non_striker_user_id": "123e4567-e89b-12d3-a456-426614174002",
                "current_bowler_user_id": "123e4567-e89b-12d3-a456-426614174001",
                "started_at": "2025-10-31T14:00:00Z",
                "completed_at": None,
                "created_at": "2025-10-31T14:00:00Z",
                "updated_at": "2025-10-31T15:32:45Z"
            }
        }
    )


class InningsWithStateResponse(InningsResponse):
    """
    Extended innings response with live state calculation
    
    Includes everything from InningsResponse plus:
    - Live innings state (current batsmen, bowler stats)
    - Match situation (required rate, runs needed)
    - Derived from ball-by-ball event log
    """
    live_state: InningsStateSchema = Field(
        ...,
        description="Current innings state (derived from balls)"
    )
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174003",
                "match_id": "123e4567-e89b-12d3-a456-426614174004",
                "innings_number": 2,
                "batting_team_id": "123e4567-e89b-12d3-a456-426614174000",
                "bowling_team_id": "123e4567-e89b-12d3-a456-426614174001",
                "total_runs": 145,
                "wickets_fallen": 4,
                "extras": 12,
                "live_state": {
                    "current_score": "145/4",
                    "overs_bowled": 15.3,
                    "run_rate": 9.35,
                    "target_runs": 180,
                    "required_run_rate": 7.89,
                    "runs_required": 35,
                    "balls_remaining": 28
                }
            }
        }
    )


# ============================================================================
# OVER RESPONSE SCHEMAS
# ============================================================================

class OverResponse(BaseModel):
    """
    Response schema for over details
    
    Includes:
    - Over metadata (number, bowler)
    - Over summary (runs, wickets, extras)
    - Ball-by-ball sequence for UI display
    """
    id: UUID = Field(..., description="Over ID")
    innings_id: UUID = Field(..., description="Innings ID")
    over_number: int = Field(..., description="Over number (1-based)")
    bowler_user_id: UUID = Field(..., description="Bowler ID")
    bowler_name: Optional[str] = Field(None, description="Bowler name")
    
    # Over summary
    runs_conceded: int = Field(..., description="Runs in this over")
    wickets_taken: int = Field(..., description="Wickets in this over")
    legal_deliveries: int = Field(..., description="Legal balls bowled")
    extras_in_over: int = Field(..., description="Extras in this over")
    is_maiden: bool = Field(..., description="Maiden over (0 runs)")
    is_completed: bool = Field(..., description="Over completed")
    
    # Ball sequence (e.g., ["W", "1", "4", "0", "2", "6"])
    ball_sequence: List[str] = Field(
        default=[],
        description="Ball-by-ball sequence for UI"
    )
    
    # Timing
    started_at: Optional[datetime] = Field(None, description="Over start time")
    completed_at: Optional[datetime] = Field(None, description="Over end time")
    created_at: datetime = Field(..., description="Record creation time")
    updated_at: datetime = Field(..., description="Last update time")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174005",
                "innings_id": "123e4567-e89b-12d3-a456-426614174003",
                "over_number": 15,
                "bowler_user_id": "123e4567-e89b-12d3-a456-426614174001",
                "bowler_name": "Jasprit Bumrah",
                "runs_conceded": 8,
                "wickets_taken": 1,
                "legal_deliveries": 6,
                "extras_in_over": 1,
                "is_maiden": False,
                "is_completed": True,
                "ball_sequence": ["1", "W", "0", "4", "1", "wd", "2"],
                "started_at": "2025-10-31T15:25:00Z",
                "completed_at": "2025-10-31T15:32:00Z",
                "created_at": "2025-10-31T15:25:00Z",
                "updated_at": "2025-10-31T15:32:00Z"
            }
        }
    )
