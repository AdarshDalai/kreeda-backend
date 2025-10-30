"""
Pydantic schemas for Cricket Teams and Team Memberships

This module provides request/response schemas for:
- Team creation and management
- Team membership operations
- JSONB field validation (team_colors, home_ground, roles)

Following the pattern from copilot-instructions.md:
- Validate JSONB schemas in Pydantic before DB insertion
- Use enums from src.models.enums
- Comprehensive docstrings and examples
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, ConfigDict

from src.models.enums import (
    SportType,
    TeamType,
    TeamMemberRole,
    MembershipStatus,
)


# ============================================================================
# JSONB NESTED MODELS
# ============================================================================

class TeamColorsSchema(BaseModel):
    """
    Team color scheme (stored as JSONB in teams.team_colors)
    
    Examples:
        {"primary": "#FF0000", "secondary": "#FFFFFF"}
        {"primary": "#1E40AF", "secondary": "#FACC15", "accent": "#10B981"}
    """
    primary: str = Field(
        ...,
        description="Primary team color (hex code)",
        pattern=r"^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$",
        examples=["#FF0000", "#1E40AF"]
    )
    secondary: Optional[str] = Field(
        None,
        description="Secondary team color (hex code)",
        pattern=r"^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$",
        examples=["#FFFFFF", "#FACC15"]
    )
    accent: Optional[str] = Field(
        None,
        description="Accent color for highlights (hex code)",
        pattern=r"^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$",
        examples=["#10B981", "#F59E0B"]
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "primary": "#1E40AF",
                "secondary": "#FFFFFF",
                "accent": "#FACC15"
            }
        }
    )


class HomeGroundSchema(BaseModel):
    """
    Home ground details (stored as JSONB in teams.home_ground)
    
    Used for: Team profile, match venue suggestions
    """
    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Ground name",
        examples=["Eden Gardens", "Lords Cricket Ground"]
    )
    city: Optional[str] = Field(
        None,
        max_length=100,
        description="City name",
        examples=["Kolkata", "London"]
    )
    state: Optional[str] = Field(
        None,
        max_length=100,
        description="State/Province",
        examples=["West Bengal", "England"]
    )
    country: Optional[str] = Field(
        None,
        max_length=100,
        description="Country name",
        examples=["India", "United Kingdom"]
    )
    latitude: Optional[float] = Field(
        None,
        ge=-90.0,
        le=90.0,
        description="Latitude coordinate",
        examples=[22.5626, 51.5294]
    )
    longitude: Optional[float] = Field(
        None,
        ge=-180.0,
        le=180.0,
        description="Longitude coordinate",
        examples=[88.3432, -0.1726]
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Eden Gardens",
                "city": "Kolkata",
                "state": "West Bengal",
                "country": "India",
                "latitude": 22.5626,
                "longitude": 88.3432
            }
        }
    )


# ============================================================================
# TEAM REQUEST SCHEMAS
# ============================================================================

class TeamCreateRequest(BaseModel):
    """
    Request schema for creating a new team
    
    Required: name, sport_type
    Optional: short_name, team_type, logo_url, colors, home_ground
    
    Workflow:
        1. User creates team (becomes creator and admin)
        2. Creator can add members
        3. Members can be assigned roles (player, captain, coach)
    """
    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Full team name",
        examples=["Mumbai Indians", "Royal Challengers Bangalore"]
    )
    short_name: Optional[str] = Field(
        None,
        max_length=20,
        description="Team abbreviation (auto-generated if not provided)",
        examples=["MI", "RCB"]
    )
    sport_type: SportType = Field(
        default=SportType.CRICKET,
        description="Sport for this team (currently only cricket supported)"
    )
    team_type: TeamType = Field(
        default=TeamType.CASUAL,
        description="Team organization level"
    )
    logo_url: Optional[str] = Field(
        None,
        max_length=500,
        description="Team logo image URL",
        examples=["https://example.com/logos/team-logo.png"]
    )
    team_colors: Optional[TeamColorsSchema] = Field(
        None,
        description="Team color scheme (primary/secondary/accent)"
    )
    home_ground: Optional[HomeGroundSchema] = Field(
        None,
        description="Team's home ground details"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Mumbai Indians",
                "short_name": "MI",
                "sport_type": "cricket",
                "team_type": "franchise",
                "team_colors": {
                    "primary": "#004BA0",
                    "secondary": "#FFD700",
                    "accent": "#FFFFFF"
                },
                "home_ground": {
                    "name": "Wankhede Stadium",
                    "city": "Mumbai",
                    "state": "Maharashtra",
                    "country": "India"
                }
            }
        }
    )


class TeamUpdateRequest(BaseModel):
    """
    Request schema for updating team details
    
    All fields optional - only provided fields will be updated
    Restricted to team creator or team_admins
    """
    name: Optional[str] = Field(
        None,
        min_length=2,
        max_length=100,
        description="Updated team name"
    )
    short_name: Optional[str] = Field(
        None,
        max_length=20,
        description="Updated team abbreviation"
    )
    team_type: Optional[TeamType] = Field(
        None,
        description="Updated team organization level"
    )
    logo_url: Optional[str] = Field(
        None,
        max_length=500,
        description="Updated logo URL"
    )
    team_colors: Optional[TeamColorsSchema] = Field(
        None,
        description="Updated color scheme"
    )
    home_ground: Optional[HomeGroundSchema] = Field(
        None,
        description="Updated home ground"
    )
    is_active: Optional[bool] = Field(
        None,
        description="Team active status (deactivate to hide from searches)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "logo_url": "https://example.com/new-logo.png",
                "team_colors": {
                    "primary": "#FF0000",
                    "secondary": "#000000"
                }
            }
        }
    )


# ============================================================================
# TEAM MEMBERSHIP REQUEST SCHEMAS
# ============================================================================

class TeamMembershipCreateRequest(BaseModel):
    """
    Request schema for adding a member to a team
    
    Required: user_id or cricket_profile_id
    Optional: roles, jersey_number
    
    Workflow:
        1. Team admin sends invite to user
        2. System creates membership with status=ACTIVE
        3. User can accept (keeps ACTIVE) or reject (status=LEFT)
    """
    user_id: UUID = Field(
        ...,
        description="User ID to add as team member"
    )
    cricket_profile_id: Optional[UUID] = Field(
        None,
        description="Specific cricket profile to use (if user has multiple sport profiles)"
    )
    roles: List[TeamMemberRole] = Field(
        default=[TeamMemberRole.PLAYER],
        description="Member roles in team (can have multiple)"
    )
    jersey_number: Optional[int] = Field(
        None,
        ge=0,
        le=999,
        description="Player's jersey number"
    )

    @field_validator('roles')
    @classmethod
    def validate_roles(cls, v: List[TeamMemberRole]) -> List[TeamMemberRole]:
        """Ensure at least one role and no duplicates"""
        if not v:
            raise ValueError("At least one role must be assigned")
        if len(v) != len(set(v)):
            raise ValueError("Duplicate roles not allowed")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "roles": ["player", "captain"],
                "jersey_number": 18
            }
        }
    )


class TeamMembershipUpdateRequest(BaseModel):
    """
    Request schema for updating team membership
    
    Used for: Changing roles, jersey number, status (bench/injure)
    Restricted to: Team admins
    """
    roles: Optional[List[TeamMemberRole]] = Field(
        None,
        description="Updated member roles"
    )
    jersey_number: Optional[int] = Field(
        None,
        ge=0,
        le=999,
        description="Updated jersey number"
    )
    status: Optional[MembershipStatus] = Field(
        None,
        description="Updated membership status"
    )

    @field_validator('roles')
    @classmethod
    def validate_roles(cls, v: Optional[List[TeamMemberRole]]) -> Optional[List[TeamMemberRole]]:
        """Ensure no duplicates if roles provided"""
        if v is not None:
            if not v:
                raise ValueError("At least one role must be assigned")
            if len(v) != len(set(v)):
                raise ValueError("Duplicate roles not allowed")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "roles": ["player", "vice_captain"],
                "jersey_number": 7
            }
        }
    )


# ============================================================================
# TEAM RESPONSE SCHEMAS
# ============================================================================

class TeamMembershipResponse(BaseModel):
    """
    Response schema for team membership
    
    Includes: Member details, roles, status, timestamps
    Used in: Team roster, member list endpoints
    """
    id: UUID = Field(..., description="Membership ID")
    team_id: UUID = Field(..., description="Team ID")
    user_id: UUID = Field(..., description="User ID")
    sport_profile_id: UUID = Field(..., description="Sport profile ID")
    cricket_profile_id: Optional[UUID] = Field(None, description="Cricket profile ID")
    roles: List[TeamMemberRole] = Field(..., description="Member roles")
    jersey_number: Optional[int] = Field(None, description="Jersey number")
    status: MembershipStatus = Field(..., description="Membership status")
    joined_at: datetime = Field(..., description="When member joined team")
    
    # Optional nested user/profile data (populated by service layer)
    user_name: Optional[str] = Field(None, description="User display name")
    cricket_profile_name: Optional[str] = Field(None, description="Cricket profile name")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174001",
                "team_id": "123e4567-e89b-12d3-a456-426614174002",
                "user_id": "123e4567-e89b-12d3-a456-426614174003",
                "sport_profile_id": "123e4567-e89b-12d3-a456-426614174004",
                "cricket_profile_id": "123e4567-e89b-12d3-a456-426614174005",
                "roles": ["player", "captain"],
                "jersey_number": 18,
                "status": "active",
                "joined_at": "2024-01-15T10:30:00Z",
                "user_name": "Virat Kohli",
                "cricket_profile_name": "Virat Kohli"
            }
        }
    )


class TeamResponse(BaseModel):
    """
    Response schema for team details
    
    Includes: Team info, creator, member count, timestamps
    Used in: Team detail, list endpoints
    """
    id: UUID = Field(..., description="Team ID")
    name: str = Field(..., description="Team name")
    short_name: str = Field(..., description="Team abbreviation")
    sport_type: SportType = Field(..., description="Sport type")
    team_type: TeamType = Field(..., description="Team organization level")
    created_by: UUID = Field(..., description="Creator user ID")
    logo_url: Optional[str] = Field(None, description="Logo URL")
    team_colors: Optional[TeamColorsSchema] = Field(None, description="Color scheme")
    home_ground: Optional[HomeGroundSchema] = Field(None, description="Home ground")
    is_active: bool = Field(..., description="Team active status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    # Computed fields (populated by service layer)
    member_count: Optional[int] = Field(None, description="Total active members")
    creator_name: Optional[str] = Field(None, description="Creator display name")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Mumbai Indians",
                "short_name": "MI",
                "sport_type": "cricket",
                "team_type": "franchise",
                "created_by": "123e4567-e89b-12d3-a456-426614174001",
                "logo_url": "https://example.com/mi-logo.png",
                "team_colors": {
                    "primary": "#004BA0",
                    "secondary": "#FFD700"
                },
                "home_ground": {
                    "name": "Wankhede Stadium",
                    "city": "Mumbai",
                    "country": "India"
                },
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
                "member_count": 15,
                "creator_name": "Rohit Sharma"
            }
        }
    )


class TeamDetailResponse(TeamResponse):
    """
    Extended team response with full member roster
    
    Includes: All team info + list of members
    Used in: GET /teams/{team_id} endpoint
    """
    members: List[TeamMembershipResponse] = Field(
        default=[],
        description="Team roster (all memberships)"
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Mumbai Indians",
                "short_name": "MI",
                "sport_type": "cricket",
                "team_type": "franchise",
                "created_by": "123e4567-e89b-12d3-a456-426614174001",
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
                "member_count": 2,
                "members": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174002",
                        "team_id": "123e4567-e89b-12d3-a456-426614174000",
                        "user_id": "123e4567-e89b-12d3-a456-426614174003",
                        "roles": ["player", "captain"],
                        "jersey_number": 45,
                        "status": "active",
                        "joined_at": "2024-01-01T00:00:00Z"
                    }
                ]
            }
        }
    )


# ============================================================================
# LIST RESPONSE SCHEMAS
# ============================================================================

class TeamListResponse(BaseModel):
    """
    Paginated response for team list
    
    Used in: GET /teams endpoint (search/filter)
    """
    teams: List[TeamResponse] = Field(..., description="List of teams")
    total: int = Field(..., description="Total teams matching criteria")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "teams": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "name": "Mumbai Indians",
                        "short_name": "MI",
                        "sport_type": "cricket",
                        "team_type": "franchise",
                        "created_by": "123e4567-e89b-12d3-a456-426614174001",
                        "is_active": True,
                        "created_at": "2024-01-01T00:00:00Z",
                        "updated_at": "2024-01-01T00:00:00Z",
                        "member_count": 15
                    }
                ],
                "total": 50,
                "page": 1,
                "page_size": 10
            }
        }
    )
