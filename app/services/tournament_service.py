"""
Simplified Tournament service for managing cricket tournaments and competitions
Focuses on core functionality with proper SQLAlchemy usage
"""
import logging
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any

from sqlalchemy import and_, desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.cricket import CricketMatch
from app.models.tournament import Tournament, TournamentMatch, TournamentStanding, TournamentTeam
from app.models.user import Team, User
from app.schemas.tournament import TournamentFixtureGeneration
from app.utils.error_handler import (
    APIError,
    ValidationError,
    AlreadyExistsError,
    InternalServerError,
)

logger = logging.getLogger(__name__)


class TournamentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_tournament(
        self,
        name: str,
        tournament_type: str,
        created_by_id: str,
        start_date: datetime,
        registration_deadline: Optional[datetime] = None,
        max_teams: int = 16,
        min_teams: int = 4,
        entry_fee: Decimal = Decimal("0"),
        prize_money: Optional[Decimal] = None,
        description: Optional[str] = None,
        rules: Optional[str] = None,
        venue_details: Optional[str] = None,
    ) -> Tournament:
        """Create a new tournament"""
        try:
            tournament = Tournament(
                name=name,
                tournament_type=tournament_type,
                created_by_id=created_by_id,
                start_date=start_date,
                registration_deadline=registration_deadline,
                max_teams=max_teams,
                min_teams=min_teams,
                entry_fee=entry_fee,
                prize_money=prize_money,
                description=description,
                rules=rules,
                venue_details=venue_details,
                status="upcoming"
            )
            
            self.db.add(tournament)
            await self.db.commit()
            await self.db.refresh(tournament)
            
            logger.info(f"Tournament created: {tournament.id}")
            return tournament
            
        except Exception as e:
            logger.error(f"Failed to create tournament: {e}")
            await self.db.rollback()
            raise InternalServerError("create tournament")

    async def register_team_for_tournament(
        self, 
        tournament_id: str, 
        team_id: str, 
        registered_by_id: str,
        payment_reference: Optional[str] = None
    ) -> TournamentTeam:
        """Register a team for a tournament"""
        try:
            # Check if tournament exists and is accepting registrations
            tournament = await self._get_tournament_by_id(tournament_id)
            if not tournament:
                raise ValidationError("tournament_id", "Tournament not found")
            
            # Simple status check using string comparison
            tournament_status = str(tournament.status)
            if tournament_status not in ["upcoming", "registration_open"]:
                raise ValidationError("tournament_status", "Tournament registration is closed")
            
            # Check if team is already registered
            existing = await self.db.execute(
                select(TournamentTeam).where(
                    TournamentTeam.tournament_id == tournament_id,
                    TournamentTeam.team_id == team_id
                )
            )
            if existing.scalar_one_or_none():
                raise AlreadyExistsError("team registration", "Team already registered")
            
            # Create registration
            registration = TournamentTeam(
                tournament_id=tournament_id,
                team_id=team_id,
                registered_by_id=registered_by_id,
                payment_reference=payment_reference,
                registration_fee_paid=(tournament.entry_fee == 0 or payment_reference is not None)
            )
            
            self.db.add(registration)
            await self.db.commit()
            await self.db.refresh(registration)
            
            logger.info(f"Team {team_id} registered for tournament {tournament_id}")
            return registration
            
        except APIError:
            raise
        except Exception as e:
            logger.error(f"Failed to register team: {e}")
            await self.db.rollback()
            raise InternalServerError("register team")

    async def get_tournament_standings(self, tournament_id: str) -> List[TournamentStanding]:
        """Get tournament standings ordered by position"""
        try:
            result = await self.db.execute(
                select(TournamentStanding)
                .where(TournamentStanding.tournament_id == tournament_id)
                .order_by(TournamentStanding.position.asc())
                .options(selectinload(TournamentStanding.team))
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Failed to get standings: {e}")
            raise InternalServerError("get tournament standings")

    async def get_tournament_teams(self, tournament_id: str) -> List[TournamentTeam]:
        """Get all teams registered for a tournament"""
        try:
            result = await self.db.execute(
                select(TournamentTeam)
                .where(TournamentTeam.tournament_id == tournament_id)
                .options(selectinload(TournamentTeam.team))
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Failed to get tournament teams: {e}")
            raise InternalServerError("get tournament teams")

    async def simple_update_standings(self, tournament_id: str, team_id: str, points: int = 2) -> None:
        """Simple standings update - just add points for a win"""
        try:
            # Check if standing exists
            existing = await self.db.execute(
                select(TournamentStanding).where(
                    TournamentStanding.tournament_id == tournament_id,
                    TournamentStanding.team_id == team_id
                )
            )
            standing = existing.scalar_one_or_none()
            
            if not standing:
                # Create new standing
                standing = TournamentStanding(
                    tournament_id=tournament_id,
                    team_id=team_id,
                    matches_played=1,
                    matches_won=1 if points == 2 else 0,
                    matches_lost=0 if points >= 1 else 1,
                    matches_tied=1 if points == 1 else 0,
                    points=points,
                )
                self.db.add(standing)
            else:
                # Update existing standing
                await self.db.execute(
                    update(TournamentStanding)
                    .where(
                        TournamentStanding.tournament_id == tournament_id,
                        TournamentStanding.team_id == team_id
                    )
                    .values(
                        matches_played=TournamentStanding.matches_played + 1,
                        matches_won=TournamentStanding.matches_won + (1 if points == 2 else 0),
                        matches_lost=TournamentStanding.matches_lost + (0 if points >= 1 else 1),
                        matches_tied=TournamentStanding.matches_tied + (1 if points == 1 else 0),
                        points=TournamentStanding.points + points,
                    )
                )
            
            await self.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to update standings: {e}")
            await self.db.rollback()
            raise InternalServerError("update standings")

    async def _get_tournament_by_id(self, tournament_id: str) -> Optional[Tournament]:
        """Get tournament by ID"""
        result = await self.db.execute(
            select(Tournament).where(Tournament.id == tournament_id)
        )
        return result.scalar_one_or_none()

    async def _get_registered_teams_count(self, tournament_id: str) -> int:
        """Get count of registered teams"""
        result = await self.db.execute(
            select(func.count(TournamentTeam.team_id)).where(
                TournamentTeam.tournament_id == tournament_id
            )
        )
        return result.scalar() or 0