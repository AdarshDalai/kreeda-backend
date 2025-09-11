import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.middleware import get_current_active_user
from app.models.user import User
from app.services.stats_service import CricketStatsEngine
from app.utils.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
async def stats_health():
    return {"success": True, "message": "Statistics service healthy"}


@router.get("/players/{player_id}/stats")
async def get_player_stats(
    player_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get comprehensive player statistics"""
    try:
        stats_engine = CricketStatsEngine(db)
        stats = await stats_engine.get_player_career_stats(player_id)

        return {"success": True, "data": stats}

    except Exception as e:
        logger.error(f"Error fetching player stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch player statistics",
        )


@router.get("/teams/{team_id}/stats")
async def get_team_stats(
    team_id: str,
    season_year: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get team statistics"""
    try:
        stats_engine = CricketStatsEngine(db)
        stats = await stats_engine.get_team_stats(team_id, season_year)

        return {"success": True, "data": stats}

    except Exception as e:
        logger.error(f"Error fetching team stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch team statistics",
        )


@router.get("/teams/{team_id}/form")
async def get_team_form(
    team_id: str,
    last_matches: int = 5,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get recent form for a team"""
    try:
        stats_engine = CricketStatsEngine(db)
        form = await stats_engine.get_recent_form(team_id, last_matches)

        return {"success": True, "data": form}

    except Exception as e:
        logger.error(f"Error fetching team form: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch team form",
        )


@router.get("/matches/{match_id}/insights")
async def get_match_insights(
    match_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get detailed match insights and analytics"""
    try:
        stats_engine = CricketStatsEngine(db)
        insights = await stats_engine.get_match_insights(match_id)

        if "error" in insights:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=insights["error"]
            )

        return {"success": True, "data": insights}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching match insights: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch match insights",
        )
