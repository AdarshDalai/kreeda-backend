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
        rules: Optional[str] = None,  # Kept for API compatibility but not used
        venue_details: Optional[str] = None,
    ) -> Tournament:
        """Create a new tournament"""
        try:
            # Convert string UUID to UUID object
            created_by_uuid = uuid.UUID(created_by_id) if isinstance(created_by_id, str) else created_by_id
            
            tournament = Tournament(
                name=name,
                tournament_type=tournament_type,
                created_by_id=created_by_uuid,
                start_date=start_date,
                registration_deadline=registration_deadline,
                max_teams=max_teams,
                min_teams=min_teams,
                entry_fee=entry_fee,
                prize_money=prize_money,
                description=description,
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
            # Convert string UUIDs to UUID objects
            tournament_uuid = uuid.UUID(tournament_id) if isinstance(tournament_id, str) else tournament_id
            team_uuid = uuid.UUID(team_id) if isinstance(team_id, str) else team_id
            registered_by_uuid = uuid.UUID(registered_by_id) if isinstance(registered_by_id, str) else registered_by_id
            
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
                    TournamentTeam.tournament_id == tournament_uuid,
                    TournamentTeam.team_id == team_uuid
                )
            )
            if existing.scalar_one_or_none():
                raise AlreadyExistsError("team registration", "Team already registered")
            
            # Create registration
            registration = TournamentTeam(
                tournament_id=tournament_uuid,
                team_id=team_uuid,
                registered_by_id=registered_by_uuid,
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
            # Convert string UUID to UUID object
            tournament_uuid = uuid.UUID(tournament_id) if isinstance(tournament_id, str) else tournament_id
            
            result = await self.db.execute(
                select(TournamentStanding)
                .where(TournamentStanding.tournament_id == tournament_uuid)
                .order_by(TournamentStanding.current_position.asc())
                .options(selectinload(TournamentStanding.team))
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Failed to get standings: {e}")
            raise InternalServerError("get tournament standings")

    async def get_tournament_teams(self, tournament_id: str) -> List[TournamentTeam]:
        """Get all teams registered for a tournament"""
        try:
            # Convert string UUID to UUID object
            tournament_uuid = uuid.UUID(tournament_id) if isinstance(tournament_id, str) else tournament_id
            
            result = await self.db.execute(
                select(TournamentTeam)
                .where(TournamentTeam.tournament_id == tournament_uuid)
                .options(selectinload(TournamentTeam.team))
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Failed to get tournament teams: {e}")
            raise InternalServerError("get tournament teams")

    async def simple_update_standings(self, tournament_id: str, team_id: str, points: int = 2) -> None:
        """Simple standings update - just add points for a win"""
        try:
            # Convert string UUIDs to UUID objects
            tournament_uuid = uuid.UUID(tournament_id) if isinstance(tournament_id, str) else tournament_id
            team_uuid = uuid.UUID(team_id) if isinstance(team_id, str) else team_id
            
            # Check if standing exists
            existing = await self.db.execute(
                select(TournamentStanding).where(
                    TournamentStanding.tournament_id == tournament_uuid,
                    TournamentStanding.team_id == team_uuid
                )
            )
            standing = existing.scalar_one_or_none()
            
            if not standing:
                # Create new standing
                standing = TournamentStanding(
                    tournament_id=tournament_uuid,
                    team_id=team_uuid,
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
                        TournamentStanding.tournament_id == tournament_uuid,
                        TournamentStanding.team_id == team_uuid
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

    async def get_tournaments(self, skip: int = 0, limit: int = 100) -> List[Tournament]:
        """Get list of tournaments"""
        try:
            result = await self.db.execute(
                select(Tournament).offset(skip).limit(limit).order_by(Tournament.created_at.desc())
            )
            tournaments = result.scalars().all()
            return list(tournaments)
        except Exception as e:
            logger.error(f"Failed to get tournaments: {e}")
            raise InternalServerError("get tournaments")

    async def get_tournament_by_id(self, tournament_id: str) -> Optional[Tournament]:
        """Get tournament by ID"""
        try:
            return await self._get_tournament_by_id(tournament_id)
        except Exception as e:
            logger.error(f"Failed to get tournament: {e}")
            raise InternalServerError("get tournament")

    async def update_tournament(
        self,
        tournament_id: str,
        updates: dict,
        updated_by_id: str
    ) -> Optional[Tournament]:
        """Update tournament"""
        try:
            tournament = await self._get_tournament_by_id(tournament_id)
            if not tournament:
                raise APIError(
                    code="TOURNAMENT_NOT_FOUND",
                    message=f"Tournament with ID {tournament_id} not found",
                    status_code=404
                )
            
            # Update only provided fields
            for field, value in updates.items():
                if hasattr(tournament, field) and value is not None:
                    setattr(tournament, field, value)
            
            # Set updated_at manually
            if hasattr(tournament, 'updated_at'):
                setattr(tournament, 'updated_at', datetime.utcnow())
            
            await self.db.commit()
            await self.db.refresh(tournament)
            return tournament
        except APIError:
            raise
        except Exception as e:
            logger.error(f"Failed to update tournament: {e}")
            await self.db.rollback()
            raise InternalServerError("update tournament")

    async def delete_tournament(self, tournament_id: str) -> bool:
        """Delete tournament"""
        try:
            tournament = await self._get_tournament_by_id(tournament_id)
            if not tournament:
                raise APIError(
                    code="TOURNAMENT_NOT_FOUND",
                    message=f"Tournament with ID {tournament_id} not found",
                    status_code=404
                )
            
            await self.db.delete(tournament)
            await self.db.commit()
            return True
        except APIError:
            raise
        except Exception as e:
            logger.error(f"Failed to delete tournament: {e}")
            await self.db.rollback()
            raise InternalServerError("delete tournament")

    async def _get_tournament_by_id(self, tournament_id: str) -> Optional[Tournament]:
        """Get tournament by ID"""
        # Convert string UUID to UUID object
        tournament_uuid = uuid.UUID(tournament_id) if isinstance(tournament_id, str) else tournament_id
        
        result = await self.db.execute(
            select(Tournament).where(Tournament.id == tournament_uuid)
        )
        return result.scalar_one_or_none()

    async def _get_registered_teams_count(self, tournament_id: str) -> int:
        """Get count of registered teams"""
        # Convert string UUID to UUID object
        tournament_uuid = uuid.UUID(tournament_id) if isinstance(tournament_id, str) else tournament_id
        
        result = await self.db.execute(
            select(func.count(TournamentTeam.team_id)).where(
                TournamentTeam.tournament_id == tournament_uuid
            )
        )
        return result.scalar() or 0