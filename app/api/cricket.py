import logging
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.middleware import get_current_active_user
from app.models.cricket import CricketBall, CricketMatch
from app.models.user import User
from app.schemas.cricket import (
    BallRecord,
    BallResponse,
    CricketMatchCreate,
    MatchResponseBasic,
)
from app.services.cricket_service import CricketService
from app.utils.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
async def cricket_health():
    return {"success": True, "message": "Cricket service healthy"}


@router.post("/cricket", response_model=MatchResponseBasic)
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
        logger.error(f"Failed to create match: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create match",
        )


@router.get("/cricket", response_model=List[MatchResponseBasic])
async def get_matches(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get all matches"""
    try:
        result = await db.execute(
            select(CricketMatch).order_by(CricketMatch.created_at.desc())
        )
        matches = result.scalars().all()

        return matches

    except Exception as e:
        logger.error(f"Failed to get matches: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve matches",
        )


@router.get("/cricket/{match_id}", response_model=MatchResponseBasic)
async def get_match(
    match_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get specific match details"""
    try:
        result = await db.execute(
            select(CricketMatch).where(CricketMatch.id == match_id)
        )
        match = result.scalar_one_or_none()

        if not match:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Match not found"
            )

        return match

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get match: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve match",
        )


@router.post("/cricket/{match_id}/balls", response_model=BallResponse)
async def record_ball(
    match_id: uuid.UUID,
    ball_data: BallRecord,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Record a ball in the cricket match"""
    try:
        # Get match
        result = await db.execute(
            select(CricketMatch).where(CricketMatch.id == match_id)
        )
        match = result.scalar_one_or_none()

        if not match:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Match not found"
            )

        # Use cricket service to record ball
        cricket_service = CricketService(db)
        ball, scorecard = await cricket_service.record_ball(str(match_id), ball_data)

        logger.info(f"Ball recorded in match {match_id}")
        return ball

    except Exception as e:
        logger.error(f"Failed to record ball: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record ball",
        )


@router.get("/cricket/{match_id}/scorecard")
async def get_scorecard(
    match_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get live scorecard for a match"""
    try:
        # Get match
        result = await db.execute(
            select(CricketMatch).where(CricketMatch.id == match_id)
        )
        match = result.scalar_one_or_none()

        if not match:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Match not found"
            )

        # Generate scorecard
        cricket_service = CricketService(db)
        scorecard = await cricket_service.get_match_scorecard(str(match_id))

        return scorecard

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get scorecard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve scorecard",
        )
