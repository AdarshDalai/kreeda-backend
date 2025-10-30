"""
Cricket Match Service Layer
Business logic for match creation, toss, playing XI, and match lifecycle

Follows SOLID principles:
- Single Responsibility: Each method handles one specific operation
- Open/Closed: Extensible for new match types without modification
- Dependency Inversion: Depends on abstractions (AsyncSession interface)

Key workflows:
1. Match creation: Validate teams → Set match_rules → Generate match_code → status=SCHEDULED
2. Conduct toss: Validate teams → Update toss details → status=LIVE (if XI set) or TOSS_PENDING
3. Set playing XI: Validate roster → Check team membership → Create playing_xi records
4. Start match: Validate prerequisites (toss, XI) → status=LIVE → actual_start_time

State transitions:
SCHEDULED → TOSS_PENDING → LIVE → INNINGS_BREAK → COMPLETED/ABANDONED
"""
import random
import string
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import joinedload

from src.models.cricket.match import Match, MatchOfficial, MatchPlayingXI
from src.models.cricket.team import Team, TeamMembership
from src.models.user_auth import UserAuth
from src.models.user_profile import UserProfile
from src.models.enums import (
    SportType, MatchType, MatchStatus, MatchVisibility,
    ElectedTo, OfficialRole, MembershipStatus
)
from src.schemas.cricket.match import (
    MatchCreateRequest, MatchUpdateRequest,
    TossRequest, PlayingXIRequest, PlayingXIPlayerRequest,
    MatchOfficialRequest,
    MatchResponse, MatchDetailResponse, MatchListResponse,
    MatchOfficialResponse, PlayingXIResponse
)
from src.core.exceptions import (
    NotFoundError, ValidationError, ForbiddenError,
    ConflictError, UnprocessableEntityError
)
from src.core.logging import logger


class MatchService:
    """
    Service class for match operations
    
    All methods are static to avoid state management
    Each method represents a single business operation
    """
    
    # ========================================================================
    # MATCH OPERATIONS
    # ========================================================================
    
    @staticmethod
    async def create_match(
        user_id: UUID,
        request: MatchCreateRequest,
        db: AsyncSession
    ) -> MatchResponse:
        """
        Create a new match
        
        Business Rules:
        - Both teams must exist and be active
        - Teams must be different (validated in schema)
        - Match code auto-generated (KRD-XXXX format)
        - match_rules defaults provided for standard formats
        - Creator becomes match creator
        
        Args:
            user_id: UUID of user creating the match
            request: Match creation data
            db: Database session
        
        Returns:
            MatchResponse: Created match data
        
        Raises:
            NotFoundError: If user or teams don't exist
            ValidationError: If teams inactive or invalid
        
        Example:
            match = await MatchService.create_match(
                user_id=UUID("..."),
                request=MatchCreateRequest(team_a_id=..., team_b_id=..., ...),
                db=db_session
            )
        """
        logger.info(
            f"Creating match",
            extra={
                "user_id": str(user_id),
                "team_a_id": str(request.team_a_id),
                "team_b_id": str(request.team_b_id)
            }
        )
        
        try:
            # Verify user exists
            user_result = await db.execute(
                select(UserAuth).where(UserAuth.user_id == user_id)
            )
            user = user_result.scalar_one_or_none()
            if not user:
                raise NotFoundError(
                    message=f"User not found",
                    error_code="USER_NOT_FOUND",
                    details={"user_id": str(user_id)}
                )
            
            # Verify team A exists and is active
            team_a_result = await db.execute(
                select(Team).where(Team.id == request.team_a_id)
            )
            team_a = team_a_result.scalar_one_or_none()
            if not team_a:
                raise NotFoundError(
                    message=f"Team A not found",
                    error_code="TEAM_NOT_FOUND",
                    details={"team_id": str(request.team_a_id)}
                )
            if not team_a.is_active:
                raise ValidationError(
                    message=f"Team A is not active",
                    error_code="TEAM_NOT_ACTIVE",
                    details={"team_id": str(request.team_a_id)}
                )
            
            # Verify team B exists and is active
            team_b_result = await db.execute(
                select(Team).where(Team.id == request.team_b_id)
            )
            team_b = team_b_result.scalar_one_or_none()
            if not team_b:
                raise NotFoundError(
                    message=f"Team B not found",
                    error_code="TEAM_NOT_FOUND",
                    details={"team_id": str(request.team_b_id)}
                )
            if not team_b.is_active:
                raise ValidationError(
                    message=f"Team B is not active",
                    error_code="TEAM_NOT_ACTIVE",
                    details={"team_id": str(request.team_b_id)}
                )
            
            # Apply default match_rules for standard formats
            if request.match_rules:
                match_rules_dict = request.match_rules.model_dump()
            else:
                default_rules = MatchService._get_default_match_rules(request.match_type)
                match_rules_dict = default_rules.model_dump()
            
            # Generate unique match code
            match_code = await MatchService._generate_match_code(db)
            
            # Create match
            match = Match(
                sport_type=SportType.CRICKET,
                match_type=request.match_type,
                match_category=request.match_category,
                match_rules=match_rules_dict,
                team_a_id=request.team_a_id,
                team_b_id=request.team_b_id,
                venue=request.venue.model_dump(),
                scheduled_start_time=request.scheduled_start_time,
                visibility=request.visibility,
                match_status=MatchStatus.SCHEDULED,
                match_code=match_code,
                tournament_id=request.tournament_id,
                round_name=request.round_name,
                created_by_user_id=user_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(match)
            await db.commit()
            await db.refresh(match)
            
            logger.info(
                f"Match created successfully",
                extra={"match_id": str(match.id), "match_code": match_code}
            )
            
            # Build response
            response_data = MatchResponse.model_validate(match, from_attributes=True)
            response_data.team_a_name = team_a.name
            response_data.team_b_name = team_b.name
            return response_data
            
        except (NotFoundError, ValidationError):
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            logger.error(
                f"Failed to create match",
                extra={"user_id": str(user_id), "error": str(e)},
                exc_info=True
            )
            raise
    
    @staticmethod
    async def conduct_toss(
        match_id: UUID,
        user_id: UUID,
        request: TossRequest,
        db: AsyncSession
    ) -> MatchResponse:
        """
        Conduct match toss
        
        Business Rules:
        - Match must be in SCHEDULED status
        - Only match creator can conduct toss
        - toss_won_by_team_id must be team_a_id or team_b_id
        - Updates match_status to LIVE (if playing XI set) or TOSS_PENDING
        
        Args:
            match_id: UUID of match
            user_id: UUID of user conducting toss
            request: Toss data
            db: Database session
        
        Returns:
            MatchResponse: Updated match data
        
        Raises:
            NotFoundError: If match doesn't exist
            ForbiddenError: If user not authorized
            ValidationError: If match state invalid or team ID wrong
        """
        logger.info(
            f"Conducting toss for match",
            extra={"match_id": str(match_id), "user_id": str(user_id)}
        )
        
        try:
            # Get match
            match_result = await db.execute(
                select(Match).where(Match.id == match_id)
            )
            match = match_result.scalar_one_or_none()
            if not match:
                raise NotFoundError(
                    message=f"Match not found",
                    error_code="MATCH_NOT_FOUND",
                    details={"match_id": str(match_id)}
                )
            
            # Check permissions (match creator only)
            if match.created_by_user_id != user_id:
                raise ForbiddenError(
                    message="Only match creator can conduct toss",
                    error_code="TOSS_NOT_ALLOWED",
                    details={"match_id": str(match_id)}
                )
            
            # Validate match status
            if match.match_status != MatchStatus.SCHEDULED:
                raise ValidationError(
                    message=f"Cannot conduct toss for match in {match.match_status.value} status",
                    error_code="INVALID_MATCH_STATUS",
                    details={"current_status": match.match_status.value}
                )
            
            # Validate toss winner is one of the teams
            if request.toss_won_by_team_id not in [match.team_a_id, match.team_b_id]:
                raise ValidationError(
                    message="Toss winner must be one of the match teams",
                    error_code="INVALID_TOSS_WINNER",
                    details={"toss_winner_id": str(request.toss_won_by_team_id)}
                )
            
            # Update toss details
            match.toss_won_by_team_id = request.toss_won_by_team_id
            match.elected_to = request.elected_to
            match.toss_completed_at = datetime.utcnow()
            
            # Check if playing XI is set for both teams
            playing_xi_count_result = await db.execute(
                select(func.count(MatchPlayingXI.id)).where(
                    MatchPlayingXI.match_id == match_id
                )
            )
            playing_xi_count = playing_xi_count_result.scalar() or 0
            
            # Update match status
            if playing_xi_count >= 2:  # Both teams have at least one player (minimum)
                match.match_status = MatchStatus.LIVE
            else:
                match.match_status = MatchStatus.TOSS_PENDING
            
            match.updated_at = datetime.utcnow()
            
            await db.commit()
            await db.refresh(match)
            
            logger.info(
                f"Toss conducted successfully",
                extra={
                    "match_id": str(match_id),
                    "new_status": match.match_status.value
                }
            )
            
            # Get team names
            team_a_result = await db.execute(
                select(Team).where(Team.id == match.team_a_id)
            )
            team_a = team_a_result.scalar_one()
            team_b_result = await db.execute(
                select(Team).where(Team.id == match.team_b_id)
            )
            team_b = team_b_result.scalar_one()
            
            response_data = MatchResponse.model_validate(match, from_attributes=True)
            response_data.team_a_name = team_a.name
            response_data.team_b_name = team_b.name
            return response_data
            
        except (NotFoundError, ForbiddenError, ValidationError):
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            logger.error(
                f"Failed to conduct toss",
                extra={"match_id": str(match_id), "error": str(e)},
                exc_info=True
            )
            raise
    
    @staticmethod
    async def set_playing_xi(
        match_id: UUID,
        user_id: UUID,
        request: PlayingXIRequest,
        db: AsyncSession
    ) -> List[PlayingXIResponse]:
        """
        Set playing XI for a team
        
        Business Rules:
        - Match must be SCHEDULED or TOSS_PENDING
        - User must be team creator or admin
        - Team must be one of the match teams
        - All players must be active team members
        - Player count must match match_rules.players_per_team
        - Cannot modify XI once match is LIVE
        
        Args:
            match_id: UUID of match
            user_id: UUID of user setting XI
            request: Playing XI data
            db: Database session
        
        Returns:
            List[PlayingXIResponse]: Playing XI records
        
        Raises:
            NotFoundError: If match or team doesn't exist
            ForbiddenError: If user not authorized
            ValidationError: If match state, roster, or player count invalid
        """
        logger.info(
            f"Setting playing XI for match",
            extra={
                "match_id": str(match_id),
                "team_id": str(request.team_id),
                "player_count": len(request.players)
            }
        )
        
        try:
            # Get match
            match_result = await db.execute(
                select(Match).where(Match.id == match_id)
            )
            match = match_result.scalar_one_or_none()
            if not match:
                raise NotFoundError(
                    message=f"Match not found",
                    error_code="MATCH_NOT_FOUND",
                    details={"match_id": str(match_id)}
                )
            
            # Validate match status
            if match.match_status not in [MatchStatus.SCHEDULED, MatchStatus.TOSS_PENDING]:
                raise ValidationError(
                    message=f"Cannot set playing XI for match in {match.match_status.value} status",
                    error_code="INVALID_MATCH_STATUS",
                    details={"current_status": match.match_status.value}
                )
            
            # Validate team is one of the match teams
            if request.team_id not in [match.team_a_id, match.team_b_id]:
                raise ValidationError(
                    message="Team is not part of this match",
                    error_code="INVALID_TEAM",
                    details={"team_id": str(request.team_id)}
                )
            
            # Check user authorization (team admin or match creator)
            from src.services.cricket.team import TeamService
            is_team_admin = await TeamService._is_team_admin(request.team_id, user_id, db)
            is_match_creator = match.created_by_user_id == user_id
            
            if not (is_team_admin or is_match_creator):
                raise ForbiddenError(
                    message="Only team admins or match creator can set playing XI",
                    error_code="SET_XI_NOT_ALLOWED",
                    details={"team_id": str(request.team_id)}
                )
            
            # Validate player count matches match_rules
            expected_players = match.match_rules.get("players_per_team", 11)
            if len(request.players) != expected_players:
                raise ValidationError(
                    message=f"Playing XI must have exactly {expected_players} players",
                    error_code="INVALID_PLAYER_COUNT",
                    details={
                        "expected": expected_players,
                        "provided": len(request.players)
                    }
                )
            
            # Validate all players are active team members
            for player_req in request.players:
                membership_result = await db.execute(
                    select(TeamMembership).where(
                        and_(
                            TeamMembership.team_id == request.team_id,
                            TeamMembership.user_id == player_req.user_id,
                            TeamMembership.status == MembershipStatus.ACTIVE
                        )
                    )
                )
                membership = membership_result.scalar_one_or_none()
                if not membership:
                    raise ValidationError(
                        message=f"Player is not an active member of the team",
                        error_code="PLAYER_NOT_TEAM_MEMBER",
                        details={"user_id": str(player_req.user_id)}
                    )
            
            # Delete existing playing XI for this team (if any)
            await db.execute(
                select(MatchPlayingXI).where(
                    and_(
                        MatchPlayingXI.match_id == match_id,
                        MatchPlayingXI.team_id == request.team_id
                    )
                )
            )
            existing_xi_result = await db.execute(
                select(MatchPlayingXI).where(
                    and_(
                        MatchPlayingXI.match_id == match_id,
                        MatchPlayingXI.team_id == request.team_id
                    )
                )
            )
            existing_xi = existing_xi_result.scalars().all()
            for xi in existing_xi:
                await db.delete(xi)
            
            # Create playing XI records
            playing_xi_records = []
            for player_req in request.players:
                # Get cricket profile if provided
                cricket_profile_id = player_req.cricket_profile_id
                if not cricket_profile_id:
                    # Auto-link cricket profile if user has one
                    membership_result = await db.execute(
                        select(TeamMembership).where(
                            and_(
                                TeamMembership.team_id == request.team_id,
                                TeamMembership.user_id == player_req.user_id
                            )
                        )
                    )
                    membership = membership_result.scalar_one_or_none()
                    if membership:
                        cricket_profile_id = membership.cricket_profile_id
                
                xi_record = MatchPlayingXI(
                    match_id=match_id,
                    team_id=request.team_id,
                    user_id=player_req.user_id,
                    cricket_profile_id=cricket_profile_id,
                    can_bat=player_req.can_bat,
                    can_bowl=player_req.can_bowl,
                    is_wicket_keeper=player_req.is_wicket_keeper,
                    is_captain=player_req.is_captain,
                    batting_position=player_req.batting_position,
                    bowling_preference=player_req.bowling_preference,
                    played=True,
                    created_at=datetime.utcnow()
                )
                db.add(xi_record)
                playing_xi_records.append(xi_record)
            
            await db.commit()
            
            # Refresh all records
            for record in playing_xi_records:
                await db.refresh(record)
            
            logger.info(
                f"Playing XI set successfully",
                extra={"match_id": str(match_id), "team_id": str(request.team_id)}
            )
            
            # Build response
            xi_responses = []
            for record in playing_xi_records:
                # Get player name
                user_profile_result = await db.execute(
                    select(UserProfile).where(UserProfile.user_id == record.user_id)
                )
                user_profile = user_profile_result.scalar_one_or_none()
                user_name = user_profile.display_name if user_profile else None
                
                response = PlayingXIResponse.model_validate(record, from_attributes=True)
                response.user_name = user_name
                xi_responses.append(response)
            
            return xi_responses
            
        except (NotFoundError, ForbiddenError, ValidationError):
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            logger.error(
                f"Failed to set playing XI",
                extra={"match_id": str(match_id), "error": str(e)},
                exc_info=True
            )
            raise
    
    @staticmethod
    async def get_match(
        match_id: UUID,
        db: AsyncSession,
        include_details: bool = False
    ) -> MatchResponse | MatchDetailResponse:
        """
        Get match by ID
        
        Args:
            match_id: UUID of match
            db: Database session
            include_details: If True, return MatchDetailResponse with officials and playing XI
        
        Returns:
            MatchResponse or MatchDetailResponse
        
        Raises:
            NotFoundError: If match doesn't exist
        """
        logger.info(
            f"Fetching match",
            extra={"match_id": str(match_id), "include_details": include_details}
        )
        
        # Get match with team relationships
        match_result = await db.execute(
            select(Match)
            .options(
                joinedload(Match.team_a),
                joinedload(Match.team_b)
            )
            .where(Match.id == match_id)
        )
        match = match_result.scalar_one_or_none()
        
        if not match:
            raise NotFoundError(
                message=f"Match not found",
                error_code="MATCH_NOT_FOUND",
                details={"match_id": str(match_id)}
            )
        
        # Get team names
        team_a_name = match.team_a.name if hasattr(match, 'team_a') and match.team_a else None
        team_b_name = match.team_b.name if hasattr(match, 'team_b') and match.team_b else None
        
        if include_details:
            # Get officials
            officials_result = await db.execute(
                select(MatchOfficial)
                .options(joinedload(MatchOfficial.user))
                .where(MatchOfficial.match_id == match_id)
            )
            officials = officials_result.scalars().all()
            
            official_responses = []
            for official in officials:
                user_profile_result = await db.execute(
                    select(UserProfile).where(UserProfile.user_id == official.user_id)
                )
                user_profile = user_profile_result.scalar_one_or_none()
                user_name = user_profile.display_name if user_profile else None
                
                response = MatchOfficialResponse.model_validate(official, from_attributes=True)
                response.user_name = user_name
                official_responses.append(response)
            
            # Get playing XI
            playing_xi_result = await db.execute(
                select(MatchPlayingXI)
                .where(MatchPlayingXI.match_id == match_id)
                .order_by(MatchPlayingXI.team_id, MatchPlayingXI.batting_position)
            )
            playing_xi = playing_xi_result.scalars().all()
            
            xi_responses = []
            for xi in playing_xi:
                user_profile_result = await db.execute(
                    select(UserProfile).where(UserProfile.user_id == xi.user_id)
                )
                user_profile = user_profile_result.scalar_one_or_none()
                user_name = user_profile.display_name if user_profile else None
                
                response = PlayingXIResponse.model_validate(xi, from_attributes=True)
                response.user_name = user_name
                xi_responses.append(response)
            
            # Build detailed response
            response_data = MatchDetailResponse.model_validate(match, from_attributes=True)
            response_data.team_a_name = team_a_name
            response_data.team_b_name = team_b_name
            response_data.officials = official_responses
            response_data.playing_xi = xi_responses
            return response_data
        else:
            response_data = MatchResponse.model_validate(match, from_attributes=True)
            response_data.team_a_name = team_a_name
            response_data.team_b_name = team_b_name
            return response_data
    
    @staticmethod
    async def list_matches(
        db: AsyncSession,
        sport_type: Optional[SportType] = None,
        match_type: Optional[MatchType] = None,
        match_status: Optional[MatchStatus] = None,
        team_id: Optional[UUID] = None,
        visibility: Optional[MatchVisibility] = None,
        page: int = 1,
        page_size: int = 10
    ) -> MatchListResponse:
        """
        List matches with filtering and pagination
        
        Args:
            db: Database session
            sport_type: Filter by sport
            match_type: Filter by format (T20, ODI, etc.)
            match_status: Filter by status
            team_id: Filter by team participation
            visibility: Filter by visibility
            page: Page number (1-indexed)
            page_size: Items per page
        
        Returns:
            MatchListResponse: Paginated match list
        """
        logger.info(
            f"Listing matches",
            extra={
                "sport_type": sport_type.value if sport_type else None,
                "page": page,
                "page_size": page_size
            }
        )
        
        # Build filters
        filters = []
        
        if sport_type:
            filters.append(Match.sport_type == sport_type)
        
        if match_type:
            filters.append(Match.match_type == match_type)
        
        if match_status:
            filters.append(Match.match_status == match_status)
        
        if team_id:
            filters.append(
                or_(
                    Match.team_a_id == team_id,
                    Match.team_b_id == team_id
                )
            )
        
        if visibility:
            filters.append(Match.visibility == visibility)
        
        # Get total count
        count_query = select(func.count(Match.id))
        if filters:
            count_query = count_query.where(and_(*filters))
        
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0
        
        # Get paginated matches
        offset = (page - 1) * page_size
        matches_query = select(Match).options(
            joinedload(Match.team_a),
            joinedload(Match.team_b)
        )
        if filters:
            matches_query = matches_query.where(and_(*filters))
        
        matches_query = matches_query.order_by(
            Match.scheduled_start_time.desc()
        ).offset(offset).limit(page_size)
        
        matches_result = await db.execute(matches_query)
        matches = matches_result.scalars().all()
        
        # Build response
        match_responses = []
        for match in matches:
            team_a_name = match.team_a.name if hasattr(match, 'team_a') and match.team_a else None
            team_b_name = match.team_b.name if hasattr(match, 'team_b') and match.team_b else None
            
            response_data = MatchResponse.model_validate(match, from_attributes=True)
            response_data.team_a_name = team_a_name
            response_data.team_b_name = team_b_name
            match_responses.append(response_data)
        
        return MatchListResponse(
            matches=match_responses,
            total=total,
            page=page,
            page_size=page_size
        )
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    @staticmethod
    async def _generate_match_code(db: AsyncSession) -> str:
        """
        Generate unique match code in format KRD-XXXX
        
        Args:
            db: Database session
        
        Returns:
            str: Unique match code
        """
        while True:
            # Generate random 4-character alphanumeric code
            code_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
            match_code = f"KRD-{code_suffix}"
            
            # Check uniqueness
            existing_result = await db.execute(
                select(Match).where(Match.match_code == match_code)
            )
            existing = existing_result.scalar_one_or_none()
            
            if not existing:
                return match_code
    
    @staticmethod
    def _get_default_match_rules(match_type: MatchType):
        """
        Get default match rules for standard formats
        
        Args:
            match_type: Match format
        
        Returns:
            MatchRulesSchema: Default match_rules configuration
        """
        from src.schemas.cricket.match import MatchRulesSchema
        
        if match_type == MatchType.T20:
            return MatchRulesSchema(
                players_per_team=11,
                overs_per_side=20,
                balls_per_over=6,
                wickets_to_fall=10,
                powerplay_overs=6,
                death_overs_start=16,
                super_over_if_tie=True
            )
        elif match_type == MatchType.ODI:
            return MatchRulesSchema(
                players_per_team=11,
                overs_per_side=50,
                balls_per_over=6,
                wickets_to_fall=10,
                powerplay_overs=10,
                dls_applicable=True
            )
        elif match_type == MatchType.THE_HUNDRED:
            return MatchRulesSchema(
                players_per_team=11,
                overs_per_side=20,  # 100 balls = ~16.67 overs
                balls_per_over=5,  # The Hundred uses 5-ball overs (with some 10-ball overs)
                wickets_to_fall=10,
                powerplay_overs=5
            )
        else:
            # Default/Custom
            return MatchRulesSchema(
                players_per_team=11,
                overs_per_side=20,
                balls_per_over=6,
                wickets_to_fall=10
            )
