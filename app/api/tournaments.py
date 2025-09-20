"""
Tournament API endpoints for managing cricket tournaments and competitions
"""
import logging
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.middleware import get_current_user
from app.models.tournament import Tournament
from app.models.user import User
from app.schemas.tournament import (
    TournamentCreate,
    TournamentResponse,
    TournamentTeamRegistration,
    TournamentTeamResponse,
    TournamentStandingResponse,
)
from app.services.tournament_service import TournamentService
from app.utils.database import get_db
from app.utils.error_handler import APIError

logger = logging.getLogger(__name__)

router = APIRouter(tags=["tournaments"])


@router.post("/", response_model=TournamentResponse, status_code=status.HTTP_201_CREATED)
async def create_tournament(
    tournament: TournamentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new tournament"""
    try:
        service = TournamentService(db)
        created_tournament = await service.create_tournament(
            name=tournament.name,
            tournament_type=tournament.tournament_type,
            created_by_id=str(current_user.id),
            start_date=tournament.start_date,
            registration_deadline=tournament.registration_deadline,
            max_teams=tournament.max_teams,
            min_teams=tournament.min_teams,
            entry_fee=tournament.entry_fee or Decimal("0"),
            prize_money=tournament.prize_money,
            description=tournament.description,
            rules=None,  # Not in schema
            venue_details=tournament.venue_details,
        )
        return TournamentResponse.from_orm(created_tournament)
    except APIError as e:
        logger.error(f"API error creating tournament: {e}")
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        logger.error(f"Unexpected error creating tournament: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create tournament"
        )


@router.post("/{tournament_id}/register", response_model=TournamentTeamResponse)
async def register_team_for_tournament(
    tournament_id: str,
    registration: TournamentTeamRegistration,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Register a team for a tournament"""
    try:
        service = TournamentService(db)
        team_registration = await service.register_team_for_tournament(
            tournament_id=tournament_id,
            team_id=str(registration.team_id),
            registered_by_id=str(current_user.id),
            payment_reference=registration.payment_reference,
        )
        return TournamentTeamResponse.from_orm(team_registration)
    except APIError as e:
        logger.error(f"API error registering team: {e}")
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        logger.error(f"Unexpected error registering team: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register team"
        )


@router.get("/{tournament_id}/standings", response_model=List[TournamentStandingResponse])
async def get_tournament_standings(
    tournament_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get tournament standings"""
    try:
        service = TournamentService(db)
        standings = await service.get_tournament_standings(tournament_id)
        return [TournamentStandingResponse.from_orm(standing) for standing in standings]
    except APIError as e:
        logger.error(f"API error getting standings: {e}")
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        logger.error(f"Unexpected error getting standings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get tournament standings"
        )


@router.get("/{tournament_id}/teams", response_model=List[TournamentTeamResponse])
async def get_tournament_teams(
    tournament_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all teams registered for a tournament"""
    try:
        service = TournamentService(db)
        teams = await service.get_tournament_teams(tournament_id)
        return [TournamentTeamResponse.from_orm(team) for team in teams]
    except APIError as e:
        logger.error(f"API error getting tournament teams: {e}")
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        logger.error(f"Unexpected error getting tournament teams: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get tournament teams"
        )


@router.post("/{tournament_id}/standings/update")
async def update_tournament_standings(
    tournament_id: str,
    team_id: str,
    points: int = 2,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Simple standings update (for testing/manual updates)"""
    try:
        service = TournamentService(db)
        await service.simple_update_standings(tournament_id, team_id, points)
        return {"message": "Standings updated successfully"}
    except APIError as e:
        logger.error(f"API error updating standings: {e}")
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        logger.error(f"Unexpected error updating standings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update standings"
        )