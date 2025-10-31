"""
Live Scoring REST Router

API endpoints for ball-by-ball cricket scoring:
- Create innings
- Record balls
- Manage current players (batsmen, bowler)
- Get live innings state
- Create overs

Pattern: Router → Service → Database
Router handles HTTP, Service handles business logic
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.connection import get_db
from src.services.cricket.innings_service import InningsService
from src.services.cricket.ball_service import BallService
from src.schemas.cricket.innings import (
    InningsCreateRequest,
    InningsResponse,
    InningsWithStateResponse,
    InningsUpdateRequest,
    SetBatsmenRequest,
    SetBowlerRequest
)
from src.schemas.cricket.ball import (
    BallCreateRequest,
    BallResponse
)
from src.core.exceptions import NotFoundError, ValidationError


router = APIRouter(
    prefix="/cricket/live-scoring",
    tags=["Cricket Live Scoring"]
)


# ============================================================================
# INNINGS ENDPOINTS
# ============================================================================

@router.post(
    "/matches/{match_id}/innings",
    response_model=InningsResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start New Innings",
    description="""
    Start a new innings for a match.
    
    Workflow:
    1. Validate match is LIVE or TOSS_PENDING
    2. Validate teams are in match
    3. Create innings with initial state (0/0 in 0.0 overs)
    4. Set opening batsmen via PUT /innings/{id}/batsmen
    5. Set first bowler via PUT /innings/{id}/bowler
    6. Create first over via POST /overs
    7. Start recording balls
    
    Required for second innings: target_runs (first innings total + 1)
    """
)
async def create_innings(
    match_id: UUID,
    request: InningsCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create new innings for match"""
    try:
        return await InningsService.create_innings(match_id, request, db)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/innings/{innings_id}",
    response_model=InningsResponse,
    summary="Get Innings Details",
    description="Retrieve innings details without live state calculation"
)
async def get_innings(
    innings_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get innings details"""
    try:
        return await InningsService.get_innings(innings_id, db)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get(
    "/innings/{innings_id}/state",
    response_model=InningsWithStateResponse,
    summary="Get Live Innings State",
    description="""
    Get innings with real-time state calculation.
    
    Derived from ball events:
    - Current score (145/4)
    - Overs bowled (15.3)
    - Run rate (9.35)
    - Batsmen stats (runs, balls, strike rate)
    - Bowler stats (overs, runs, wickets, economy)
    - Chase situation (required rate, runs needed)
    
    Use for:
    - Live scorecard display
    - Real-time match updates
    - Spectator experience
    """
)
async def get_innings_state(
    innings_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get innings with live state"""
    try:
        return await InningsService.get_current_state(innings_id, db)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.put(
    "/innings/{innings_id}/batsmen",
    response_model=InningsResponse,
    summary="Set Current Batsmen",
    description="""
    Set current batsmen (striker and non-striker).
    
    Used when:
    - Starting innings (set opening pair)
    - After wicket (set new batsman)
    - Player rotation
    
    Striker: Batsman facing current delivery
    Non-striker: Batsman at other end
    """
)
async def set_batsmen(
    innings_id: UUID,
    request: SetBatsmenRequest,
    db: AsyncSession = Depends(get_db)
):
    """Set current batsmen"""
    try:
        return await InningsService.set_batsmen(innings_id, request, db)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put(
    "/innings/{innings_id}/bowler",
    response_model=InningsResponse,
    summary="Set Current Bowler",
    description="""
    Set current bowler for the over.
    
    Used when:
    - Starting new over
    - Changing bowler mid-match
    
    Bowler must be from bowling team.
    Create new over after setting bowler.
    """
)
async def set_bowler(
    innings_id: UUID,
    request: SetBowlerRequest,
    db: AsyncSession = Depends(get_db)
):
    """Set current bowler"""
    try:
        return await InningsService.set_bowler(innings_id, request, db)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put(
    "/innings/{innings_id}",
    response_model=InningsResponse,
    summary="Update Innings",
    description="""
    Update innings details.
    
    Used for:
    - Ending innings (is_completed=True)
    - Marking all-out (wickets_fallen=10 auto-sets this)
    - Recording declaration (declared=True)
    
    Note: All-out is auto-detected when 10th wicket falls.
    """
)
async def update_innings(
    innings_id: UUID,
    request: InningsUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Update innings"""
    try:
        return await InningsService.update_innings(innings_id, request, db)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# ============================================================================
# OVER ENDPOINTS
# ============================================================================

@router.post(
    "/innings/{innings_id}/overs",
    status_code=status.HTTP_201_CREATED,
    summary="Create New Over",
    description="""
    Create a new over for the innings.
    
    Workflow:
    1. Set bowler via PUT /innings/{id}/bowler
    2. Create over (this endpoint)
    3. Record balls via POST /balls
    
    Over auto-completes after 6 legal deliveries.
    Maiden over auto-detected (0 runs in completed over).
    """
)
async def create_over(
    innings_id: UUID,
    over_number: int,
    bowler_user_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Create new over"""
    try:
        over = await BallService.create_over(
            innings_id,
            over_number,
            bowler_user_id,
            db
        )
        return {
            "id": over.id,
            "innings_id": over.innings_id,
            "over_number": over.over_number,
            "bowler_user_id": over.bowler_user_id,
            "message": f"Over {over_number} created"
        }
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============================================================================
# BALL ENDPOINTS (PRIMARY SCORING)
# ============================================================================

@router.post(
    "/balls",
    response_model=BallResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record Ball Bowled (PRIMARY SCORING ENDPOINT)",
    description="""
    Record a ball bowled - the atomic unit of cricket scoring.
    
    Event Sourcing Pattern:
    - Creates immutable Ball record
    - Updates innings aggregates (runs, wickets, overs)
    - Updates over aggregates (runs, wickets, ball sequence)
    - Auto-completes over after 6 legal deliveries
    - Auto-completes innings if all-out (10 wickets)
    - Creates Wicket record if is_wicket=True
    
    Workflow:
    1. Validate innings and over exist
    2. Create Ball record (immutable event)
    3. Create Wicket record (if applicable)
    4. Update innings state
    5. Update over state
    6. Return enriched response
    
    Ball Types:
    - Legal delivery: is_legal_delivery=True (counts toward over)
    - Wide: extra_type=WIDE, is_legal_delivery=False
    - No-ball: extra_type=NO_BALL, is_legal_delivery=False
    - Bye/Leg-bye: extra_type=BYE/LEG_BYE, runs_scored=0
    
    Wicket: Set is_wicket=True and provide wicket_details
    Boundary: Set is_boundary=True and boundary_type (FOUR/SIX)
    
    This endpoint broadcasts to WebSocket for real-time updates.
    """
)
async def record_ball(
    request: BallCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Record ball bowled"""
    try:
        return await BallService.record_ball(request, db)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/balls/{ball_id}",
    response_model=BallResponse,
    summary="Get Ball Details",
    description="Retrieve ball details with wicket info if applicable"
)
async def get_ball(
    ball_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get ball details"""
    try:
        return await BallService.get_ball(ball_id, db)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get(
    "/innings/{innings_id}/balls",
    response_model=List[BallResponse],
    summary="Get All Balls for Innings",
    description="""
    Get all balls for an innings in chronological order.
    
    Used for:
    - Ball-by-ball replay
    - Match archives
    - Statistics calculation
    - Highlight generation
    
    Returns balls ordered by ball_number (1.1, 1.2, ..., 20.6)
    """
)
async def get_innings_balls(
    innings_id: UUID,
    limit: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get all balls for innings"""
    try:
        return await BallService.get_innings_balls(innings_id, db, limit)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
