from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
import logging
import uuid

from app.utils.database import get_db
from app.models.user import User
from app.models.cricket import CricketMatch, CricketBall
from app.schemas.cricket import (
    CricketMatchCreate,
    BallRecord,
    BallResponse,
    MatchResponseBasic,
    ScorerAssignment,
)
from app.auth.middleware import get_current_active_user
from app.services.cricket_service import CricketService
from app.services.scoring_integrity_service import ScoringIntegrityService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
async def cricket_health():
    return {"success": True, "message": "Cricket service with integrity checks healthy"}


@router.post("/matches", response_model=MatchResponseBasic)
async def create_match(
    match_data: CricketMatchCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new cricket match"""
    try:
        # Create new match
        new_match = CricketMatch(
            team_a_id=match_data.team_a_id,
            team_b_id=match_data.team_b_id,
            overs_per_innings=match_data.overs_per_innings,
            venue=match_data.venue,
            match_date=match_data.match_date,
            created_by_id=current_user.id,
        )

        db.add(new_match)
        await db.commit()
        await db.refresh(new_match)

        logger.info(f"Match created: {new_match.id} by {current_user.username}")
        return new_match

    except Exception as e:
        logger.error(f"Error creating match: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/matches", response_model=List[MatchResponseBasic])
async def get_matches(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get all matches for the user"""
    try:
        query = select(CricketMatch).order_by(CricketMatch.created_at.desc())
        result = await db.execute(query)
        matches = result.scalars().all()

        return matches

    except Exception as e:
        logger.error(f"Error fetching matches: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/matches/{match_id}", response_model=MatchResponseBasic)
async def get_match(
    match_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get match by ID"""
    try:
        query = select(CricketMatch).where(CricketMatch.id == match_id)
        result = await db.execute(query)
        match = result.scalar_one_or_none()

        if not match:
            raise HTTPException(status_code=404, detail="Match not found")

        return match

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching match: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/matches/{match_id}/scorers")
async def assign_match_scorers(
    match_id: str,
    scorer_data: ScorerAssignment,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Assign official scorers for a match"""
    try:
        # Verify match exists and user has permission
        query = select(CricketMatch).where(CricketMatch.id == match_id)
        result = await db.execute(query)
        match = result.scalar_one_or_none()

        if not match:
            raise HTTPException(status_code=404, detail="Match not found")

        if str(match.created_by_id) != str(current_user.id):
            raise HTTPException(
                status_code=403, detail="Only match creator can assign scorers"
            )

        # Assign scorers using integrity service
        integrity_service = ScoringIntegrityService(db)
        result = await integrity_service.assign_match_scorers(
            match_id=match_id,
            team_a_scorer_id=scorer_data.team_a_scorer_id,
            team_b_scorer_id=scorer_data.team_b_scorer_id,
            appointed_by_id=str(current_user.id),
            umpire_id=scorer_data.umpire_id,
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error assigning scorers: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/matches/{match_id}/scoring-status")
async def get_match_scoring_status(
    match_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get scoring status and integrity information for a match"""
    try:
        integrity_service = ScoringIntegrityService(db)
        status = await integrity_service.get_match_scoring_status(match_id)

        return status

    except Exception as e:
        logger.error(f"Error getting scoring status: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/matches/{match_id}/balls")
async def record_ball_with_integrity(
    match_id: str,
    ball_data: BallRecord,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Record a ball with integrity verification"""
    try:
        # Get client info for audit trail
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

        # Use integrity service to record ball
        integrity_service = ScoringIntegrityService(db)
        result = await integrity_service.record_ball_entry(
            match_id=match_id,
            scorer_id=str(current_user.id),
            ball_data=ball_data,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Error recording ball with integrity: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/matches/{match_id}/disputes/{innings}/{over_number}/{ball_number}/resolve"
)
async def resolve_scoring_dispute(
    match_id: str,
    innings: int,
    over_number: int,
    ball_number: int,
    resolution_data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Resolve a scoring dispute (umpire/referee only)"""
    try:
        integrity_service = ScoringIntegrityService(db)

        # Check if user is authorized to resolve disputes
        scoring_status = await integrity_service.get_match_scoring_status(match_id)
        user_roles = [
            s["role"]
            for s in scoring_status["scorers"]
            if s["user_id"] == str(current_user.id)
        ]

        if "umpire" not in user_roles and "referee" not in user_roles:
            raise HTTPException(
                status_code=403, detail="Only umpires/referees can resolve disputes"
            )

        result = await integrity_service.resolve_dispute(
            match_id=match_id,
            innings=innings,
            over_number=over_number,
            ball_number=ball_number,
            resolver_id=str(current_user.id),
            final_entry_id=str(resolution_data.get("final_entry_id", "")),
            resolution_notes=str(resolution_data.get("resolution_notes", "")),
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving dispute: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/matches/{match_id}/scorecard")
async def get_scorecard(
    match_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get match scorecard (only verified balls)"""
    try:
        cricket_service = CricketService(db)
        scorecard = await cricket_service.get_match_scorecard(match_id)

        # Add integrity information
        integrity_service = ScoringIntegrityService(db)
        scoring_status = await integrity_service.get_match_scoring_status(match_id)

        return {
            "scorecard": scorecard,
            "integrity_info": {
                "verified_balls": scoring_status["verified_balls"],
                "pending_verifications": scoring_status["pending_verifications"],
                "disputes_count": len(scoring_status["disputes"]),
                "scorers": scoring_status["scorers"],
            },
        }

    except Exception as e:
        logger.error(f"Error fetching scorecard: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Legacy endpoint for backward compatibility
@router.post("/matches/{match_id}/balls/legacy", response_model=BallResponse)
async def record_ball_legacy(
    match_id: str,
    ball_data: BallRecord,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Legacy ball recording without integrity checks (for testing only)"""
    try:
        cricket_service = CricketService(db)
        ball = await cricket_service.record_ball(match_id, ball_data)

        return ball

    except Exception as e:
        logger.error(f"Error recording ball (legacy): {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/matches/{match_id}/live-updates")
async def get_live_match_updates(
    match_id: str,
    last_update: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get live match updates for spectators"""
    try:
        # Get latest verified balls
        query = select(CricketBall).where(CricketBall.match_id == match_id)

        if last_update:
            query = query.where(CricketBall.created_at > last_update)

        query = query.order_by(CricketBall.created_at.desc()).limit(50)
        result = await db.execute(query)
        balls = result.scalars().all()

        # Get current match state
        match_query = select(CricketMatch).where(CricketMatch.id == match_id)
        match_result = await db.execute(match_query)
        match = match_result.scalar_one_or_none()

        if not match:
            raise HTTPException(status_code=404, detail="Match not found")

        return {
            "match_id": match_id,
            "current_score": {
                "team_a": {
                    "score": match.team_a_score,
                    "wickets": match.team_a_wickets,
                    "overs": match.team_a_overs,
                },
                "team_b": {
                    "score": match.team_b_score,
                    "wickets": match.team_b_wickets,
                    "overs": match.team_b_overs,
                },
            },
            "status": match.status,
            "current_innings": match.current_innings,
            "recent_balls": [
                {
                    "over": ball.over_number,
                    "ball": ball.ball_number,
                    "runs": ball.runs_scored,
                    "extras": ball.extras,
                    "is_wicket": ball.is_wicket,
                    "is_boundary": ball.is_boundary,
                    "timestamp": ball.created_at.isoformat(),
                }
                for ball in balls
            ],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting live updates: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
