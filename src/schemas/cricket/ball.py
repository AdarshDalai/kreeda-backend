"""
Pydantic schemas for Cricket Ball-by-Ball Scoring

This module provides request/response schemas for:
- Ball recording (the atomic unit of cricket)
- Wicket details (dismissals)
- Ball events for WebSocket broadcasting
- Aggregated ball statistics

Event Sourcing Pattern:
- Each ball is immutable once created
- Current innings state derived from ball records
- Wickets linked to specific balls
- Real-time aggregation from ball events
"""
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, ConfigDict

from src.models.enums import (
    ExtraType,
    BoundaryType,
    ShotType,
    DismissalType
)


# ============================================================================
# BALL REQUEST SCHEMAS
# ============================================================================

class BallCreateRequest(BaseModel):
    """
    Request schema for recording a ball bowled
    
    This is the PRIMARY endpoint for live scoring - every legal delivery
    and extra creates a Ball record.
    
    Workflow:
        1. Validate batsman/bowler are in match
        2. Create immutable Ball record
        3. If wicket: Create linked Wicket record
        4. Update innings state (runs, overs, wickets)
        5. Update performance aggregates
        6. Broadcast via WebSocket
    
    Event Sourcing:
        - Ball records are NEVER modified
        - Current state derived from ball history
        - Disputes handled via scoring_events table
    """
    innings_id: UUID = Field(
        ...,
        description="Innings ID where ball was bowled"
    )
    over_id: UUID = Field(
        ...,
        description="Over ID (created when over starts)"
    )
    ball_number: float = Field(
        ...,
        description="Ball number in format over.ball (e.g., 15.4)",
        examples=[1.1, 15.4, 19.6]
    )
    
    # Players involved
    bowler_user_id: UUID = Field(
        ...,
        description="Bowler who bowled this ball"
    )
    batsman_user_id: UUID = Field(
        ...,
        description="Batsman on strike (facing this ball)"
    )
    non_striker_user_id: Optional[UUID] = Field(
        None,
        description="Batsman at non-striker end"
    )
    
    # Ball outcome
    runs_scored: int = Field(
        default=0,
        ge=0,
        le=6,
        description="Runs scored off the bat (0-6)",
        examples=[0, 1, 4, 6]
    )
    is_wicket: bool = Field(
        default=False,
        description="Wicket fell on this ball"
    )
    is_boundary: bool = Field(
        default=False,
        description="Ball went for boundary"
    )
    boundary_type: Optional[BoundaryType] = Field(
        None,
        description="Type of boundary (FOUR or SIX)"
    )
    
    # Extras
    is_legal_delivery: bool = Field(
        default=True,
        description="Legal delivery (counts toward over)"
    )
    extra_type: ExtraType = Field(
        default=ExtraType.NONE,
        description="Type of extra (wide, no-ball, bye, etc.)"
    )
    extra_runs: int = Field(
        default=0,
        ge=0,
        description="Extra runs awarded",
        examples=[0, 1, 2, 4]
    )
    
    # Analytics (optional)
    shot_type: Optional[ShotType] = Field(
        None,
        description="Type of shot played"
    )
    fielding_position: Optional[str] = Field(
        None,
        max_length=50,
        description="Where ball was fielded",
        examples=["mid-off", "deep square leg", "long-on"]
    )
    wagon_wheel_data: Optional[Dict[str, Any]] = Field(
        None,
        description="Ball trajectory data for wagon wheel",
        examples=[{"angle": 45, "distance": 75}]
    )
    
    # Milestones
    is_milestone: bool = Field(
        default=False,
        description="Ball resulted in milestone"
    )
    milestone_type: Optional[str] = Field(
        None,
        max_length=50,
        description="Type of milestone",
        examples=["fifty", "hundred", "hat_trick", "5_wicket_haul"]
    )
    
    # Wicket details (if is_wicket=True)
    wicket_details: Optional['WicketDetailsSchema'] = Field(
        None,
        description="Dismissal details (required if is_wicket=True)"
    )
    
    @field_validator('ball_number')
    @classmethod
    def validate_ball_number(cls, v: float) -> float:
        """Validate ball number format (over.ball)"""
        over_num = int(v)
        ball_in_over = round((v - over_num) * 10)
        
        if over_num < 0:
            raise ValueError("Over number must be non-negative")
        if ball_in_over < 1 or ball_in_over > 6:
            raise ValueError("Ball in over must be 1-6 (e.g., 15.1 to 15.6)")
        
        return v
    
    @field_validator('runs_scored')
    @classmethod
    def validate_runs(cls, v: int) -> int:
        """Validate run count"""
        if v < 0 or v > 6:
            raise ValueError("Runs scored must be 0-6")
        return v
    
    @field_validator('extra_runs')
    @classmethod
    def validate_extra_runs(cls, v: int) -> int:
        """Validate extra runs"""
        if v < 0:
            raise ValueError("Extra runs cannot be negative")
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "innings_id": "123e4567-e89b-12d3-a456-426614174003",
                "over_id": "123e4567-e89b-12d3-a456-426614174005",
                "ball_number": 15.4,
                "bowler_user_id": "123e4567-e89b-12d3-a456-426614174001",
                "batsman_user_id": "123e4567-e89b-12d3-a456-426614174000",
                "non_striker_user_id": "123e4567-e89b-12d3-a456-426614174002",
                "runs_scored": 4,
                "is_wicket": False,
                "is_boundary": True,
                "boundary_type": "FOUR",
                "is_legal_delivery": True,
                "extra_type": "NONE",
                "extra_runs": 0,
                "shot_type": "DRIVE"
            }
        }
    )


class WicketDetailsSchema(BaseModel):
    """
    Wicket dismissal details
    
    Attached to BallCreateRequest when is_wicket=True
    Creates linked Wicket record in database
    """
    batsman_out_user_id: UUID = Field(
        ...,
        description="Batsman who got out"
    )
    dismissal_type: DismissalType = Field(
        ...,
        description="How batsman was dismissed"
    )
    bowler_user_id: Optional[UUID] = Field(
        None,
        description="Bowler who got wicket (null for run-outs)"
    )
    fielder_user_id: Optional[UUID] = Field(
        None,
        description="Fielder who caught/stumped (if applicable)"
    )
    fielder2_user_id: Optional[UUID] = Field(
        None,
        description="Second fielder (for relay catches)"
    )
    wicket_number: int = Field(
        ...,
        ge=1,
        le=10,
        description="Wicket number in innings (1-10)"
    )
    team_score_at_wicket: int = Field(
        ...,
        ge=0,
        description="Team score when wicket fell (e.g., 45 in '45/3')"
    )
    partnership_runs: int = Field(
        default=0,
        ge=0,
        description="Runs scored in partnership"
    )
    
    @field_validator('wicket_number')
    @classmethod
    def validate_wicket_number(cls, v: int) -> int:
        """Ensure wicket number is 1-10"""
        if v < 1 or v > 10:
            raise ValueError("Wicket number must be between 1 and 10")
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "batsman_out_user_id": "123e4567-e89b-12d3-a456-426614174000",
                "dismissal_type": "CAUGHT",
                "bowler_user_id": "123e4567-e89b-12d3-a456-426614174001",
                "fielder_user_id": "123e4567-e89b-12d3-a456-426614174006",
                "wicket_number": 3,
                "team_score_at_wicket": 45,
                "partnership_runs": 28
            }
        }
    )


# ============================================================================
# BALL RESPONSE SCHEMAS
# ============================================================================

class BallResponse(BaseModel):
    """
    Response schema for ball details
    
    Returns full ball record with all metadata
    """
    id: UUID = Field(..., description="Ball ID")
    innings_id: UUID = Field(..., description="Innings ID")
    over_id: UUID = Field(..., description="Over ID")
    ball_number: float = Field(..., description="Ball number (over.ball)")
    
    # Players
    bowler_user_id: UUID = Field(..., description="Bowler ID")
    batsman_user_id: UUID = Field(..., description="Batsman on strike ID")
    non_striker_user_id: Optional[UUID] = Field(None, description="Non-striker ID")
    
    bowler_name: Optional[str] = Field(None, description="Bowler name")
    batsman_name: Optional[str] = Field(None, description="Batsman name")
    non_striker_name: Optional[str] = Field(None, description="Non-striker name")
    
    # Outcome
    runs_scored: int = Field(..., description="Runs off bat")
    is_wicket: bool = Field(..., description="Wicket fell")
    is_boundary: bool = Field(..., description="Boundary scored")
    boundary_type: Optional[BoundaryType] = Field(None, description="Boundary type")
    
    # Extras
    is_legal_delivery: bool = Field(..., description="Legal delivery")
    extra_type: ExtraType = Field(..., description="Extra type")
    extra_runs: int = Field(..., description="Extra runs")
    
    # Analytics
    shot_type: Optional[ShotType] = Field(None, description="Shot played")
    fielding_position: Optional[str] = Field(None, description="Fielding position")
    wagon_wheel_data: Optional[Dict[str, Any]] = Field(None, description="Trajectory data")
    
    # Milestones
    is_milestone: bool = Field(..., description="Milestone achieved")
    milestone_type: Optional[str] = Field(None, description="Milestone type")
    
    # Validation
    validation_source: str = Field(..., description="Validation source")
    validation_confidence: float = Field(..., description="Confidence score (0-1)")
    
    # Timing
    bowled_at: datetime = Field(..., description="When ball was bowled")
    created_at: datetime = Field(..., description="Record created at")
    
    # Wicket details (populated if is_wicket=True)
    wicket: Optional['WicketResponse'] = Field(
        None,
        description="Wicket details (if is_wicket=True)"
    )
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174007",
                "innings_id": "123e4567-e89b-12d3-a456-426614174003",
                "over_id": "123e4567-e89b-12d3-a456-426614174005",
                "ball_number": 15.4,
                "bowler_user_id": "123e4567-e89b-12d3-a456-426614174001",
                "batsman_user_id": "123e4567-e89b-12d3-a456-426614174000",
                "bowler_name": "Jasprit Bumrah",
                "batsman_name": "Virat Kohli",
                "runs_scored": 4,
                "is_wicket": False,
                "is_boundary": True,
                "boundary_type": "FOUR",
                "is_legal_delivery": True,
                "extra_type": "NONE",
                "extra_runs": 0,
                "shot_type": "DRIVE",
                "validation_source": "dual_scorer",
                "validation_confidence": 1.0,
                "bowled_at": "2025-10-31T15:32:45Z",
                "created_at": "2025-10-31T15:32:45Z"
            }
        }
    )


class WicketResponse(BaseModel):
    """
    Response schema for wicket details
    
    Returned as nested object in BallResponse when is_wicket=True
    """
    id: UUID = Field(..., description="Wicket ID")
    ball_id: UUID = Field(..., description="Ball ID")
    innings_id: UUID = Field(..., description="Innings ID")
    
    batsman_out_user_id: UUID = Field(..., description="Batsman out ID")
    batsman_out_name: Optional[str] = Field(None, description="Batsman out name")
    
    dismissal_type: DismissalType = Field(..., description="Dismissal type")
    
    # Credits
    bowler_user_id: Optional[UUID] = Field(None, description="Bowler ID")
    fielder_user_id: Optional[UUID] = Field(None, description="Fielder ID")
    fielder2_user_id: Optional[UUID] = Field(None, description="Second fielder ID")
    
    bowler_name: Optional[str] = Field(None, description="Bowler name")
    fielder_name: Optional[str] = Field(None, description="Fielder name")
    fielder2_name: Optional[str] = Field(None, description="Second fielder name")
    
    # Context
    wicket_number: int = Field(..., description="Wicket number (1-10)")
    team_score_at_wicket: int = Field(..., description="Team score at wicket")
    partnership_runs: int = Field(..., description="Partnership runs")
    
    # Timing
    dismissed_at: datetime = Field(..., description="Dismissal time")
    created_at: datetime = Field(..., description="Record created")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174008",
                "ball_id": "123e4567-e89b-12d3-a456-426614174007",
                "innings_id": "123e4567-e89b-12d3-a456-426614174003",
                "batsman_out_user_id": "123e4567-e89b-12d3-a456-426614174000",
                "batsman_out_name": "Virat Kohli",
                "dismissal_type": "CAUGHT",
                "bowler_user_id": "123e4567-e89b-12d3-a456-426614174001",
                "fielder_user_id": "123e4567-e89b-12d3-a456-426614174006",
                "bowler_name": "Jasprit Bumrah",
                "fielder_name": "Ravindra Jadeja",
                "wicket_number": 3,
                "team_score_at_wicket": 145,
                "partnership_runs": 68,
                "dismissed_at": "2025-10-31T15:32:45Z",
                "created_at": "2025-10-31T15:32:45Z"
            }
        }
    )


# ============================================================================
# BALL EVENT SCHEMAS (FOR WEBSOCKET)
# ============================================================================

class BallEventSchema(BaseModel):
    """
    Real-time ball event for WebSocket broadcasting
    
    Broadcasted to all connected clients when ball is bowled
    Includes ball details + updated innings state
    
    WebSocket message format:
    {
        "type": "BALL_BOWLED",
        "data": <BallEventSchema>,
        "timestamp": "2025-10-31T15:32:45Z"
    }
    """
    ball: BallResponse = Field(
        ...,
        description="Full ball details"
    )
    
    # Updated innings state after this ball
    innings_state: Dict[str, Any] = Field(
        ...,
        description="Updated innings state (runs, wickets, overs)",
        examples=[{
            "current_score": "145/4",
            "overs_bowled": 15.4,
            "run_rate": 9.35
        }]
    )
    
    # Over summary (if over just completed)
    over_summary: Optional[Dict[str, Any]] = Field(
        None,
        description="Over summary (if ball completed the over)",
        examples=[{
            "over_number": 15,
            "runs_conceded": 8,
            "wickets_taken": 1,
            "ball_sequence": ["1", "W", "0", "4", "1", "wd", "2"]
        }]
    )
    
    # Milestone info (if achieved)
    milestone: Optional[Dict[str, Any]] = Field(
        None,
        description="Milestone details (if achieved)",
        examples=[{
            "type": "fifty",
            "player_name": "Virat Kohli",
            "runs": 50,
            "balls": 32
        }]
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "ball": {
                    "id": "123e4567-e89b-12d3-a456-426614174007",
                    "ball_number": 15.4,
                    "runs_scored": 4,
                    "is_boundary": True
                },
                "innings_state": {
                    "current_score": "145/4",
                    "overs_bowled": 15.4,
                    "run_rate": 9.35
                },
                "over_summary": None,
                "milestone": None
            }
        }
    )


# ============================================================================
# AGGREGATED BALL STATISTICS
# ============================================================================

class BallStatisticsSchema(BaseModel):
    """
    Aggregated statistics for an innings (derived from balls)
    
    Used for match summaries and analysis
    """
    total_balls: int = Field(..., description="Total balls bowled")
    legal_deliveries: int = Field(..., description="Legal deliveries")
    runs_from_bat: int = Field(..., description="Runs off the bat")
    extras_total: int = Field(..., description="Total extras")
    boundaries: int = Field(..., description="Total boundaries (4s + 6s)")
    fours: int = Field(..., description="Fours hit")
    sixes: int = Field(..., description="Sixes hit")
    wickets: int = Field(..., description="Wickets fallen")
    dot_balls: int = Field(..., description="Dot balls (0 runs)")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_balls": 120,
                "legal_deliveries": 116,
                "runs_from_bat": 165,
                "extras_total": 15,
                "boundaries": 18,
                "fours": 14,
                "sixes": 4,
                "wickets": 5,
                "dot_balls": 42
            }
        }
    )
