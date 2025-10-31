"""
Innings Service - Business Logic for Innings Management

This service handles:
- Creating new innings
- Managing current players (batsmen, bowler)
- Deriving live state from ball events
- Ending innings
- State transitions

Event Sourcing Pattern:
- Current state calculated from ball records
- No direct state updates - derived from events
- Real-time aggregation via SQL queries
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import joinedload

from src.models.cricket.innings import Innings, Over
from src.models.cricket.ball import Ball, Wicket
from src.models.cricket.match import Match
from src.models.cricket.team import Team
from src.models.user_auth import UserAuth
from src.models.enums import MatchStatus
from src.schemas.cricket.innings import (
    InningsCreateRequest,
    InningsResponse,
    InningsWithStateResponse,
    InningsStateSchema,
    InningsUpdateRequest,
    SetBatsmenRequest,
    SetBowlerRequest,
    OverResponse,
    CurrentBatsmanSchema,
    CurrentBowlerSchema
)
from src.core.exceptions import NotFoundError, ValidationError


class InningsService:
    """
    Service for innings management
    
    Responsibilities:
    - Start new innings
    - Set current players
    - Calculate live state from ball events
    - End innings
    - Over management
    """
    
    @staticmethod
    async def create_innings(
        match_id: UUID,
        request: InningsCreateRequest,
        db: AsyncSession
    ) -> InningsResponse:
        """
        Start a new innings
        
        Workflow:
            1. Validate match exists and is LIVE
            2. Validate teams are in match
            3. Create Innings record
            4. Return InningsResponse
        
        Args:
            match_id: Match UUID
            request: Innings creation data
            db: Database session
            
        Returns:
            InningsResponse with created innings
            
        Raises:
            NotFoundError: Match or teams not found
            ValidationError: Match not in LIVE state or team validation fails
        """
        # Validate match exists and is LIVE
        result = await db.execute(
            select(Match)
            .where(Match.id == match_id)
            .options(
                joinedload(Match.team_a),
                joinedload(Match.team_b)
            )
        )
        match = result.scalar_one_or_none()
        
        if not match:
            raise NotFoundError(f"Match {match_id} not found")
        
        if match.status not in [MatchStatus.LIVE, MatchStatus.TOSS_PENDING]:
            raise ValidationError(
                f"Cannot create innings for match in status '{match.status.value}'. "
                "Match must be LIVE or TOSS_PENDING."
            )
        
        # Validate teams
        team_ids = {match.team_a_id, match.team_b_id}
        if request.batting_team_id not in team_ids or request.bowling_team_id not in team_ids:
            raise ValidationError(
                "Batting and bowling teams must be participating in the match"
            )
        
        if request.batting_team_id == request.bowling_team_id:
            raise ValidationError(
                "Batting and bowling teams cannot be the same"
            )
        
        # Check for existing innings with same number
        result = await db.execute(
            select(Innings)
            .where(
                and_(
                    Innings.match_id == match_id,
                    Innings.innings_number == request.innings_number
                )
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            raise ValidationError(
                f"Innings {request.innings_number} already exists for this match"
            )
        
        # Create innings
        innings = Innings(
            match_id=match_id,
            innings_number=request.innings_number,
            batting_team_id=request.batting_team_id,
            bowling_team_id=request.bowling_team_id,
            target_runs=request.target_runs,
            started_at=datetime.utcnow()
        )
        
        db.add(innings)
        await db.commit()
        await db.refresh(innings)
        
        # Get team names
        batting_team = match.team_a if match.team_a_id == request.batting_team_id else match.team_b
        bowling_team = match.team_b if match.team_b_id == request.bowling_team_id else match.team_a
        
        return InningsResponse(
            id=innings.id,
            match_id=innings.match_id,
            innings_number=innings.innings_number,
            batting_team_id=innings.batting_team_id,
            bowling_team_id=innings.bowling_team_id,
            batting_team_name=batting_team.name,
            bowling_team_name=bowling_team.name,
            total_runs=innings.total_runs,
            wickets_fallen=innings.wickets_fallen,
            extras=innings.extras,
            current_over_number=innings.current_over_number,
            current_ball_in_over=innings.current_ball_in_over,
            is_completed=innings.is_completed,
            all_out=innings.all_out,
            declared=innings.declared,
            target_runs=innings.target_runs,
            striker_user_id=innings.striker_user_id,
            non_striker_user_id=innings.non_striker_user_id,
            current_bowler_user_id=innings.current_bowler_user_id,
            started_at=innings.started_at,
            completed_at=innings.completed_at,
            created_at=innings.created_at,
            updated_at=innings.updated_at
        )
    
    @staticmethod
    async def get_innings(
        innings_id: UUID,
        db: AsyncSession
    ) -> InningsResponse:
        """
        Get innings details
        
        Args:
            innings_id: Innings UUID
            db: Database session
            
        Returns:
            InningsResponse with innings details
            
        Raises:
            NotFoundError: Innings not found
        """
        result = await db.execute(
            select(Innings)
            .where(Innings.id == innings_id)
            .options(
                joinedload(Innings.match).joinedload(Match.team_a),
                joinedload(Innings.match).joinedload(Match.team_b)
            )
        )
        innings = result.scalar_one_or_none()
        
        if not innings:
            raise NotFoundError(f"Innings {innings_id} not found")
        
        # Get team names
        match = innings.match
        batting_team = match.team_a if match.team_a_id == innings.batting_team_id else match.team_b
        bowling_team = match.team_b if match.team_b_id == innings.bowling_team_id else match.team_a
        
        return InningsResponse(
            id=innings.id,
            match_id=innings.match_id,
            innings_number=innings.innings_number,
            batting_team_id=innings.batting_team_id,
            bowling_team_id=innings.bowling_team_id,
            batting_team_name=batting_team.name,
            bowling_team_name=bowling_team.name,
            total_runs=innings.total_runs,
            wickets_fallen=innings.wickets_fallen,
            extras=innings.extras,
            current_over_number=innings.current_over_number,
            current_ball_in_over=innings.current_ball_in_over,
            is_completed=innings.is_completed,
            all_out=innings.all_out,
            declared=innings.declared,
            target_runs=innings.target_runs,
            striker_user_id=innings.striker_user_id,
            non_striker_user_id=innings.non_striker_user_id,
            current_bowler_user_id=innings.current_bowler_user_id,
            started_at=innings.started_at,
            completed_at=innings.completed_at,
            created_at=innings.created_at,
            updated_at=innings.updated_at
        )
    
    @staticmethod
    async def set_batsmen(
        innings_id: UUID,
        request: SetBatsmenRequest,
        db: AsyncSession
    ) -> InningsResponse:
        """
        Set current batsmen (striker and non-striker)
        
        Used when:
        - Starting innings (set opening pair)
        - After wicket (set new batsman)
        - Player rotation
        
        Args:
            innings_id: Innings UUID
            request: Batsmen user IDs
            db: Database session
            
        Returns:
            Updated InningsResponse
            
        Raises:
            NotFoundError: Innings or players not found
            ValidationError: Players not in batting team
        """
        result = await db.execute(
            select(Innings)
            .where(Innings.id == innings_id)
        )
        innings = result.scalar_one_or_none()
        
        if not innings:
            raise NotFoundError(f"Innings {innings_id} not found")
        
        # TODO: Validate players are in batting team's playing XI
        # This requires team_memberships join - implement after team service is ready
        
        innings.striker_user_id = request.striker_user_id
        if request.non_striker_user_id:
            innings.non_striker_user_id = request.non_striker_user_id
        
        await db.commit()
        await db.refresh(innings)
        
        return await InningsService.get_innings(innings_id, db)
    
    @staticmethod
    async def set_bowler(
        innings_id: UUID,
        request: SetBowlerRequest,
        db: AsyncSession
    ) -> InningsResponse:
        """
        Set current bowler
        
        Used when:
        - Starting new over
        - Changing bowler mid-match
        
        Args:
            innings_id: Innings UUID
            request: Bowler user ID
            db: Database session
            
        Returns:
            Updated InningsResponse
            
        Raises:
            NotFoundError: Innings or bowler not found
            ValidationError: Bowler not in bowling team
        """
        result = await db.execute(
            select(Innings)
            .where(Innings.id == innings_id)
        )
        innings = result.scalar_one_or_none()
        
        if not innings:
            raise NotFoundError(f"Innings {innings_id} not found")
        
        # TODO: Validate bowler is in bowling team's playing XI
        
        innings.current_bowler_user_id = request.bowler_user_id
        
        await db.commit()
        await db.refresh(innings)
        
        return await InningsService.get_innings(innings_id, db)
    
    @staticmethod
    async def get_current_state(
        innings_id: UUID,
        db: AsyncSession
    ) -> InningsWithStateResponse:
        """
        Get innings with live state calculation
        
        Derives current state from ball events:
        - Current score (runs/wickets)
        - Overs bowled
        - Run rate
        - Batsmen stats (runs, balls, strike rate)
        - Bowler stats (overs, runs, wickets, economy)
        - Match situation (required rate for chase)
        
        Args:
            innings_id: Innings UUID
            db: Database session
            
        Returns:
            InningsWithStateResponse with live state
            
        Raises:
            NotFoundError: Innings not found
        """
        # Get innings details
        innings_response = await InningsService.get_innings(innings_id, db)
        
        # Get innings record
        result = await db.execute(
            select(Innings)
            .where(Innings.id == innings_id)
        )
        innings = result.scalar_one_or_none()
        
        # Calculate live state
        live_state = await InningsService._calculate_live_state(innings, db)
        
        return InningsWithStateResponse(
            **innings_response.model_dump(),
            live_state=live_state
        )
    
    @staticmethod
    async def _calculate_live_state(
        innings: Innings,
        db: AsyncSession
    ) -> InningsStateSchema:
        """
        Calculate live innings state from ball events
        
        Event Sourcing Pattern:
        - Query all balls for this innings
        - Aggregate runs, wickets, overs
        - Calculate batsmen and bowler statistics
        - Derive match situation
        
        Args:
            innings: Innings model
            db: Database session
            
        Returns:
            InningsStateSchema with calculated state
        """
        # Current score string
        current_score = f"{innings.total_runs}/{innings.wickets_fallen}"
        
        # Overs bowled (e.g., 15.3 = 15 overs + 3 balls)
        overs_bowled = innings.current_over_number + (innings.current_ball_in_over / 6.0)
        
        # Run rate (runs per over)
        run_rate = innings.total_runs / overs_bowled if overs_bowled > 0 else 0.0
        
        # Get current batsmen stats (if set)
        striker = None
        non_striker = None
        
        if innings.striker_user_id:
            striker = await InningsService._get_batsman_stats(
                innings.id,
                innings.striker_user_id,
                db
            )
        
        if innings.non_striker_user_id:
            non_striker = await InningsService._get_batsman_stats(
                innings.id,
                innings.non_striker_user_id,
                db
            )
        
        # Get current bowler stats (if set)
        current_bowler = None
        if innings.current_bowler_user_id:
            current_bowler = await InningsService._get_bowler_stats(
                innings.id,
                innings.current_bowler_user_id,
                db
            )
        
        # Chase scenario calculations
        target_runs = innings.target_runs
        required_run_rate = None
        runs_required = None
        balls_remaining = None
        
        if target_runs:
            runs_required = target_runs - innings.total_runs
            # TODO: Get match_rules from Match to calculate balls_remaining
            # For now, assume T20 (20 overs = 120 balls)
            total_balls = 120
            balls_bowled = int(innings.current_over_number * 6 + innings.current_ball_in_over)
            balls_remaining = total_balls - balls_bowled
            
            if balls_remaining > 0:
                overs_remaining = balls_remaining / 6.0
                required_run_rate = runs_required / overs_remaining if overs_remaining > 0 else 0.0
        
        return InningsStateSchema(
            current_score=current_score,
            overs_bowled=round(overs_bowled, 1),
            run_rate=round(run_rate, 2),
            striker=striker,
            non_striker=non_striker,
            current_bowler=current_bowler,
            target_runs=target_runs,
            required_run_rate=round(required_run_rate, 2) if required_run_rate else None,
            runs_required=runs_required,
            balls_remaining=balls_remaining
        )
    
    @staticmethod
    async def _get_batsman_stats(
        innings_id: UUID,
        user_id: UUID,
        db: AsyncSession
    ) -> CurrentBatsmanSchema:
        """
        Calculate batsman statistics from ball records
        
        Args:
            innings_id: Innings UUID
            user_id: Batsman user ID
            db: Database session
            
        Returns:
            CurrentBatsmanSchema with calculated stats
        """
        # Get batsman name
        result = await db.execute(
            select(UserAuth.email)  # TODO: Use display_name when available
            .where(UserAuth.user_id == user_id)
        )
        name = result.scalar_one_or_none() or "Unknown"
        
        # Calculate stats from balls
        result = await db.execute(
            select(
                func.sum(Ball.runs_scored).label('runs'),
                func.count(Ball.id).label('balls')
            )
            .where(
                and_(
                    Ball.innings_id == innings_id,
                    Ball.batsman_user_id == user_id,
                    Ball.is_legal_delivery == True
                )
            )
        )
        stats = result.first()
        
        runs_scored = int(stats.runs or 0)
        balls_faced = int(stats.balls or 0)
        strike_rate = (runs_scored / balls_faced * 100) if balls_faced > 0 else 0.0
        
        return CurrentBatsmanSchema(
            user_id=user_id,
            name=name,
            runs_scored=runs_scored,
            balls_faced=balls_faced,
            strike_rate=round(strike_rate, 2)
        )
    
    @staticmethod
    async def _get_bowler_stats(
        innings_id: UUID,
        user_id: UUID,
        db: AsyncSession
    ) -> CurrentBowlerSchema:
        """
        Calculate bowler statistics from ball records
        
        Args:
            innings_id: Innings UUID
            user_id: Bowler user ID
            db: Database session
            
        Returns:
            CurrentBowlerSchema with calculated stats
        """
        # Get bowler name
        result = await db.execute(
            select(UserAuth.email)  # TODO: Use display_name when available
            .where(UserAuth.user_id == user_id)
        )
        name = result.scalar_one_or_none() or "Unknown"
        
        # Calculate stats from balls
        result = await db.execute(
            select(
                func.count(Ball.id).label('legal_balls'),
                func.sum(Ball.runs_scored + Ball.extra_runs).label('runs'),
                func.count(Ball.id).filter(Ball.is_wicket == True).label('wickets')
            )
            .where(
                and_(
                    Ball.innings_id == innings_id,
                    Ball.bowler_user_id == user_id,
                    Ball.is_legal_delivery == True
                )
            )
        )
        stats = result.first()
        
        legal_balls = int(stats.legal_balls or 0)
        runs_conceded = int(stats.runs or 0)
        wickets_taken = int(stats.wickets or 0)
        
        # Calculate overs (e.g., 32 balls = 5.2 overs)
        overs_complete = legal_balls // 6
        balls_in_current_over = legal_balls % 6
        overs_bowled = overs_complete + (balls_in_current_over / 10.0)
        
        # Economy rate (runs per over)
        total_overs = legal_balls / 6.0
        economy_rate = runs_conceded / total_overs if total_overs > 0 else 0.0
        
        return CurrentBowlerSchema(
            user_id=user_id,
            name=name,
            overs_bowled=round(overs_bowled, 1),
            runs_conceded=runs_conceded,
            wickets_taken=wickets_taken,
            economy_rate=round(economy_rate, 2)
        )
    
    @staticmethod
    async def update_innings(
        innings_id: UUID,
        request: InningsUpdateRequest,
        db: AsyncSession
    ) -> InningsResponse:
        """
        Update innings details
        
        Used for:
        - Ending innings (is_completed=True)
        - Marking all-out
        - Recording declaration
        
        Args:
            innings_id: Innings UUID
            request: Update fields
            db: Database session
            
        Returns:
            Updated InningsResponse
            
        Raises:
            NotFoundError: Innings not found
        """
        result = await db.execute(
            select(Innings)
            .where(Innings.id == innings_id)
        )
        innings = result.scalar_one_or_none()
        
        if not innings:
            raise NotFoundError(f"Innings {innings_id} not found")
        
        # Apply updates
        if request.is_completed is not None:
            innings.is_completed = request.is_completed
            if request.is_completed:
                innings.completed_at = datetime.utcnow()
        
        if request.all_out is not None:
            innings.all_out = request.all_out
        
        if request.declared is not None:
            innings.declared = request.declared
        
        await db.commit()
        await db.refresh(innings)
        
        return await InningsService.get_innings(innings_id, db)
