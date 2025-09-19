"""
Statistics API endpoints for player and team analytics
Provides comprehensive performance tracking and leaderboards
"""
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.middleware import get_current_user
from app.models.user import User
from app.schemas.statistics import (
    PlayerCareerStatsResponse,
    PlayerMatchPerformanceResponse,
    TeamSeasonStatsResponse,
    StatsFilterRequest,
    LeaderboardRequest,
)
from app.services.statistics_service import StatisticsService
from app.utils.database import get_db
from app.utils.error_handler import APIError

logger = logging.getLogger(__name__)

router = APIRouter(tags=["statistics"])


@router.get("/health")
async def statistics_health_check():
    """Health check for statistics system"""
    return {
        "status": "healthy", 
        "service": "statistics",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/career/{user_id}", response_model=Optional[PlayerCareerStatsResponse])
async def get_player_career_stats(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get comprehensive career statistics for a player"""
    try:
        service = StatisticsService(db)
        career_stats = await service.get_player_career_stats(user_id)
        
        if not career_stats:
            return None
        
        return PlayerCareerStatsResponse.from_orm(career_stats)
        
    except APIError as e:
        logger.error(f"API error getting career stats: {e}")
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        logger.error(f"Unexpected error getting career stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get career statistics"
        )


@router.post("/career/{user_id}/update", response_model=PlayerCareerStatsResponse)
async def update_player_career_stats(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update or create career statistics based on current match data"""
    try:
        service = StatisticsService(db)
        career_stats = await service.update_or_create_career_stats(user_id)
        return PlayerCareerStatsResponse.from_orm(career_stats)
        
    except APIError as e:
        logger.error(f"API error updating career stats: {e}")
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        logger.error(f"Unexpected error updating career stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update career statistics"
        )


@router.get("/leaderboard/{category}")
async def get_leaderboard(
    category: str,
    limit: int = Query(default=20, ge=1, le=100),
    min_matches: int = Query(default=5, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get leaderboard for a specific category"""
    try:
        valid_categories = ["batting_avg", "runs", "wickets", "strike_rate", "economy_rate"]
        if category not in valid_categories:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid category. Must be one of: {', '.join(valid_categories)}"
            )
        
        service = StatisticsService(db)
        leaderboard = await service.get_leaderboard_data(category, limit, min_matches)
        
        return {
            "category": category,
            "limit": limit,
            "min_matches": min_matches,
            "entries": leaderboard
        }
        
    except APIError as e:
        logger.error(f"API error getting leaderboard: {e}")
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        logger.error(f"Unexpected error getting leaderboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get leaderboard"
        )


@router.get("/matches/{user_id}")
async def get_player_match_history(
    user_id: str,
    limit: int = Query(default=10, ge=1, le=50),
    tournament_id: Optional[str] = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get player's match performance history"""
    try:
        service = StatisticsService(db)
        match_history = await service.get_player_match_history(user_id, limit, tournament_id)
        
        return {
            "user_id": user_id,
            "matches": match_history,
            "total_matches": len(match_history)
        }
        
    except APIError as e:
        logger.error(f"API error getting match history: {e}")
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        logger.error(f"Unexpected error getting match history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get match history"
        )


@router.get("/team/{team_id}/season")
async def get_team_season_summary(
    team_id: str,
    season_year: Optional[int] = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get team performance summary for a season"""
    try:
        service = StatisticsService(db)
        season_summary = await service.get_team_season_summary(team_id, season_year)
        
        return {
            "team_id": team_id,
            "season_year": season_year,
            "summary": season_summary
        }
        
    except APIError as e:
        logger.error(f"API error getting team season summary: {e}")
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        logger.error(f"Unexpected error getting team season summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get team season summary"
        )


@router.get("/tournament/{tournament_id}/leaderboard")
async def get_tournament_leaderboard(
    tournament_id: str,
    category: str = Query(default="runs"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get tournament-specific leaderboard"""
    try:
        service = StatisticsService(db)
        leaderboard = await service.get_tournament_leaderboard(tournament_id, category)
        
        return {
            "tournament_id": tournament_id,
            "category": category,
            "entries": leaderboard
        }
        
    except APIError as e:
        logger.error(f"API error getting tournament leaderboard: {e}")
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        logger.error(f"Unexpected error getting tournament leaderboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get tournament leaderboard"
        )


@router.get("/analytics/overview")
async def get_analytics_overview(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get analytics overview with key statistics"""
    try:
        service = StatisticsService(db)
        
        # Get multiple leaderboards for overview
        top_run_scorers = await service.get_leaderboard_data("runs", limit=5)
        top_wicket_takers = await service.get_leaderboard_data("wickets", limit=5)
        top_batting_averages = await service.get_leaderboard_data("batting_avg", limit=5)
        
        return {
            "top_run_scorers": top_run_scorers,
            "top_wicket_takers": top_wicket_takers,
            "top_batting_averages": top_batting_averages,
            "last_updated": "2024-01-01T00:00:00Z"  # Could be made dynamic
        }
        
    except APIError as e:
        logger.error(f"API error getting analytics overview: {e}")
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        logger.error(f"Unexpected error getting analytics overview: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get analytics overview"
        )


@router.get("/player/{user_id}/summary")
async def get_player_comprehensive_summary(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get comprehensive player summary with stats, recent form, and rankings"""
    try:
        service = StatisticsService(db)
        
        # Get career stats
        career_stats = await service.get_player_career_stats(user_id)
        if not career_stats:
            # Create initial stats if none exist
            career_stats = await service.update_or_create_career_stats(user_id)
        
        # Get recent match history
        recent_matches = await service.get_player_match_history(user_id, limit=5)
        
        # Get current career stats summary
        calculated_stats = await service.calculate_career_stats_from_matches(user_id)
        
        return {
            "user_id": user_id,
            "career_stats": PlayerCareerStatsResponse.from_orm(career_stats) if career_stats else None,
            "recent_matches": recent_matches,
            "calculated_stats": calculated_stats,
            "summary": {
                "total_matches": calculated_stats.get("total_matches", 0),
                "career_runs": calculated_stats.get("total_runs", 0),
                "career_wickets": calculated_stats.get("total_wickets", 0),
                "batting_average": calculated_stats.get("batting_average", 0),
                "strike_rate": calculated_stats.get("batting_strike_rate", 0),
            }
        }
        
    except APIError as e:
        logger.error(f"API error getting player summary: {e}")
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        logger.error(f"Unexpected error getting player summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get player summary"
        )