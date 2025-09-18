"""
Tournament service for managing cricket tournaments and competitions
Integrates with Phase 1 team and match services
"""
import logging
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Tuple

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
    PermissionDeniedError,
    AlreadyExistsError,
    InternalServerError
)

logger = logging.getLogger(__name__)


class TournamentService:
    """Service for tournament management and operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_tournament(self, tournament_data: dict, creator_id: str) -> Tournament:
        """Create a new tournament"""
        try:
            tournament = Tournament(
                **tournament_data,
                created_by_id=creator_id,
                status="upcoming"
            )
            
            self.db.add(tournament)
            await self.db.commit()
            await self.db.refresh(tournament)
            
            logger.info(f"Tournament created: {tournament.name} by {creator_id}")
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
            
            if tournament.status not in ["upcoming", "registration_open"]:
                raise ValidationError("tournament_status", "Tournament registration is closed")
            
            # Check registration deadline
            if tournament.registration_deadline and datetime.utcnow() > tournament.registration_deadline:
                raise ValidationError("registration_deadline", "Registration deadline has passed")
            
            # Check if team is already registered
            existing_registration = await self.db.execute(
                select(TournamentTeam).where(
                    TournamentTeam.tournament_id == tournament_id,
                    TournamentTeam.team_id == team_id
                )
            )
            if existing_registration.scalar_one_or_none():
                raise AlreadyExistsError("team registration", f"Team already registered for this tournament")
            
            # Check if tournament is full
            current_teams_count = await self._get_registered_teams_count(tournament_id)
            if current_teams_count >= tournament.max_teams:
                raise ValidationError("max_teams", "Tournament is full")
            
            # Create registration
            registration = TournamentTeam(
                tournament_id=tournament_id,
                team_id=team_id,
                registered_by_id=registered_by_id,
                payment_reference=payment_reference,
                registration_fee_paid=(tournament.entry_fee == 0 or payment_reference is not None)
            )
            
            self.db.add(registration)
            
            # Initialize standings entry
            standing = TournamentStanding(
                tournament_id=tournament_id,
                team_id=team_id
            )
            self.db.add(standing)
            
            await self.db.commit()
            await self.db.refresh(registration)
            
            logger.info(f"Team {team_id} registered for tournament {tournament_id}")
            return registration
            
        except APIError:
            raise
        except Exception as e:
            logger.error(f"Failed to register team for tournament: {e}")
            await self.db.rollback()
            raise InternalServerError("register team for tournament")
    
    async def generate_tournament_fixtures(
        self, 
        tournament_id: str, 
        fixture_config: TournamentFixtureGeneration,
        creator_id: str
    ) -> List[TournamentMatch]:
        """Generate tournament fixtures based on tournament type"""
        try:
            tournament = await self._get_tournament_by_id(tournament_id)
            if not tournament:
                raise ValidationError("tournament_id", "Tournament not found")
            
            # Check permission
            if tournament.created_by_id != uuid.UUID(creator_id):
                raise PermissionDeniedError("generate fixtures for this tournament")
            
            # Check if fixtures already exist
            existing_fixtures = await self.db.execute(
                select(TournamentMatch).where(TournamentMatch.tournament_id == tournament_id)
            )
            if existing_fixtures.scalars().first():
                raise ValidationError("fixtures", "Fixtures already generated for this tournament")
            
            # Get registered teams
            teams = await self._get_tournament_teams(tournament_id)
            if len(teams) < tournament.min_teams:
                raise ValidationError("min_teams", f"Need at least {tournament.min_teams} teams to generate fixtures")
            
            # Generate fixtures based on tournament type
            if tournament.tournament_type == "round_robin":
                fixtures = await self._generate_round_robin_fixtures(tournament, teams, fixture_config)
            elif tournament.tournament_type == "knockout":
                fixtures = await self._generate_knockout_fixtures(tournament, teams, fixture_config)
            elif tournament.tournament_type == "league":
                fixtures = await self._generate_league_fixtures(tournament, teams, fixture_config)
            else:
                raise ValidationError("tournament_type", "Unsupported tournament type")
            
            # Save fixtures to database
            self.db.add_all(fixtures)
            
            # Update tournament status
            await self.db.execute(
                update(Tournament)
                .where(Tournament.id == tournament_id)
                .values(status="ongoing", updated_at=datetime.utcnow())
            )
            
            await self.db.commit()
            
            logger.info(f"Generated {len(fixtures)} fixtures for tournament {tournament_id}")
            return fixtures
            
        except APIError:
            raise
        except Exception as e:
            logger.error(f"Failed to generate tournament fixtures: {e}")
            await self.db.rollback()
            raise InternalServerError("generate tournament fixtures")
    
    async def update_standings_after_match(self, match_id: str) -> None:
        """Update tournament standings after a match is completed"""
        try:
            # Get tournament match
            result = await self.db.execute(
                select(TournamentMatch)
                .where(TournamentMatch.match_id == match_id)
            )
            tournament_match = result.scalar_one_or_none()
            
            if not tournament_match:
                # Not a tournament match, skip
                return
            
            # Get the actual match directly
            match_result = await self.db.execute(
                select(CricketMatch).where(CricketMatch.id == match_id)
            )
            match = match_result.scalar_one_or_none()
            
            if not match or match.status != "completed":
                # Match not found or not completed yet
                return
            
            # Update standings for both teams
            await self._update_team_standing(
                str(tournament_match.tournament_id),
                match.team_a_id,
                match
            )
            await self._update_team_standing(
                str(tournament_match.tournament_id),
                match.team_b_id,
                match
            )
            
            # Recalculate positions
            await self._recalculate_tournament_positions(str(tournament_match.tournament_id))
            
            await self.db.commit()
            
            logger.info(f"Updated tournament standings for match {match_id}")
            
        except Exception as e:
            logger.error(f"Failed to update tournament standings: {e}")
            await self.db.rollback()
            raise InternalServerError("update tournament standings")
    
    async def get_tournament_standings(self, tournament_id: str) -> List[TournamentStanding]:
        """Get tournament standings ordered by position"""
        try:
            result = await self.db.execute(
                select(TournamentStanding)
                .options(selectinload(TournamentStanding.team))
                .where(TournamentStanding.tournament_id == tournament_id)
                .order_by(
                    TournamentStanding.points.desc(),
                    TournamentStanding.net_run_rate.desc(),
                    TournamentStanding.matches_won.desc()
                )
            )
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Failed to get tournament standings: {e}")
            raise InternalServerError("retrieve tournament standings")
    
    # Private helper methods
    async def _get_tournament_by_id(self, tournament_id: str) -> Optional[Tournament]:
        """Get tournament by ID"""
        result = await self.db.execute(
            select(Tournament).where(Tournament.id == tournament_id)
        )
        return result.scalar_one_or_none()
    
    async def _get_registered_teams_count(self, tournament_id: str) -> int:
        """Get count of registered teams"""
        result = await self.db.execute(
            select(func.count(TournamentTeam.team_id))
            .where(TournamentTeam.tournament_id == tournament_id)
        )
        return result.scalar_one()
    
    async def _get_tournament_teams(self, tournament_id: str) -> List[TournamentTeam]:
        """Get all registered teams for tournament"""
        result = await self.db.execute(
            select(TournamentTeam)
            .options(selectinload(TournamentTeam.team))
            .where(TournamentTeam.tournament_id == tournament_id)
            .where(TournamentTeam.status == "registered")
        )
        return result.scalars().all()
    
    async def _generate_round_robin_fixtures(
        self, 
        tournament: Tournament, 
        teams: List[TournamentTeam], 
        config: TournamentFixtureGeneration
    ) -> List[TournamentMatch]:
        """Generate round-robin tournament fixtures"""
        fixtures = []
        match_number = 1
        current_date = config.start_date or tournament.start_date
        
        # Generate all possible pairings
        for i, team_a in enumerate(teams):
            for team_b in teams[i+1:]:
                # Create cricket match
                cricket_match = CricketMatch(
                    team_a_id=team_a.team_id,
                    team_b_id=team_b.team_id,
                    overs_per_innings=tournament.overs_per_innings,
                    venue=config.venues[0] if config.venues else "TBD",
                    match_date=current_date,
                    created_by_id=tournament.created_by_id,
                    status="upcoming"
                )
                self.db.add(cricket_match)
                await self.db.flush()  # Get the ID
                
                # Create tournament match
                tournament_match = TournamentMatch(
                    tournament_id=tournament.id,
                    match_id=cricket_match.id,
                    round_number=1,
                    match_number=match_number,
                    stage="group",
                    scheduled_date=current_date,
                    venue=cricket_match.venue
                )
                fixtures.append(tournament_match)
                
                match_number += 1
                current_date += timedelta(hours=config.match_interval_hours)
        
        return fixtures
    
    async def _generate_knockout_fixtures(
        self, 
        tournament: Tournament, 
        teams: List[TournamentTeam], 
        config: TournamentFixtureGeneration
    ) -> List[TournamentMatch]:
        """Generate knockout tournament fixtures"""
        fixtures = []
        match_number = 1
        current_date = config.start_date or tournament.start_date
        
        # For knockout, we'll generate first round only
        # Subsequent rounds are generated as matches are completed
        team_pairs = []
        for i in range(0, len(teams), 2):
            if i + 1 < len(teams):
                team_pairs.append((teams[i], teams[i + 1]))
        
        for team_a, team_b in team_pairs:
            # Create cricket match
            cricket_match = CricketMatch(
                team_a_id=team_a.team_id,
                team_b_id=team_b.team_id,
                overs_per_innings=tournament.overs_per_innings,
                venue=config.venues[0] if config.venues else "TBD",
                match_date=current_date,
                created_by_id=tournament.created_by_id,
                status="upcoming"
            )
            self.db.add(cricket_match)
            await self.db.flush()
            
            # Create tournament match
            tournament_match = TournamentMatch(
                tournament_id=tournament.id,
                match_id=cricket_match.id,
                round_number=1,
                match_number=match_number,
                stage="first_round",
                scheduled_date=current_date,
                venue=cricket_match.venue,
                is_knockout=True
            )
            fixtures.append(tournament_match)
            
            match_number += 1
            current_date += timedelta(hours=config.match_interval_hours)
        
        return fixtures
    
    async def _generate_league_fixtures(
        self, 
        tournament: Tournament, 
        teams: List[TournamentTeam], 
        config: TournamentFixtureGeneration
    ) -> List[TournamentMatch]:
        """Generate league tournament fixtures (similar to round-robin but with return matches)"""
        # For now, implement as double round-robin
        return await self._generate_round_robin_fixtures(tournament, teams, config)
    
    async def _update_team_standing(
        self, 
        tournament_id: str, 
        team_id: uuid.UUID, 
        match: CricketMatch
    ) -> None:
        """Update standing for a specific team after a match"""
        # Determine match result for this team
        is_team_a = (match.team_a_id == team_id)
        
        # Get actual score values (these should be integers, not Column objects)
        team_score = match.team_a_score if is_team_a else match.team_b_score
        opponent_score = match.team_b_score if is_team_a else match.team_a_score
        team_overs = match.team_a_overs if is_team_a else match.team_b_overs
        opponent_overs = match.team_b_overs if is_team_a else match.team_a_overs
        
        # Determine result - make sure we're comparing actual values
        won = (team_score is not None and opponent_score is not None and team_score > opponent_score)
        tied = (team_score is not None and opponent_score is not None and team_score == opponent_score)
        points = 2 if won else (1 if tied else 0)
        
        # Update standing
        await self.db.execute(
            update(TournamentStanding)
            .where(
                and_(
                    TournamentStanding.tournament_id == tournament_id,
                    TournamentStanding.team_id == team_id
                )
            )
            .values(
                matches_played=TournamentStanding.matches_played + 1,
                matches_won=TournamentStanding.matches_won + (1 if won else 0),
                matches_lost=TournamentStanding.matches_lost + (1 if not won and not tied else 0),
                matches_tied=TournamentStanding.matches_tied + (1 if tied else 0),
                points=TournamentStanding.points + points,
                runs_scored=TournamentStanding.runs_scored + team_score,
                runs_conceded=TournamentStanding.runs_conceded + opponent_score,
                overs_faced=TournamentStanding.overs_faced + team_overs,
                overs_bowled=TournamentStanding.overs_bowled + opponent_overs,
                last_updated=datetime.utcnow()
            )
        )
        
        # Recalculate net run rate
        await self._calculate_net_run_rate(tournament_id, team_id)
    
    async def _calculate_net_run_rate(self, tournament_id: str, team_id: uuid.UUID) -> None:
        """Calculate and update net run rate for a team"""
        result = await self.db.execute(
            select(TournamentStanding).where(
                and_(
                    TournamentStanding.tournament_id == tournament_id,
                    TournamentStanding.team_id == team_id
                )
            )
        )
        standing = result.scalar_one()
        
        if standing.overs_faced > 0 and standing.overs_bowled > 0:
            run_rate_for = standing.runs_scored / float(standing.overs_faced)
            run_rate_against = standing.runs_conceded / float(standing.overs_bowled)
            net_run_rate = run_rate_for - run_rate_against
            
            await self.db.execute(
                update(TournamentStanding)
                .where(
                    and_(
                        TournamentStanding.tournament_id == tournament_id,
                        TournamentStanding.team_id == team_id
                    )
                )
                .values(net_run_rate=Decimal(str(round(net_run_rate, 2))))
            )
    
    async def _recalculate_tournament_positions(self, tournament_id: str) -> None:
        """Recalculate positions for all teams in tournament"""
        standings = await self.get_tournament_standings(tournament_id)
        
        for position, standing in enumerate(standings, 1):
            await self.db.execute(
                update(TournamentStanding)
                .where(
                    and_(
                        TournamentStanding.tournament_id == tournament_id,
                        TournamentStanding.team_id == standing.team_id
                    )
                )
                .values(
                    previous_position=standing.current_position,
                    current_position=position
                )
            )