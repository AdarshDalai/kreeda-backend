"""
Cricket Profile Schemas
Pydantic models for sport profiles and cricket player profiles following API_DESIGN.md
"""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, UUID4, field_validator
from src.models.enums import (
    SportType, ProfileVisibility, PlayingRole, 
    BattingStyle, BowlingStyle
)


# ============================================================================
# SPORT PROFILE SCHEMAS
# ============================================================================

class SportProfileCreate(BaseModel):
    """
    Request schema for creating a sport profile
    
    A user can have one profile per sport (e.g., one for cricket, one for football)
    """
    sport_type: SportType = Field(
        ..., 
        description="Type of sport for this profile",
        examples=["CRICKET"]
    )
    visibility: ProfileVisibility = Field(
        default=ProfileVisibility.PUBLIC,
        description="Who can view this profile",
        examples=["PUBLIC"]
    )
    
    @field_validator('sport_type')
    @classmethod
    def validate_sport_type(cls, v):
        """Ensure sport_type is a valid SportType enum"""
        if not isinstance(v, SportType):
            # Allow string conversion
            if isinstance(v, str):
                try:
                    return SportType(v.upper())
                except ValueError:
                    raise ValueError(
                        f"Invalid sport_type. Must be one of: {[s.value for s in SportType]}"
                    )
        return v
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "sport_type": "CRICKET",
                "visibility": "PUBLIC"
            }
        }


class SportProfileResponse(BaseModel):
    """
    Response schema for sport profile
    """
    id: UUID4 = Field(..., description="Unique identifier for the sport profile")
    user_id: UUID4 = Field(..., description="User who owns this profile")
    sport_type: SportType = Field(..., description="Type of sport")
    is_verified: bool = Field(
        default=False, 
        description="Whether this profile is verified (for professional players)"
    )
    verification_proof: Optional[str] = Field(
        None, 
        description="Proof of identity verification"
    )
    verified_at: Optional[datetime] = Field(
        None, 
        description="When the profile was verified"
    )
    visibility: ProfileVisibility = Field(..., description="Profile visibility setting")
    created_at: datetime = Field(..., description="Profile creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "123e4567-e89b-12d3-a456-426614174001",
                "sport_type": "CRICKET",
                "is_verified": False,
                "verification_proof": None,
                "verified_at": None,
                "visibility": "PUBLIC",
                "created_at": "2025-10-30T10:30:00Z",
                "updated_at": "2025-10-30T10:30:00Z"
            }
        }


# ============================================================================
# CRICKET PLAYER PROFILE SCHEMAS
# ============================================================================

class CricketPlayerProfileCreate(BaseModel):
    """
    Request schema for creating a cricket player profile
    
    This extends a sport profile with cricket-specific data
    """
    sport_profile_id: UUID4 = Field(
        ..., 
        description="ID of the sport profile (must be CRICKET type)"
    )
    playing_role: PlayingRole = Field(
        ...,
        description="Primary playing role",
        examples=["BATSMAN"]
    )
    batting_style: Optional[BattingStyle] = Field(
        None,
        description="Batting hand preference",
        examples=["RIGHT_HAND"]
    )
    bowling_style: Optional[BowlingStyle] = Field(
        None,
        description="Bowling style (optional for batsmen)",
        examples=["RIGHT_ARM_MEDIUM"]
    )
    jersey_number: Optional[int] = Field(
        None,
        description="Preferred jersey number",
        ge=1,
        le=99,
        examples=[7]
    )
    
    @field_validator('playing_role')
    @classmethod
    def validate_playing_role(cls, v):
        """Ensure playing_role is valid"""
        if not isinstance(v, PlayingRole):
            if isinstance(v, str):
                try:
                    return PlayingRole(v.lower())
                except ValueError:
                    raise ValueError(
                        f"Invalid playing_role. Must be one of: {[r.value for r in PlayingRole]}"
                    )
        return v
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "sport_profile_id": "123e4567-e89b-12d3-a456-426614174000",
                "playing_role": "ALL_ROUNDER",
                "batting_style": "RIGHT_HAND",
                "bowling_style": "RIGHT_ARM_MEDIUM",
                "jersey_number": 7
            }
        }


class CricketPlayerProfileUpdate(BaseModel):
    """
    Request schema for updating cricket player profile
    
    All fields are optional - only provided fields will be updated
    """
    playing_role: Optional[PlayingRole] = Field(None, description="Update playing role")
    batting_style: Optional[BattingStyle] = Field(None, description="Update batting style")
    bowling_style: Optional[BowlingStyle] = Field(None, description="Update bowling style")
    jersey_number: Optional[int] = Field(None, description="Update jersey number", ge=1, le=99)
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "playing_role": "ALL_ROUNDER",
                "jersey_number": 18
            }
        }


class CareerStats(BaseModel):
    """
    Cricket career statistics (read-only, computed from matches)
    """
    # General
    matches_played: int = Field(default=0, description="Total matches played")
    
    # Batting
    total_runs: int = Field(default=0, description="Total runs scored")
    batting_avg: Optional[float] = Field(None, description="Batting average")
    strike_rate: Optional[float] = Field(None, description="Strike rate")
    highest_score: int = Field(default=0, description="Highest score in an innings")
    fifties: int = Field(default=0, description="Number of 50+ scores")
    hundreds: int = Field(default=0, description="Number of 100+ scores")
    balls_faced: int = Field(default=0, description="Total balls faced")
    fours: int = Field(default=0, description="Total fours hit")
    sixes: int = Field(default=0, description="Total sixes hit")
    
    # Bowling
    total_wickets: int = Field(default=0, description="Total wickets taken")
    bowling_avg: Optional[float] = Field(None, description="Bowling average")
    economy_rate: Optional[float] = Field(None, description="Economy rate")
    best_bowling: Optional[str] = Field(None, description="Best bowling figures (e.g., '5/23')")
    five_wickets: int = Field(default=0, description="5-wicket hauls")
    ten_wickets: int = Field(default=0, description="10-wicket matches")
    balls_bowled: int = Field(default=0, description="Total balls bowled")
    runs_conceded: int = Field(default=0, description="Total runs conceded")
    maidens: int = Field(default=0, description="Maiden overs bowled")
    
    # Fielding
    catches: int = Field(default=0, description="Catches taken")
    stumpings: int = Field(default=0, description="Stumpings (wicket-keepers)")
    run_outs: int = Field(default=0, description="Run-outs effected")
    
    class Config:
        from_attributes = True


class CricketPlayerProfileResponse(BaseModel):
    """
    Response schema for cricket player profile (basic)
    """
    id: UUID4 = Field(..., description="Cricket profile unique identifier")
    sport_profile_id: UUID4 = Field(..., description="Parent sport profile ID")
    playing_role: PlayingRole = Field(..., description="Primary playing role")
    batting_style: Optional[BattingStyle] = Field(None, description="Batting style")
    bowling_style: Optional[BowlingStyle] = Field(None, description="Bowling style")
    jersey_number: Optional[int] = Field(None, description="Jersey number")
    created_at: datetime = Field(..., description="Profile creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174002",
                "sport_profile_id": "123e4567-e89b-12d3-a456-426614174000",
                "playing_role": "ALL_ROUNDER",
                "batting_style": "RIGHT_HAND",
                "bowling_style": "RIGHT_ARM_MEDIUM",
                "jersey_number": 7,
                "created_at": "2025-10-30T10:30:00Z",
                "updated_at": "2025-10-30T10:30:00Z"
            }
        }


class UserBasicInfo(BaseModel):
    """
    Basic user information for nested responses
    """
    id: UUID4 = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    full_name: Optional[str] = Field(None, description="User's full name")
    avatar_url: Optional[str] = Field(None, description="Profile picture URL")
    
    class Config:
        from_attributes = True


class CricketPlayerProfileDetailResponse(BaseModel):
    """
    Response schema for cricket player profile with full details
    
    Includes user information and career statistics
    """
    id: UUID4 = Field(..., description="Cricket profile unique identifier")
    sport_profile_id: UUID4 = Field(..., description="Parent sport profile ID")
    user: Optional[UserBasicInfo] = Field(None, description="User information")
    playing_role: PlayingRole = Field(..., description="Primary playing role")
    batting_style: Optional[BattingStyle] = Field(None, description="Batting style")
    bowling_style: Optional[BowlingStyle] = Field(None, description="Bowling style")
    jersey_number: Optional[int] = Field(None, description="Jersey number")
    career_stats: CareerStats = Field(..., description="Career statistics")
    stats_last_updated: Optional[datetime] = Field(
        None, 
        description="When stats were last recalculated"
    )
    created_at: datetime = Field(..., description="Profile creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174002",
                "sport_profile_id": "123e4567-e89b-12d3-a456-426614174000",
                "user": {
                    "id": "123e4567-e89b-12d3-a456-426614174001",
                    "email": "virat@kreeda.app",
                    "full_name": "Virat Kohli",
                    "avatar_url": "https://example.com/avatar.jpg"
                },
                "playing_role": "BATSMAN",
                "batting_style": "RIGHT_HAND",
                "bowling_style": None,
                "jersey_number": 18,
                "career_stats": {
                    "matches_played": 150,
                    "total_runs": 5420,
                    "batting_avg": 52.15,
                    "strike_rate": 138.5,
                    "highest_score": 183,
                    "fifties": 28,
                    "hundreds": 12,
                    "balls_faced": 3912,
                    "fours": 580,
                    "sixes": 142,
                    "total_wickets": 5,
                    "bowling_avg": 45.2,
                    "economy_rate": 8.1,
                    "best_bowling": "2/15",
                    "five_wickets": 0,
                    "ten_wickets": 0,
                    "balls_bowled": 168,
                    "runs_conceded": 226,
                    "maidens": 0,
                    "catches": 89,
                    "stumpings": 0,
                    "run_outs": 12
                },
                "stats_last_updated": "2025-10-30T10:30:00Z",
                "created_at": "2025-10-30T10:30:00Z",
                "updated_at": "2025-10-30T10:30:00Z"
            }
        }
