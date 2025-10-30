"""
Pydantic schemas for Cricket Matches

This module provides request/response schemas for:
- Match creation and management
- Toss configuration
- Playing XI selection
- Match officials assignment
- JSONB field validation (match_rules, venue, weather_conditions)

Following event sourcing pattern from copilot-instructions.md:
- Match state transitions: SCHEDULED → TOSS_PENDING → LIVE → COMPLETED
- Immutable match setup once started
- Comprehensive JSONB validation before DB insertion
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, ConfigDict

from src.models.enums import (
    SportType,
    MatchType,
    MatchCategory,
    MatchStatus,
    MatchVisibility,
    ResultType,
    ElectedTo,
    OfficialRole,
    OfficialAssignment,
)


# ============================================================================
# JSONB NESTED MODELS
# ============================================================================

class MatchRulesSchema(BaseModel):
    """
    Match configuration rules (stored as JSONB in matches.match_rules)
    
    Provides ultimate flexibility for different match formats:
    - Standard formats: T20, ODI, Test
    - Custom formats: 8-a-side, 15-overs, gully cricket
    
    Example T20:
        {"players_per_team": 11, "overs_per_side": 20, "balls_per_over": 6,
         "wickets_to_fall": 10, "powerplay_overs": 6}
    """
    players_per_team: int = Field(
        default=11,
        ge=2,
        le=15,
        description="Number of players per team (2-15 for flexibility)"
    )
    overs_per_side: Optional[int] = Field(
        default=20,
        ge=1,
        le=50,
        description="Overs per innings (None for unlimited)"
    )
    balls_per_over: int = Field(
        default=6,
        ge=4,
        le=8,
        description="Balls per over (usually 6, can be 8 for custom)"
    )
    wickets_to_fall: int = Field(
        default=10,
        ge=1,
        le=14,
        description="Wickets needed to end innings"
    )
    powerplay_overs: Optional[int] = Field(
        None,
        ge=0,
        le=20,
        description="Number of powerplay overs (field restrictions)"
    )
    death_overs_start: Optional[int] = Field(
        None,
        ge=1,
        le=50,
        description="Over number when death overs start"
    )
    allow_same_bowler_consecutive: bool = Field(
        default=False,
        description="Allow same bowler to bowl consecutive overs"
    )
    retire_after_runs: Optional[int] = Field(
        None,
        ge=25,
        le=200,
        description="Batsman must retire after scoring X runs (gully cricket)"
    )
    mandatory_bowling: bool = Field(
        default=False,
        description="All players must bowl minimum overs"
    )
    dls_applicable: bool = Field(
        default=False,
        description="Use Duckworth-Lewis-Stern for rain interruptions"
    )
    super_over_if_tie: bool = Field(
        default=False,
        description="Play super over if match tied"
    )
    boundary_count_rule: bool = Field(
        default=False,
        description="Use boundary count as tiebreaker (2019 WC rule)"
    )

    @field_validator('wickets_to_fall')
    @classmethod
    def validate_wickets(cls, v: int, info) -> int:
        """Wickets to fall must be <= players_per_team - 1"""
        data = info.data
        if 'players_per_team' in data and v >= data['players_per_team']:
            raise ValueError(f"wickets_to_fall ({v}) must be < players_per_team ({data['players_per_team']})")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "players_per_team": 11,
                "overs_per_side": 20,
                "balls_per_over": 6,
                "wickets_to_fall": 10,
                "powerplay_overs": 6,
                "death_overs_start": 16,
                "super_over_if_tie": True
            }
        }
    )


class VenueSchema(BaseModel):
    """
    Match venue details (stored as JSONB in matches.venue)
    
    Used for: Match location, spectator discovery, weather tracking
    """
    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Venue name",
        examples=["Eden Gardens", "Local Park Ground"]
    )
    city: Optional[str] = Field(
        None,
        max_length=100,
        description="City name"
    )
    state: Optional[str] = Field(
        None,
        max_length=100,
        description="State/Province"
    )
    country: Optional[str] = Field(
        None,
        max_length=100,
        description="Country name"
    )
    latitude: Optional[float] = Field(
        None,
        ge=-90.0,
        le=90.0,
        description="Latitude for map display"
    )
    longitude: Optional[float] = Field(
        None,
        ge=-180.0,
        le=180.0,
        description="Longitude for map display"
    )
    ground_type: Optional[str] = Field(
        None,
        max_length=50,
        description="Ground surface type",
        examples=["turf", "matting", "concrete", "astroturf"]
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Wankhede Stadium",
                "city": "Mumbai",
                "state": "Maharashtra",
                "country": "India",
                "latitude": 18.9388,
                "longitude": 72.8258,
                "ground_type": "turf"
            }
        }
    )


class WeatherConditionsSchema(BaseModel):
    """
    Weather conditions during match (stored as JSONB in matches.weather_conditions)
    
    Optional metadata for match context
    """
    temperature: Optional[float] = Field(
        None,
        ge=-20.0,
        le=60.0,
        description="Temperature in Celsius"
    )
    humidity: Optional[int] = Field(
        None,
        ge=0,
        le=100,
        description="Humidity percentage"
    )
    wind_speed: Optional[float] = Field(
        None,
        ge=0.0,
        le=200.0,
        description="Wind speed in km/h"
    )
    conditions: Optional[str] = Field(
        None,
        max_length=50,
        description="Weather description",
        examples=["sunny", "cloudy", "overcast", "drizzle", "rain"]
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "temperature": 28.5,
                "humidity": 65,
                "wind_speed": 12.0,
                "conditions": "partly cloudy"
            }
        }
    )


# ============================================================================
# MATCH REQUEST SCHEMAS
# ============================================================================

class MatchCreateRequest(BaseModel):
    """
    Request schema for creating a new match
    
    Required: team_a_id, team_b_id, match_type, venue, scheduled_start_time
    Optional: match_rules (defaults to standard format), visibility, officials
    
    Workflow:
        1. Create match (status=SCHEDULED)
        2. Assign officials (scorers, umpires)
        3. Conduct toss (status=TOSS_PENDING → LIVE)
        4. Set playing XI
        5. Start match (status=LIVE)
    """
    team_a_id: UUID = Field(..., description="First team ID")
    team_b_id: UUID = Field(..., description="Second team ID")
    match_type: MatchType = Field(..., description="Match format (T20, ODI, CUSTOM)")
    match_category: MatchCategory = Field(
        default=MatchCategory.CASUAL,
        description="Match organization level"
    )
    match_rules: Optional[MatchRulesSchema] = Field(
        None,
        description="Match configuration (auto-filled for standard formats if not provided)"
    )
    venue: VenueSchema = Field(..., description="Match venue details")
    scheduled_start_time: datetime = Field(
        ...,
        description="Scheduled match start time (timezone-aware)"
    )
    visibility: MatchVisibility = Field(
        default=MatchVisibility.PUBLIC,
        description="Who can view this match"
    )
    tournament_id: Optional[UUID] = Field(
        None,
        description="Tournament ID if part of tournament (Phase 2)"
    )
    round_name: Optional[str] = Field(
        None,
        max_length=100,
        description="Tournament round name (e.g., 'Quarter Final')"
    )

    @field_validator('team_b_id')
    @classmethod
    def validate_different_teams(cls, v: UUID, info) -> UUID:
        """Ensure team_a_id != team_b_id"""
        data = info.data
        if 'team_a_id' in data and v == data['team_a_id']:
            raise ValueError("team_a_id and team_b_id must be different")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "team_a_id": "123e4567-e89b-12d3-a456-426614174000",
                "team_b_id": "123e4567-e89b-12d3-a456-426614174001",
                "match_type": "t20",
                "match_category": "tournament",
                "match_rules": {
                    "players_per_team": 11,
                    "overs_per_side": 20,
                    "balls_per_over": 6,
                    "wickets_to_fall": 10,
                    "powerplay_overs": 6
                },
                "venue": {
                    "name": "Eden Gardens",
                    "city": "Kolkata",
                    "country": "India"
                },
                "scheduled_start_time": "2024-02-15T14:00:00+05:30",
                "visibility": "public"
            }
        }
    )


class MatchUpdateRequest(BaseModel):
    """
    Request schema for updating match details
    
    Only allowed before match starts (status=SCHEDULED or TOSS_PENDING)
    Restricted to: Match creator
    """
    match_type: Optional[MatchType] = Field(None, description="Updated match format")
    match_category: Optional[MatchCategory] = Field(None, description="Updated category")
    match_rules: Optional[MatchRulesSchema] = Field(None, description="Updated match rules")
    venue: Optional[VenueSchema] = Field(None, description="Updated venue")
    scheduled_start_time: Optional[datetime] = Field(None, description="Rescheduled time")
    visibility: Optional[MatchVisibility] = Field(None, description="Updated visibility")
    weather_conditions: Optional[WeatherConditionsSchema] = Field(None, description="Weather update")
    pitch_report: Optional[str] = Field(None, max_length=1000, description="Pitch condition notes")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "scheduled_start_time": "2024-02-15T15:00:00+05:30",
                "weather_conditions": {
                    "temperature": 30.0,
                    "conditions": "sunny"
                }
            }
        }
    )


class TossRequest(BaseModel):
    """
    Request schema for conducting match toss
    
    Required: toss_won_by_team_id, elected_to
    Validates: Team must be one of the match teams
    
    Side effect: Updates match status to LIVE (or LINEUP_PENDING if playing XI not set)
    """
    toss_won_by_team_id: UUID = Field(
        ...,
        description="Team that won the toss (must be team_a_id or team_b_id)"
    )
    elected_to: ElectedTo = Field(
        ...,
        description="Toss winner's decision (bat or bowl)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "toss_won_by_team_id": "123e4567-e89b-12d3-a456-426614174000",
                "elected_to": "bat"
            }
        }
    )


class PlayingXIPlayerRequest(BaseModel):
    """
    Schema for a single player in playing XI
    
    Used in: PlayingXIRequest (list of players)
    """
    user_id: UUID = Field(..., description="User ID (must be team member)")
    cricket_profile_id: Optional[UUID] = Field(None, description="Cricket profile ID")
    can_bat: bool = Field(default=True, description="Can bat in this match")
    can_bowl: bool = Field(default=True, description="Can bowl in this match")
    is_wicket_keeper: bool = Field(default=False, description="Is wicket keeper")
    is_captain: bool = Field(default=False, description="Is team captain")
    batting_position: Optional[int] = Field(
        None,
        ge=1,
        le=11,
        description="Batting order position (1-11)"
    )
    bowling_preference: Optional[int] = Field(
        None,
        ge=1,
        le=11,
        description="Bowling preference order"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "can_bat": True,
                "can_bowl": True,
                "is_captain": True,
                "batting_position": 3
            }
        }
    )


class PlayingXIRequest(BaseModel):
    """
    Request schema for setting playing XI for a team
    
    Required: team_id, players list
    Validates:
        - Team must be match participant
        - All players must be team members
        - Player count matches match_rules.players_per_team
        - Exactly one captain
        - Exactly one wicket keeper (for standard formats)
    """
    team_id: UUID = Field(..., description="Team ID (team_a_id or team_b_id)")
    players: List[PlayingXIPlayerRequest] = Field(
        ...,
        min_length=2,
        max_length=15,
        description="List of playing XI members"
    )

    @field_validator('players')
    @classmethod
    def validate_players(cls, v: List[PlayingXIPlayerRequest]) -> List[PlayingXIPlayerRequest]:
        """Validate playing XI constraints"""
        if not v:
            raise ValueError("Playing XI cannot be empty")
        
        # Check for duplicate players
        user_ids = [p.user_id for p in v]
        if len(user_ids) != len(set(user_ids)):
            raise ValueError("Duplicate players in playing XI")
        
        # Exactly one captain
        captains = [p for p in v if p.is_captain]
        if len(captains) != 1:
            raise ValueError("Playing XI must have exactly one captain")
        
        # At least one wicket keeper (recommended, not enforced for casual)
        wicket_keepers = [p for p in v if p.is_wicket_keeper]
        if not wicket_keepers:
            # Warning, not error (gully cricket may not have designated WK)
            pass
        
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "team_id": "123e4567-e89b-12d3-a456-426614174000",
                "players": [
                    {
                        "user_id": "123e4567-e89b-12d3-a456-426614174010",
                        "is_captain": True,
                        "batting_position": 3
                    },
                    {
                        "user_id": "123e4567-e89b-12d3-a456-426614174011",
                        "is_wicket_keeper": True,
                        "batting_position": 1
                    }
                ]
            }
        }
    )


class MatchOfficialRequest(BaseModel):
    """
    Request schema for assigning match official
    
    Used for: Scorers, umpires, third umpire, match referee
    """
    user_id: UUID = Field(..., description="Official's user ID")
    role: OfficialRole = Field(..., description="Official's role")
    assignment: Optional[OfficialAssignment] = Field(
        default=OfficialAssignment.NEUTRAL,
        description="Team assignment (team_a, team_b, neutral)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174020",
                "role": "scorer",
                "assignment": "team_a"
            }
        }
    )


# ============================================================================
# MATCH RESPONSE SCHEMAS
# ============================================================================

class MatchOfficialResponse(BaseModel):
    """Response schema for match official"""
    id: UUID = Field(..., description="Official assignment ID")
    match_id: UUID = Field(..., description="Match ID")
    user_id: UUID = Field(..., description="Official user ID")
    role: OfficialRole = Field(..., description="Official role")
    assignment: Optional[OfficialAssignment] = Field(None, description="Team assignment")
    is_active: bool = Field(..., description="Currently active")
    joined_at: datetime = Field(..., description="When official joined")
    
    # Populated by service layer
    user_name: Optional[str] = Field(None, description="Official name")

    model_config = ConfigDict(from_attributes=True)


class PlayingXIResponse(BaseModel):
    """Response schema for playing XI member"""
    id: UUID = Field(..., description="Playing XI record ID")
    match_id: UUID = Field(..., description="Match ID")
    team_id: UUID = Field(..., description="Team ID")
    user_id: UUID = Field(..., description="Player user ID")
    cricket_profile_id: Optional[UUID] = Field(None, description="Cricket profile ID")
    can_bat: bool = Field(..., description="Can bat")
    can_bowl: bool = Field(..., description="Can bowl")
    is_wicket_keeper: bool = Field(..., description="Is wicket keeper")
    is_captain: bool = Field(..., description="Is captain")
    batting_position: Optional[int] = Field(None, description="Batting position")
    bowling_preference: Optional[int] = Field(None, description="Bowling preference")
    played: bool = Field(..., description="Actually played")
    
    # Populated by service layer
    user_name: Optional[str] = Field(None, description="Player name")

    model_config = ConfigDict(from_attributes=True)


class MatchResponse(BaseModel):
    """
    Response schema for match details
    
    Includes: Match info, teams, toss, status, schedule
    Used in: Match list, detail endpoints
    """
    id: UUID = Field(..., description="Match ID")
    sport_type: SportType = Field(..., description="Sport type")
    match_type: MatchType = Field(..., description="Match format")
    match_category: MatchCategory = Field(..., description="Match category")
    match_rules: MatchRulesSchema = Field(..., description="Match configuration")
    match_code: Optional[str] = Field(None, description="Public match code (e.g., KRD-AB12)")
    
    # Teams
    team_a_id: UUID = Field(..., description="Team A ID")
    team_b_id: UUID = Field(..., description="Team B ID")
    
    # Toss
    toss_won_by_team_id: Optional[UUID] = Field(None, description="Toss winner team ID")
    elected_to: Optional[ElectedTo] = Field(None, description="Toss decision")
    toss_completed_at: Optional[datetime] = Field(None, description="Toss completion time")
    
    # Venue & Schedule
    venue: VenueSchema = Field(..., description="Match venue")
    scheduled_start_time: datetime = Field(..., description="Scheduled start")
    actual_start_time: Optional[datetime] = Field(None, description="Actual start")
    estimated_end_time: Optional[datetime] = Field(None, description="Estimated end")
    actual_end_time: Optional[datetime] = Field(None, description="Actual end")
    
    # Status
    match_status: MatchStatus = Field(..., description="Current match status")
    visibility: MatchVisibility = Field(..., description="Visibility level")
    is_featured: bool = Field(..., description="Featured match")
    
    # Result
    winning_team_id: Optional[UUID] = Field(None, description="Winning team ID")
    result_type: Optional[ResultType] = Field(None, description="Result type")
    result_margin: Optional[str] = Field(None, description="Result description")
    player_of_match_user_id: Optional[UUID] = Field(None, description="Player of match")
    
    # Metadata
    created_by_user_id: UUID = Field(..., description="Match creator")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update")
    
    # Populated by service layer
    team_a_name: Optional[str] = Field(None, description="Team A name")
    team_b_name: Optional[str] = Field(None, description="Team B name")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "sport_type": "cricket",
                "match_type": "t20",
                "match_category": "tournament",
                "match_code": "KRD-AB12",
                "team_a_id": "123e4567-e89b-12d3-a456-426614174001",
                "team_b_id": "123e4567-e89b-12d3-a456-426614174002",
                "match_status": "scheduled",
                "scheduled_start_time": "2024-02-15T14:00:00+05:30",
                "team_a_name": "Mumbai Indians",
                "team_b_name": "Chennai Super Kings"
            }
        }
    )


class MatchDetailResponse(MatchResponse):
    """
    Extended match response with officials and playing XI
    
    Includes: All match info + officials + playing XI rosters
    Used in: GET /matches/{match_id} endpoint
    """
    officials: List[MatchOfficialResponse] = Field(
        default=[],
        description="Match officials (scorers, umpires)"
    )
    playing_xi: List[PlayingXIResponse] = Field(
        default=[],
        description="Playing XI for both teams"
    )
    weather_conditions: Optional[WeatherConditionsSchema] = Field(
        None,
        description="Weather conditions"
    )
    pitch_report: Optional[str] = Field(None, description="Pitch report")

    model_config = ConfigDict(from_attributes=True)


class MatchListResponse(BaseModel):
    """
    Paginated response for match list
    
    Used in: GET /matches endpoint (search/filter)
    """
    matches: List[MatchResponse] = Field(..., description="List of matches")
    total: int = Field(..., description="Total matches matching criteria")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "matches": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "match_type": "t20",
                        "match_code": "KRD-AB12",
                        "team_a_name": "Mumbai Indians",
                        "team_b_name": "Chennai Super Kings",
                        "match_status": "scheduled",
                        "scheduled_start_time": "2024-02-15T14:00:00+05:30"
                    }
                ],
                "total": 25,
                "page": 1,
                "page_size": 10
            }
        }
    )
