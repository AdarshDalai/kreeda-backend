"""
Ball Service - Event Sourcing for Ball-by-Ball Scoring

This service handles:
- Recording balls (atomic cricket events)
- Creating wicket records
- Updating innings aggregates
- Managing overs
- Real-time state updates

Event Sourcing Pattern:
- Balls are IMMUTABLE once created
- Current state derived from ball history
- No updates to ball records - only inserts
- Disputes handled via scoring_events table
"""
from datetime import datetime
from typing import Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, update
from sqlalchemy.orm import joinedload

from src.models.cricket.ball import Ball, Wicket
from src.models.cricket.innings import Innings, Over
from src.models.cricket.match import Match
from src.models.user_auth import UserAuth
from src.schemas.cricket.ball import (
    BallCreateRequest,
    BallResponse,
    WicketResponse,
    WicketDetailsSchema
)
from src.core.exceptions import NotFoundError, ValidationError
from src.core.websocket_manager import ConnectionManager
from src.schemas.cricket.websocket import WebSocketEventType


class BallService:
    """
    Service for ball-by-ball scoring
    
    Event Sourcing Core:
    - Each ball is an immutable event
    - State derived from event log
    - Real-time aggregation
    - Wickets linked to balls
    """
    
    @staticmethod
    async def record_ball(
        request: BallCreateRequest,
        db: AsyncSession,
        connection_manager: Optional[ConnectionManager] = None
    ) -> BallResponse:
        """
        Record a ball bowled (PRIMARY SCORING ENDPOINT)
        
        Event Sourcing Workflow:
            1. Validate innings exists and not completed
            2. Create immutable Ball record
            3. If wicket: Create linked Wicket record
            4. Update innings aggregates (runs, wickets, overs)
            5. Update over aggregates
            6. Check for over completion
            7. Broadcast WebSocket events to spectators
            8. Return BallResponse with enriched data
        
        This is the ATOMIC UNIT of cricket scoring.
        Every legal delivery and extra creates a Ball record.
        
        Args:
            request: Ball details
            db: Database session
            connection_manager: WebSocket manager for broadcasting (optional)
            
        Returns:
            BallResponse with ball and wicket details
            
        Raises:
            NotFoundError: Innings or over not found
            ValidationError: Innings completed or validation fails
        """
        # Validate innings
        result = await db.execute(
            select(Innings)
            .where(Innings.id == request.innings_id)
            .options(joinedload(Innings.match))
        )
        innings = result.scalar_one_or_none()
        
        if not innings:
            raise NotFoundError(f"Innings {request.innings_id} not found")
        
        if innings.is_completed:
            raise ValidationError("Cannot record ball for completed innings")
        
        # Validate over
        result = await db.execute(
            select(Over)
            .where(Over.id == request.over_id)
        )
        over = result.scalar_one_or_none()
        
        if not over:
            raise NotFoundError(f"Over {request.over_id} not found")
        
        if over.is_completed:
            raise ValidationError("Cannot add ball to completed over")
        
        # Validate wicket details if wicket
        if request.is_wicket and not request.wicket_details:
            raise ValidationError("wicket_details required when is_wicket=True")
        
        # Create Ball record (IMMUTABLE EVENT)
        ball = Ball(
            innings_id=request.innings_id,
            over_id=request.over_id,
            ball_number=request.ball_number,
            bowler_user_id=request.bowler_user_id,
            batsman_user_id=request.batsman_user_id,
            non_striker_user_id=request.non_striker_user_id,
            runs_scored=request.runs_scored,
            is_wicket=request.is_wicket,
            is_boundary=request.is_boundary,
            boundary_type=request.boundary_type,
            is_legal_delivery=request.is_legal_delivery,
            extra_type=request.extra_type,
            extra_runs=request.extra_runs,
            shot_type=request.shot_type,
            fielding_position=request.fielding_position,
            wagon_wheel_data=request.wagon_wheel_data,
            is_milestone=request.is_milestone,
            milestone_type=request.milestone_type,
            validation_source="dual_scorer",  # TODO: Get from context
            validation_confidence=1.00,
            bowled_at=datetime.utcnow()
        )
        
        db.add(ball)
        await db.flush()  # Get ball.id for wicket record
        
        # Create Wicket record if wicket fell
        wicket = None
        if request.is_wicket and request.wicket_details:
            wicket = await BallService._create_wicket(
                ball.id,
                request.innings_id,
                request.wicket_details,
                db
            )
        
        # Update innings aggregates
        await BallService._update_innings_aggregates(
            innings,
            request,
            db
        )
        
        # Update over aggregates
        await BallService._update_over_aggregates(
            over,
            request,
            db
        )
        
        # Check if over is complete (6 legal deliveries)
        if over.legal_deliveries >= 6:
            over.is_completed = True
            over.completed_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(ball)
        
        # Build enriched response
        ball_response = await BallService._build_ball_response(ball, wicket, db)
        
        # Broadcast WebSocket events to spectators
        if connection_manager:
            await BallService._broadcast_ball_events(
                innings,
                ball_response,
                over,
                connection_manager
            )
        
        return ball_response
    
    @staticmethod
    async def _create_wicket(
        ball_id: UUID,
        innings_id: UUID,
        wicket_details: WicketDetailsSchema,
        db: AsyncSession
    ) -> Wicket:
        """
        Create wicket record linked to ball
        
        Args:
            ball_id: Ball UUID
            innings_id: Innings UUID
            wicket_details: Wicket details from request
            db: Database session
            
        Returns:
            Created Wicket model
        """
        wicket = Wicket(
            ball_id=ball_id,
            innings_id=innings_id,
            batsman_out_user_id=wicket_details.batsman_out_user_id,
            dismissal_type=wicket_details.dismissal_type,
            bowler_user_id=wicket_details.bowler_user_id,
            fielder_user_id=wicket_details.fielder_user_id,
            fielder2_user_id=wicket_details.fielder2_user_id,
            wicket_number=wicket_details.wicket_number,
            team_score_at_wicket=wicket_details.team_score_at_wicket,
            partnership_runs=wicket_details.partnership_runs,
            dismissed_at=datetime.utcnow()
        )
        
        db.add(wicket)
        return wicket
    
    @staticmethod
    async def _update_innings_aggregates(
        innings: Innings,
        ball_request: BallCreateRequest,
        db: AsyncSession
    ) -> None:
        """
        Update innings aggregates after ball
        
        Updates:
        - total_runs (runs_scored + extra_runs)
        - wickets_fallen (if wicket)
        - extras (extra_runs)
        - current_ball_in_over
        - current_over_number (if over changed)
        
        Args:
            innings: Innings model
            ball_request: Ball request data
            db: Database session
        """
        # Add runs
        innings.total_runs += ball_request.runs_scored + ball_request.extra_runs
        
        # Add extras
        innings.extras += ball_request.extra_runs
        
        # Increment wickets if fell
        if ball_request.is_wicket:
            innings.wickets_fallen += 1
            
            # Check if all out (10 wickets)
            if innings.wickets_fallen >= 10:
                innings.all_out = True
                innings.is_completed = True
                innings.completed_at = datetime.utcnow()
        
        # Update ball/over position (if legal delivery)
        if ball_request.is_legal_delivery:
            innings.current_ball_in_over += 1
            
            # Check if over complete
            if innings.current_ball_in_over >= 6:
                innings.current_over_number += 1
                innings.current_ball_in_over = 0
    
    @staticmethod
    async def _update_over_aggregates(
        over: Over,
        ball_request: BallCreateRequest,
        db: AsyncSession
    ) -> None:
        """
        Update over aggregates after ball
        
        Updates:
        - runs_conceded
        - wickets_taken
        - legal_deliveries
        - extras_in_over
        - ball_sequence (JSONB array for UI)
        - is_maiden (if 0 runs in complete over)
        
        Args:
            over: Over model
            ball_request: Ball request data
            db: Database session
        """
        # Add runs conceded
        over.runs_conceded += ball_request.runs_scored + ball_request.extra_runs
        
        # Add wickets
        if ball_request.is_wicket:
            over.wickets_taken += 1
        
        # Increment legal deliveries
        if ball_request.is_legal_delivery:
            over.legal_deliveries += 1
        
        # Add extras
        over.extras_in_over += ball_request.extra_runs
        
        # Update ball sequence for UI
        ball_symbol = BallService._get_ball_symbol(ball_request)
        if over.ball_sequence is None:
            over.ball_sequence = []
        over.ball_sequence.append(ball_symbol)
        
        # Check maiden over (6 legal deliveries, 0 runs)
        if over.legal_deliveries == 6 and over.runs_conceded == 0:
            over.is_maiden = True
    
    @staticmethod
    def _get_ball_symbol(ball_request: BallCreateRequest) -> str:
        """
        Get ball symbol for UI display
        
        Returns:
        - "W" for wicket
        - "wd" for wide
        - "nb" for no-ball
        - "4" for four
        - "6" for six
        - Runs as string (e.g., "1", "2", "3")
        - "0" for dot ball
        
        Args:
            ball_request: Ball request data
            
        Returns:
            Symbol string for UI
        """
        if ball_request.is_wicket:
            return "W"
        
        if ball_request.extra_type.value == "wide":
            return "wd"
        elif ball_request.extra_type.value == "no_ball":
            return "nb"
        
        if ball_request.is_boundary:
            if ball_request.boundary_type.value == "six":
                return "6"
            elif ball_request.boundary_type.value == "four":
                return "4"
        
        return str(ball_request.runs_scored)
    
    @staticmethod
    async def _build_ball_response(
        ball: Ball,
        wicket: Optional[Wicket],
        db: AsyncSession
    ) -> BallResponse:
        """
        Build enriched BallResponse with player names
        
        Args:
            ball: Ball model
            wicket: Wicket model (if wicket fell)
            db: Database session
            
        Returns:
            BallResponse with enriched data
        """
        # Get player names
        bowler_name = await BallService._get_user_name(ball.bowler_user_id, db)
        batsman_name = await BallService._get_user_name(ball.batsman_user_id, db)
        non_striker_name = None
        if ball.non_striker_user_id:
            non_striker_name = await BallService._get_user_name(ball.non_striker_user_id, db)
        
        # Build wicket response if applicable
        wicket_response = None
        if wicket:
            wicket_response = await BallService._build_wicket_response(wicket, db)
        
        return BallResponse(
            id=ball.id,
            innings_id=ball.innings_id,
            over_id=ball.over_id,
            ball_number=ball.ball_number,
            bowler_user_id=ball.bowler_user_id,
            batsman_user_id=ball.batsman_user_id,
            non_striker_user_id=ball.non_striker_user_id,
            bowler_name=bowler_name,
            batsman_name=batsman_name,
            non_striker_name=non_striker_name,
            runs_scored=ball.runs_scored,
            is_wicket=ball.is_wicket,
            is_boundary=ball.is_boundary,
            boundary_type=ball.boundary_type,
            is_legal_delivery=ball.is_legal_delivery,
            extra_type=ball.extra_type,
            extra_runs=ball.extra_runs,
            shot_type=ball.shot_type,
            fielding_position=ball.fielding_position,
            wagon_wheel_data=ball.wagon_wheel_data,
            is_milestone=ball.is_milestone,
            milestone_type=ball.milestone_type,
            validation_source=ball.validation_source,
            validation_confidence=ball.validation_confidence,
            bowled_at=ball.bowled_at,
            created_at=ball.created_at,
            wicket=wicket_response
        )
    
    @staticmethod
    async def _build_wicket_response(
        wicket: Wicket,
        db: AsyncSession
    ) -> WicketResponse:
        """
        Build enriched WicketResponse with player names
        
        Args:
            wicket: Wicket model
            db: Database session
            
        Returns:
            WicketResponse with player names
        """
        # Get player names
        batsman_out_name = await BallService._get_user_name(wicket.batsman_out_user_id, db)
        bowler_name = None
        if wicket.bowler_user_id:
            bowler_name = await BallService._get_user_name(wicket.bowler_user_id, db)
        fielder_name = None
        if wicket.fielder_user_id:
            fielder_name = await BallService._get_user_name(wicket.fielder_user_id, db)
        fielder2_name = None
        if wicket.fielder2_user_id:
            fielder2_name = await BallService._get_user_name(wicket.fielder2_user_id, db)
        
        return WicketResponse(
            id=wicket.id,
            ball_id=wicket.ball_id,
            innings_id=wicket.innings_id,
            batsman_out_user_id=wicket.batsman_out_user_id,
            batsman_out_name=batsman_out_name,
            dismissal_type=wicket.dismissal_type,
            bowler_user_id=wicket.bowler_user_id,
            fielder_user_id=wicket.fielder_user_id,
            fielder2_user_id=wicket.fielder2_user_id,
            bowler_name=bowler_name,
            fielder_name=fielder_name,
            fielder2_name=fielder2_name,
            wicket_number=wicket.wicket_number,
            team_score_at_wicket=wicket.team_score_at_wicket,
            partnership_runs=wicket.partnership_runs,
            dismissed_at=wicket.dismissed_at,
            created_at=wicket.created_at
        )
    
    @staticmethod
    async def _get_user_name(user_id: UUID, db: AsyncSession) -> str:
        """
        Get user display name
        
        Args:
            user_id: User UUID
            db: Database session
            
        Returns:
            User name (email for now, TODO: use display_name)
        """
        result = await db.execute(
            select(UserAuth.email)
            .where(UserAuth.user_id == user_id)
        )
        return result.scalar_one_or_none() or "Unknown"
    
    @staticmethod
    async def get_ball(
        ball_id: UUID,
        db: AsyncSession
    ) -> BallResponse:
        """
        Get ball details by ID
        
        Args:
            ball_id: Ball UUID
            db: Database session
            
        Returns:
            BallResponse with ball details
            
        Raises:
            NotFoundError: Ball not found
        """
        result = await db.execute(
            select(Ball)
            .where(Ball.id == ball_id)
            .options(joinedload(Ball.wicket))
        )
        ball = result.scalar_one_or_none()
        
        if not ball:
            raise NotFoundError(f"Ball {ball_id} not found")
        
        return await BallService._build_ball_response(ball, ball.wicket, db)
    
    @staticmethod
    async def get_innings_balls(
        innings_id: UUID,
        db: AsyncSession,
        limit: Optional[int] = None
    ) -> list[BallResponse]:
        """
        Get all balls for an innings
        
        Used for:
        - Ball-by-ball replay
        - Match archives
        - Statistics calculation
        
        Args:
            innings_id: Innings UUID
            db: Database session
            limit: Optional limit on results
            
        Returns:
            List of BallResponse ordered by ball_number
        """
        query = (
            select(Ball)
            .where(Ball.innings_id == innings_id)
            .order_by(Ball.ball_number)
            .options(joinedload(Ball.wicket))
        )
        
        if limit:
            query = query.limit(limit)
        
        result = await db.execute(query)
        balls = result.scalars().all()
        
        responses = []
        for ball in balls:
            response = await BallService._build_ball_response(ball, ball.wicket, db)
            responses.append(response)
        
        return responses
    
    @staticmethod
    async def create_over(
        innings_id: UUID,
        over_number: int,
        bowler_user_id: UUID,
        db: AsyncSession
    ) -> Over:
        """
        Create a new over
        
        Called when:
        - Starting innings (over 1)
        - Previous over completed
        
        Args:
            innings_id: Innings UUID
            over_number: Over number (1-based)
            bowler_user_id: Bowler for this over
            db: Database session
            
        Returns:
            Created Over model
            
        Raises:
            ValidationError: Over already exists
        """
        # Check for duplicate
        result = await db.execute(
            select(Over)
            .where(
                and_(
                    Over.innings_id == innings_id,
                    Over.over_number == over_number
                )
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            raise ValidationError(
                f"Over {over_number} already exists for innings {innings_id}"
            )
        
        over = Over(
            innings_id=innings_id,
            over_number=over_number,
            bowler_user_id=bowler_user_id,
            started_at=datetime.utcnow()
        )
        
        db.add(over)
        await db.commit()
        await db.refresh(over)
        
        return over
    
    @staticmethod
    async def _broadcast_ball_events(
        innings: Innings,
        ball_response: BallResponse,
        over: Over,
        connection_manager: ConnectionManager
    ) -> None:
        """
        Broadcast WebSocket events for ball bowled.
        
        Events Broadcast:
        - BALL_BOWLED (always)
        - WICKET_FALLEN (if wicket)
        - OVER_COMPLETE (if over finished)
        
        Args:
            innings: Innings model
            ball_response: Enriched ball response
            over: Over model  
            connection_manager: WebSocket manager
        """
        match_id = str(innings.match_id)
        
        # 1. Broadcast BALL_BOWLED event
        ball_event = {
            "type": WebSocketEventType.BALL_BOWLED.value,
            "data": {
                "ball_id": str(ball_response.id),
                "innings_id": str(ball_response.innings_id),
                "over_number": ball_response.over_number,
                "ball_number": ball_response.ball_number,
                "bowler": {
                    "player_id": str(ball_response.bowler_user_id),
                    "player_name": "Bowler"  # TODO: Get from UserAuth join
                },
                "batsman": {
                    "player_id": str(ball_response.batsman_user_id),
                    "player_name": "Batsman"  # TODO: Get from UserAuth join
                },
                "runs_scored": ball_response.runs_scored,
                "is_boundary": ball_response.is_boundary,
                "boundary_type": ball_response.boundary_type.value if ball_response.boundary_type else None,
                "extras": {
                    "type": ball_response.extra_type.value if ball_response.extra_type else None,
                    "runs": ball_response.extra_runs
                } if ball_response.extra_runs > 0 else None,
                "is_wicket": ball_response.is_wicket,
                "innings_state": {
                    "score": f"{innings.total_runs}/{innings.wickets_fallen}",
                    "overs": float(innings.total_overs),
                    "run_rate": innings.run_rate,
                    "wickets": innings.wickets_fallen
                },
                "commentary": None  # TODO: Add commentary generation
            }
        }
        
        await connection_manager.broadcast_to_match(match_id, ball_event)
        
        # 2. Broadcast WICKET_FALLEN if wicket
        if ball_response.is_wicket and ball_response.wicket:
            wicket_event = {
                "type": WebSocketEventType.WICKET_FALLEN.value,
                "data": {
                    "ball_id": str(ball_response.id),
                    "wicket_id": str(ball_response.wicket.id),
                    "dismissal_type": ball_response.wicket.dismissal_type.value,
                    "batsman_out": {
                        "player_id": str(ball_response.wicket.batsman_out_user_id),
                        "player_name": "Batsman",  # TODO: Get from UserAuth
                        "runs": 0,  # TODO: Get from batting_innings aggregate
                        "balls": 0
                    },
                    "bowler": {
                        "player_id": str(ball_response.wicket.bowler_user_id) if ball_response.wicket.bowler_user_id else "",
                        "player_name": "Bowler"
                    },
                    "fielder": {
                        "player_id": str(ball_response.wicket.fielder_user_id),
                        "player_name": "Fielder"
                    } if ball_response.wicket.fielder_user_id else None,
                    "innings_state": {
                        "score": f"{innings.total_runs}/{innings.wickets_fallen}",
                        "overs": float(innings.total_overs),
                        "wickets": innings.wickets_fallen
                    },
                    "fall_of_wicket": f"{innings.total_runs}/{innings.wickets_fallen} ({innings.total_overs} overs)",
                    "commentary": None  # TODO: Generate wicket commentary
                }
            }
            
            await connection_manager.broadcast_to_match(match_id, wicket_event)
        
        # 3. Broadcast OVER_COMPLETE if over finished
        if over.is_completed:
            over_event = {
                "type": WebSocketEventType.OVER_COMPLETE.value,
                "data": {
                    "innings_id": str(innings.id),
                    "over_number": over.over_number,
                    "bowler": {
                        "player_id": str(over.bowler_user_id),
                        "player_name": "Bowler"  # TODO: Get from UserAuth
                    },
                    "runs_in_over": over.runs_conceded,
                    "wickets_in_over": over.wickets_taken,
                    "balls_summary": over.ball_sequence or [],
                    "innings_state": {
                        "score": f"{innings.total_runs}/{innings.wickets_fallen}",
                        "overs": float(innings.total_overs),
                        "run_rate": innings.run_rate
                    },
                    "next_bowler": None  # TODO: Get next bowler if available
                }
            }
            
            await connection_manager.broadcast_to_match(match_id, over_event)
