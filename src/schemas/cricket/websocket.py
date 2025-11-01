"""
WebSocket Event Schemas for Live Cricket Scoring

Pydantic models for WebSocket events broadcast during live matches.
All events follow a consistent structure with type, data, and timestamp.

Author: AI Coding Agent (Professional Standards)
Date: November 1, 2025
"""

from pydantic import BaseModel, Field, UUID4
from typing import Optional, List, Literal
from datetime import datetime
from enum import Enum


# ============================================================================
# Base WebSocket Message
# ============================================================================

class WebSocketMessage(BaseModel):
    """
    Base WebSocket message structure.
    
    All WebSocket events follow this pattern:
    - type: Event type identifier
    - data: Event-specific payload
    - timestamp: Server timestamp in ISO 8601 format
    """
    type: str = Field(..., description="Event type identifier")
    data: dict = Field(..., description="Event-specific data")
    timestamp: str = Field(..., description="Server timestamp (ISO 8601)")


# ============================================================================
# Player Stats Schemas (reused across events)
# ============================================================================

class PlayerStatsSchema(BaseModel):
    """Basic player information for events."""
    player_id: UUID4
    player_name: str


class BatsmanStatsSchema(PlayerStatsSchema):
    """Batsman statistics in an event."""
    runs: int
    balls: int
    fours: Optional[int] = None
    sixes: Optional[int] = None
    strike_rate: Optional[float] = None


class BowlerStatsSchema(PlayerStatsSchema):
    """Bowler statistics in an event."""
    overs: float
    runs: int
    wickets: int
    economy: Optional[float] = None


# ============================================================================
# Innings State Schema (current match state)
# ============================================================================

class InningsStateSchema(BaseModel):
    """Current innings state included in multiple events."""
    score: str = Field(..., description="Score in format '145/4'")
    overs: float = Field(..., description="Overs bowled (e.g., 15.3)")
    run_rate: float = Field(..., description="Current run rate")
    required_rate: Optional[float] = Field(None, description="Required rate (2nd innings only)")
    wickets: Optional[int] = Field(None, description="Wickets fallen")
    last_6_overs_rate: Optional[float] = Field(None, description="Run rate in last 6 overs")


# ============================================================================
# Event 1: CONNECTION_ESTABLISHED
# ============================================================================

class CurrentInningsData(BaseModel):
    """Current innings information sent on connection."""
    innings_number: int
    batting_team_id: UUID4
    batting_team_name: str
    bowling_team_id: UUID4
    bowling_team_name: str
    score: str
    overs: float
    run_rate: float
    required_rate: Optional[float] = None


class ConnectionEstablishedData(BaseModel):
    """Data sent when WebSocket connection is established."""
    match_id: UUID4
    match_code: str
    match_status: str
    current_innings: Optional[CurrentInningsData] = None
    striker: Optional[BatsmanStatsSchema] = None
    non_striker: Optional[BatsmanStatsSchema] = None
    bowler: Optional[BowlerStatsSchema] = None


# ============================================================================
# Event 2: BALL_BOWLED
# ============================================================================

class BallBowledData(BaseModel):
    """Data for BALL_BOWLED event."""
    ball_id: UUID4
    innings_id: UUID4
    over_number: int
    ball_number: int
    bowler: PlayerStatsSchema
    batsman: PlayerStatsSchema
    runs_scored: int
    is_boundary: bool
    boundary_type: Optional[Literal["FOUR", "SIX"]] = None
    extras: Optional[dict] = None
    is_wicket: bool
    innings_state: InningsStateSchema
    batsman_stats: BatsmanStatsSchema
    bowler_stats: BowlerStatsSchema
    commentary: Optional[str] = None


# ============================================================================
# Event 3: WICKET_FALLEN
# ============================================================================

class PartnershipSchema(BaseModel):
    """Partnership information."""
    runs: int
    balls: int
    partner: str


class WicketFallenData(BaseModel):
    """Data for WICKET_FALLEN event."""
    ball_id: UUID4
    wicket_id: UUID4
    dismissal_type: str
    batsman_out: BatsmanStatsSchema
    bowler: PlayerStatsSchema
    fielder: Optional[PlayerStatsSchema] = None
    innings_state: InningsStateSchema
    fall_of_wicket: str = Field(..., description="e.g., '149/5 (15.4 overs)'")
    partnership: Optional[PartnershipSchema] = None
    commentary: Optional[str] = None


# ============================================================================
# Event 4: OVER_COMPLETE
# ============================================================================

class OverCompleteData(BaseModel):
    """Data for OVER_COMPLETE event."""
    innings_id: UUID4
    over_number: int
    bowler: PlayerStatsSchema
    runs_in_over: int
    wickets_in_over: int
    balls_summary: List[str] = Field(..., description="e.g., ['1', '0', '4', 'W', '0', '2']")
    innings_state: InningsStateSchema
    next_bowler: Optional[PlayerStatsSchema] = None


# ============================================================================
# Event 5: INNINGS_COMPLETE
# ============================================================================

class TopScorerSchema(BaseModel):
    """Top scorer information."""
    player_name: str
    runs: int
    balls: int


class TopBowlerSchema(BaseModel):
    """Top bowler information."""
    player_name: str
    wickets: int
    runs: int
    overs: float


class ExtrasSchema(BaseModel):
    """Extras breakdown."""
    wides: int
    no_balls: int
    byes: int
    leg_byes: int
    total: int


class NextInningsSchema(BaseModel):
    """Next innings information."""
    innings_number: int
    batting_team: str
    target: Optional[int] = None
    target_message: Optional[str] = None


class InningsCompleteData(BaseModel):
    """Data for INNINGS_COMPLETE event."""
    innings_id: UUID4
    innings_number: int
    batting_team: PlayerStatsSchema  # Using PlayerStatsSchema for team (has id and name)
    final_score: str = Field(..., description="e.g., '189/7'")
    overs: float
    extras: ExtrasSchema
    top_scorers: List[TopScorerSchema]
    top_bowlers: List[TopBowlerSchema]
    next_innings: Optional[NextInningsSchema] = None


# ============================================================================
# Event 6: MATCH_COMPLETE
# ============================================================================

class MarginSchema(BaseModel):
    """Match result margin."""
    type: Literal["RUNS", "WICKETS", "TIED", "NO_RESULT"]
    value: Optional[int] = None


class InningsScoreSchema(BaseModel):
    """Final innings score."""
    team: str
    score: str = Field(..., description="e.g., '189/7 (20.0)'")


class FinalScoresSchema(BaseModel):
    """Both innings final scores."""
    innings_1: InningsScoreSchema
    innings_2: InningsScoreSchema


class PlayerOfMatchSchema(BaseModel):
    """Player of the match."""
    player_id: UUID4
    player_name: str
    reason: str = Field(..., description="e.g., '78 runs from 52 balls'")


class MatchCompleteData(BaseModel):
    """Data for MATCH_COMPLETE event."""
    match_id: UUID4
    match_code: str
    result: str = Field(..., description="e.g., 'India won by 15 runs'")
    winner_team_id: Optional[UUID4] = None
    winner_team_name: Optional[str] = None
    margin: MarginSchema
    player_of_match: Optional[PlayerOfMatchSchema] = None
    final_scores: FinalScoresSchema
    match_highlights: Optional[List[str]] = None


# ============================================================================
# Event 7: SCORING_DISPUTE_RAISED
# ============================================================================

class ScorerVersionSchema(BaseModel):
    """Scorer's version of ball data."""
    runs_scored: int
    extras: Optional[dict] = None


class ScoringDisputeRaisedData(BaseModel):
    """Data for SCORING_DISPUTE_RAISED event."""
    dispute_id: UUID4
    ball_id: Optional[UUID4] = None
    innings_id: UUID4
    over_number: int
    ball_number: int
    scorer_a_version: ScorerVersionSchema
    scorer_b_version: ScorerVersionSchema
    status: Literal["PENDING_RESOLUTION"]
    message: str


# ============================================================================
# Event 8: DISPUTE_RESOLVED
# ============================================================================

class DisputeResolutionSchema(BaseModel):
    """Dispute resolution details."""
    runs_scored: int
    extras: Optional[dict] = None
    resolved_by: Literal["UMPIRE", "MAJORITY_VOTE", "CAPTAIN", "VIDEO_REVIEW"]
    resolver_name: Optional[str] = None


class DisputeResolvedData(BaseModel):
    """Data for DISPUTE_RESOLVED event."""
    dispute_id: UUID4
    ball_id: UUID4
    resolution: DisputeResolutionSchema
    message: str


# ============================================================================
# Event 9: PLAYER_CHANGED
# ============================================================================

class PlayerChangedData(BaseModel):
    """Data for PLAYER_CHANGED event."""
    change_type: Literal["BATSMAN", "BOWLER"]
    reason: Literal["WICKET", "END_OF_OVER", "INJURY", "TACTICAL"]
    player_out: Optional[PlayerStatsSchema] = None
    player_in: PlayerStatsSchema
    batting_position: Optional[int] = None


# ============================================================================
# Event 10: MILESTONE_ACHIEVED
# ============================================================================

class MilestoneStatsSchema(BaseModel):
    """Statistics for milestone achievement."""
    runs: Optional[int] = None
    balls: Optional[int] = None
    fours: Optional[int] = None
    sixes: Optional[int] = None
    wickets: Optional[int] = None
    overs: Optional[float] = None


class MilestoneAchievedData(BaseModel):
    """Data for MILESTONE_ACHIEVED event."""
    milestone_type: Literal[
        "FIFTY", 
        "CENTURY", 
        "HAT_TRICK", 
        "FIVE_WICKETS",
        "TEAM_100",
        "TEAM_200"
    ]
    player: Optional[PlayerStatsSchema] = None
    stats: MilestoneStatsSchema
    message: str


# ============================================================================
# Event 11: ERROR
# ============================================================================

class ErrorData(BaseModel):
    """Data for ERROR event."""
    error_code: str
    message: str


# ============================================================================
# Event Type Enum
# ============================================================================

class WebSocketEventType(str, Enum):
    """All supported WebSocket event types."""
    CONNECTION_ESTABLISHED = "CONNECTION_ESTABLISHED"
    BALL_BOWLED = "BALL_BOWLED"
    WICKET_FALLEN = "WICKET_FALLEN"
    OVER_COMPLETE = "OVER_COMPLETE"
    INNINGS_COMPLETE = "INNINGS_COMPLETE"
    MATCH_COMPLETE = "MATCH_COMPLETE"
    SCORING_DISPUTE_RAISED = "SCORING_DISPUTE_RAISED"
    DISPUTE_RESOLVED = "DISPUTE_RESOLVED"
    PLAYER_CHANGED = "PLAYER_CHANGED"
    MILESTONE_ACHIEVED = "MILESTONE_ACHIEVED"
    ERROR = "ERROR"
