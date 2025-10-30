"""
Cricket Profile API Router
Endpoints for managing sport profiles and cricket player profiles

Authentication:
- All endpoints require Bearer token authentication
- User ID extracted from JWT token for authorization

Endpoints:
1. POST /sport-profiles - Create sport profile
2. GET /sport-profiles/{profile_id} - Get sport profile
3. GET /users/{user_id}/sport-profiles - List user's sport profiles
4. POST /cricket-profiles - Create cricket player profile
5. GET /cricket-profiles/{profile_id} - Get cricket profile with details
6. PATCH /cricket-profiles/{profile_id} - Update cricket profile
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.connection import get_db
from src.core.security import decode_access_token
from src.core.exceptions import (
    KreedaException, DuplicateSportProfileError, SportProfileNotFoundError,
    CricketProfileNotFoundError, DuplicateCricketProfileError,
    InvalidSportTypeError, NotFoundError
)
from src.models.enums import SportType
from src.schemas.cricket.profile import (
    SportProfileCreate, SportProfileResponse,
    CricketPlayerProfileCreate, CricketPlayerProfileResponse,
    CricketPlayerProfileUpdate, CricketPlayerProfileDetailResponse
)
from src.services.cricket.profile import CricketProfileService

router = APIRouter(tags=["cricket-profiles"])


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
# SPORT PROFILE ENDPOINTS
# ========================================================================

@router.post(
    "/sport-profiles",
    response_model=SportProfileResponse,
    status_code=201,
    summary="Create sport profile",
    description="Create a new sport profile for the authenticated user. Each user can only have one profile per sport type."
)
async def create_sport_profile(
    request: SportProfileCreate,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Create a new sport profile
    
    - **sport_type**: Type of sport (CRICKET, FOOTBALL, etc.)
    - **visibility**: Profile visibility (PUBLIC, FRIENDS_ONLY, PRIVATE)
    
    Returns the created sport profile with ID
    """
    try:
        return await CricketProfileService.create_sport_profile(user_id, request, db)
    except DuplicateSportProfileError as e:
        raise HTTPException(status_code=e.http_status, detail=e.to_dict())
    except NotFoundError as e:
        raise HTTPException(status_code=e.http_status, detail=e.to_dict())
    except KreedaException as e:
        raise HTTPException(status_code=e.http_status, detail=e.to_dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Internal server error", "error": str(e)})


@router.get(
    "/sport-profiles/{profile_id}",
    response_model=SportProfileResponse,
    summary="Get sport profile",
    description="Retrieve a sport profile by its ID"
)
async def get_sport_profile(
    profile_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Get sport profile by ID
    
    - **profile_id**: UUID of the sport profile
    
    Returns the sport profile details
    """
    try:
        return await CricketProfileService.get_sport_profile(profile_id, db)
    except SportProfileNotFoundError as e:
        raise HTTPException(status_code=e.http_status, detail=e.to_dict())
    except KreedaException as e:
        raise HTTPException(status_code=e.http_status, detail=e.to_dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Internal server error", "error": str(e)})


@router.get(
    "/users/{user_id}/sport-profiles",
    response_model=List[SportProfileResponse],
    summary="List user's sport profiles",
    description="Get all sport profiles for a specific user, optionally filtered by sport type"
)
async def list_user_sport_profiles(
    user_id: UUID,
    sport_type: Optional[SportType] = Query(None, description="Filter by sport type"),
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """
    List all sport profiles for a user
    
    - **user_id**: UUID of the user whose profiles to retrieve
    - **sport_type**: Optional filter by sport type (CRICKET, FOOTBALL, etc.)
    
    Returns list of sport profiles
    """
    try:
        return await CricketProfileService.list_user_sport_profiles(user_id, sport_type, db)
    except KreedaException as e:
        raise HTTPException(status_code=e.http_status, detail=e.to_dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Internal server error", "error": str(e)})


# ========================================================================
# CRICKET PLAYER PROFILE ENDPOINTS
# ========================================================================

@router.post(
    "/cricket-profiles",
    response_model=CricketPlayerProfileResponse,
    status_code=201,
    summary="Create cricket player profile",
    description="Create a cricket player profile linked to a sport profile. The sport profile must be of type CRICKET."
)
async def create_cricket_profile(
    request: CricketPlayerProfileCreate,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Create a new cricket player profile
    
    - **sport_profile_id**: UUID of the sport profile (must be CRICKET type)
    - **playing_role**: Player role (BATSMAN, BOWLER, ALL_ROUNDER, WICKET_KEEPER)
    - **batting_style**: Batting style (RIGHT_HAND_BAT, LEFT_HAND_BAT)
    - **bowling_style**: Bowling style (RIGHT_ARM_FAST, LEFT_ARM_SPIN, etc.)
    - **jersey_number**: Optional jersey number
    
    Returns the created cricket profile with initialized stats
    """
    try:
        return await CricketProfileService.create_cricket_profile(request, db)
    except (SportProfileNotFoundError, InvalidSportTypeError, DuplicateCricketProfileError) as e:
        raise HTTPException(status_code=e.http_status, detail=e.to_dict())
    except KreedaException as e:
        raise HTTPException(status_code=e.http_status, detail=e.to_dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Internal server error", "error": str(e)})


@router.get(
    "/cricket-profiles/{profile_id}",
    response_model=CricketPlayerProfileDetailResponse,
    summary="Get cricket player profile",
    description="Retrieve a cricket player profile with full details including career statistics and optional user information"
)
async def get_cricket_profile(
    profile_id: UUID,
    include_user_info: bool = Query(False, description="Include user information in response"),
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Get cricket player profile with details
    
    - **profile_id**: UUID of the cricket profile
    - **include_user_info**: If true, includes user email, name, and avatar
    
    Returns cricket profile with career statistics and optional user info
    """
    try:
        return await CricketProfileService.get_cricket_profile(profile_id, db, include_user_info)
    except CricketProfileNotFoundError as e:
        raise HTTPException(status_code=e.http_status, detail=e.to_dict())
    except KreedaException as e:
        raise HTTPException(status_code=e.http_status, detail=e.to_dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Internal server error", "error": str(e)})


@router.patch(
    "/cricket-profiles/{profile_id}",
    response_model=CricketPlayerProfileResponse,
    summary="Update cricket player profile",
    description="Update cricket player profile. Only provided fields will be updated (partial update)."
)
async def update_cricket_profile(
    profile_id: UUID,
    request: CricketPlayerProfileUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Update cricket player profile (partial update)
    
    - **profile_id**: UUID of the cricket profile to update
    - **playing_role**: Optional new playing role
    - **batting_style**: Optional new batting style
    - **bowling_style**: Optional new bowling style
    - **jersey_number**: Optional new jersey number
    
    Only provided fields will be updated. Returns the updated profile.
    """
    try:
        return await CricketProfileService.update_cricket_profile(profile_id, request, db)
    except CricketProfileNotFoundError as e:
        raise HTTPException(status_code=e.http_status, detail=e.to_dict())
    except KreedaException as e:
        raise HTTPException(status_code=e.http_status, detail=e.to_dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Internal server error", "error": str(e)})
