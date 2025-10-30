"""
Cricket Match API Router
Endpoints for managing matches, toss, and playing XI

Authentication:
- All endpoints require Bearer token authentication
- User ID extracted from JWT token for authorization

Endpoints:
1. POST /matches - Create match
2. GET /matches - List matches (with filtering)
3. GET /matches/{match_id} - Get match details
4. POST /matches/{match_id}/toss - Conduct toss
5. POST /matches/{match_id}/playing-xi - Set playing XI
6. GET /matches/{match_id}/playing-xi - Get playing XI
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.connection import get_db
from src.core.security import decode_access_token
from src.core.exceptions import KreedaException
from src.models.enums import SportType, MatchType, MatchStatus, MatchVisibility
from src.schemas.cricket.match import (
    MatchCreateRequest, MatchUpdateRequest,
    TossRequest, PlayingXIRequest,
    MatchResponse, MatchDetailResponse, MatchListResponse,
    PlayingXIResponse
)
from src.services.cricket.match import MatchService

router = APIRouter(prefix="/matches", tags=["cricket-matches"])


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
# MATCH ENDPOINTS
# ========================================================================

@router.post(
    "",
    response_model=MatchResponse,
    status_code=201,
    summary="Create match",
    description="Create a new match between two teams. match_code is auto-generated. Default rules applied for standard formats (T20, ODI)."
)
async def create_match(
    request: MatchCreateRequest,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Create a new match
    
    Business rules:
    - Both teams must exist and be active
    - Teams must be different
    - match_code auto-generated (KRD-XXXX)
    - Default match_rules for T20/ODI if not provided
    
    Returns:
        MatchResponse: Created match with match_code
    """
    try:
        return await MatchService.create_match(user_id, request, db)
    except KreedaException as e:
        raise HTTPException(status_code=e.http_status, detail=e.to_dict())
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"code": "INTERNAL_ERROR", "message": str(e)}
        )


@router.get(
    "",
    response_model=MatchListResponse,
    summary="List matches",
    description="Get paginated list of matches with optional filtering by sport, match type, status, team, and visibility."
)
async def list_matches(
    sport_type: Optional[SportType] = Query(None, description="Filter by sport type"),
    match_type: Optional[MatchType] = Query(None, description="Filter by match format (T20, ODI, etc.)"),
    match_status: Optional[MatchStatus] = Query(None, description="Filter by match status"),
    team_id: Optional[UUID] = Query(None, description="Filter by team participation (team_a or team_b)"),
    visibility: Optional[MatchVisibility] = Query(None, description="Filter by visibility"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db)
):
    """
    List matches with pagination and filtering
    
    Query parameters:
    - sport_type: Filter by sport
    - match_type: Filter by format (T20, ODI, etc.)
    - match_status: Filter by status (scheduled, live, completed)
    - team_id: Filter matches where team is participant
    - visibility: Filter by visibility (public, private, etc.)
    - page: Page number
    - page_size: Items per page (max 100)
    
    Returns:
        MatchListResponse: Paginated match list
    """
    try:
        return await MatchService.list_matches(
            db=db,
            sport_type=sport_type,
            match_type=match_type,
            match_status=match_status,
            team_id=team_id,
            visibility=visibility,
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
    "/{match_id}",
    response_model=MatchDetailResponse,
    summary="Get match details",
    description="Get comprehensive match information including officials, playing XI, toss details, and match status."
)
async def get_match(
    match_id: UUID = Path(..., description="Match ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get match by ID with full details
    
    Returns:
        MatchDetailResponse: Match details with officials and playing XI
    """
    try:
        return await MatchService.get_match(match_id, db, include_details=True)
    except KreedaException as e:
        raise HTTPException(status_code=e.http_status, detail=e.to_dict())
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"code": "INTERNAL_ERROR", "message": str(e)}
        )


# ========================================================================
# TOSS ENDPOINT
# ========================================================================

@router.post(
    "/{match_id}/toss",
    response_model=MatchResponse,
    summary="Conduct toss",
    description="Conduct match toss. Only match creator can conduct toss. Updates match status to TOSS_PENDING or LIVE."
)
async def conduct_toss(
    request: TossRequest,
    match_id: UUID = Path(..., description="Match ID"),
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Conduct match toss
    
    Authorization:
    - Only match creator
    
    Business rules:
    - Match must be in SCHEDULED status
    - toss_won_by_team_id must be team_a or team_b
    - Status updated to LIVE if playing XI set, else TOSS_PENDING
    
    Returns:
        MatchResponse: Updated match with toss details
    """
    try:
        return await MatchService.conduct_toss(match_id, user_id, request, db)
    except KreedaException as e:
        raise HTTPException(status_code=e.http_status, detail=e.to_dict())
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"code": "INTERNAL_ERROR", "message": str(e)}
        )


# ========================================================================
# PLAYING XI ENDPOINTS
# ========================================================================

@router.post(
    "/{match_id}/playing-xi",
    response_model=List[PlayingXIResponse],
    status_code=201,
    summary="Set playing XI",
    description="Set playing XI for a team. Only team admins or match creator can set XI. Validates roster and player count."
)
async def set_playing_xi(
    request: PlayingXIRequest,
    match_id: UUID = Path(..., description="Match ID"),
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Set playing XI for a team
    
    Authorization:
    - Team admins or match creator
    
    Business rules:
    - Match must be SCHEDULED or TOSS_PENDING
    - All players must be active team members
    - Player count must match match_rules.players_per_team
    - Exactly one captain required
    - Replaces existing XI if already set
    
    Returns:
        List[PlayingXIResponse]: Playing XI records
    """
    try:
        return await MatchService.set_playing_xi(match_id, user_id, request, db)
    except KreedaException as e:
        raise HTTPException(status_code=e.http_status, detail=e.to_dict())
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"code": "INTERNAL_ERROR", "message": str(e)}
        )
