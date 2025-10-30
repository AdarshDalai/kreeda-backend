"""
Cricket Team API Router
Endpoints for managing teams and team memberships

Authentication:
- All endpoints require Bearer token authentication
- User ID extracted from JWT token for authorization

Endpoints:
1. POST /teams - Create team
2. GET /teams - List teams (with filtering)
3. GET /teams/{team_id} - Get team details
4. PUT /teams/{team_id} - Update team
5. POST /teams/{team_id}/members - Add team member
6. PUT /teams/{team_id}/members/{membership_id} - Update membership
7. DELETE /teams/{team_id}/members/{membership_id} - Remove member
8. GET /teams/{team_id}/members - Get team roster
"""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.connection import get_db
from src.core.security import decode_access_token
from src.core.exceptions import KreedaException
from src.models.enums import SportType, TeamType
from src.schemas.cricket.team import (
    TeamCreateRequest, TeamUpdateRequest,
    TeamMembershipCreateRequest, TeamMembershipUpdateRequest,
    TeamResponse, TeamDetailResponse, TeamListResponse,
    TeamMembershipResponse
)
from src.services.cricket.team import TeamService

router = APIRouter(prefix="/teams", tags=["cricket-teams"])


async def get_current_user_id(authorization: str = Header(...)) -> UUID:
    """
    Extract and validate user ID from JWT token
    
    Args:
        authorization: Bearer token from Authorization header
    
    Returns:
        UUID: User ID from token
    
    Raises:
        HTTPException(401): If token is invalid or missing
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid authorization header"
        )
    
    token = authorization.split(" ")[1]
    payload = decode_access_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid token payload"
        )
    
    try:
        return UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=401,
            detail="Invalid user ID in token"
        )


# ========================================================================
# TEAM ENDPOINTS
# ========================================================================

@router.post(
    "",
    response_model=TeamResponse,
    status_code=201,
    summary="Create team",
    description="Create a new team. The creator becomes team admin automatically. short_name is auto-generated if not provided."
)
async def create_team(
    request: TeamCreateRequest,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Create a new team
    
    Business rules:
    - Creator automatically becomes team_admin
    - short_name auto-generated from name if not provided
    - Team name must be unique for the sport
    
    Returns:
        TeamResponse: Created team data
    """
    try:
        return await TeamService.create_team(user_id, request, db)
    except KreedaException as e:
        raise HTTPException(status_code=e.http_status, detail=e.to_dict())
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"code": "INTERNAL_ERROR", "message": str(e)}
        )


@router.get(
    "",
    response_model=TeamListResponse,
    summary="List teams",
    description="Get paginated list of teams with optional filtering by sport, team type, search query, and active status."
)
async def list_teams(
    sport_type: Optional[SportType] = Query(None, description="Filter by sport type"),
    team_type: Optional[TeamType] = Query(None, description="Filter by team organization level"),
    search: Optional[str] = Query(None, description="Search in team name or short_name"),
    is_active: bool = Query(True, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db)
):
    """
    List teams with pagination and filtering
    
    Query parameters:
    - sport_type: Filter by sport (cricket, football, etc.)
    - team_type: Filter by organization level (casual, club, etc.)
    - search: Search in name/short_name
    - is_active: Show only active teams
    - page: Page number
    - page_size: Items per page (max 100)
    
    Returns:
        TeamListResponse: Paginated team list
    """
    try:
        return await TeamService.list_teams(
            db=db,
            sport_type=sport_type,
            team_type=team_type,
            search=search,
            is_active=is_active,
            page=page,
            page_size=page_size
        )
    except KreedaException as e:
        raise HTTPException(status_code=e.http_status, detail=e.to_dict())
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"code": "INTERNAL_ERROR", "message": str(e)}
        )


@router.get(
    "/{team_id}",
    response_model=TeamDetailResponse,
    summary="Get team details",
    description="Get comprehensive team information including full member roster with roles and status."
)
async def get_team(
    team_id: UUID = Path(..., description="Team ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get team by ID with full member roster
    
    Returns:
        TeamDetailResponse: Team details with members
    """
    try:
        return await TeamService.get_team(team_id, db, include_members=True)
    except KreedaException as e:
        raise HTTPException(status_code=e.http_status, detail=e.to_dict())
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"code": "INTERNAL_ERROR", "message": str(e)}
        )


@router.put(
    "/{team_id}",
    response_model=TeamResponse,
    summary="Update team",
    description="Update team details. Only team creator or team_admins can update. Cannot change sport_type or creator."
)
async def update_team(
    request: TeamUpdateRequest,
    team_id: UUID = Path(..., description="Team ID"),
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Update team details
    
    Authorization:
    - Only team creator or team_admins
    
    Returns:
        TeamResponse: Updated team data
    """
    try:
        return await TeamService.update_team(team_id, user_id, request, db)
    except KreedaException as e:
        raise HTTPException(status_code=e.http_status, detail=e.to_dict())
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"code": "INTERNAL_ERROR", "message": str(e)}
        )


# ========================================================================
# TEAM MEMBERSHIP ENDPOINTS
# ========================================================================

@router.post(
    "/{team_id}/members",
    response_model=TeamMembershipResponse,
    status_code=201,
    summary="Add team member",
    description="Add a new member to the team. Only team admins can add members. Validates jersey number uniqueness."
)
async def add_team_member(
    request: TeamMembershipCreateRequest,
    team_id: UUID = Path(..., description="Team ID"),
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Add member to team
    
    Authorization:
    - Only team creator or team_admins
    
    Business rules:
    - User must exist and not already be active member
    - Jersey number must be unique within team
    - Cricket profile auto-linked if user has one
    
    Returns:
        TeamMembershipResponse: Created membership
    """
    try:
        return await TeamService.add_member(team_id, user_id, request, db)
    except KreedaException as e:
        raise HTTPException(status_code=e.http_status, detail=e.to_dict())
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"code": "INTERNAL_ERROR", "message": str(e)}
        )


@router.get(
    "/{team_id}/members",
    response_model=TeamDetailResponse,
    summary="Get team roster",
    description="Get complete team roster with all members, roles, and status. Same as GET /teams/{team_id} but explicit endpoint."
)
async def get_team_members(
    team_id: UUID = Path(..., description="Team ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get team roster
    
    Returns:
        TeamDetailResponse: Team with full member list
    """
    try:
        return await TeamService.get_team(team_id, db, include_members=True)
    except KreedaException as e:
        raise HTTPException(status_code=e.http_status, detail=e.to_dict())
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"code": "INTERNAL_ERROR", "message": str(e)}
        )
