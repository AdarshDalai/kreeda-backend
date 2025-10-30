"""
Cricket Team Service Layer
Business logic for teams and team memberships

Follows SOLID principles:
- Single Responsibility: Each method handles one specific operation
- Open/Closed: Extensible for new features without modification
- Dependency Inversion: Depends on abstractions (AsyncSession interface)

Key workflows:
1. Team creation: User creates team → becomes creator and admin
2. Add members: Admins invite users → create memberships
3. Team discovery: Search teams, view roster, member history
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import joinedload

from src.models.cricket.team import Team, TeamMembership
from src.models.cricket.player_profile import CricketPlayerProfile
from src.models.sport_profile import SportProfile
from src.models.user_auth import UserAuth
from src.models.user_profile import UserProfile
from src.models.enums import (
    SportType, TeamType, TeamMemberRole,
    MembershipStatus
)
from src.schemas.cricket.team import (
    TeamCreateRequest, TeamUpdateRequest,
    TeamMembershipCreateRequest, TeamMembershipUpdateRequest,
    TeamResponse, TeamDetailResponse, TeamListResponse,
    TeamMembershipResponse
)
from src.core.exceptions import (
    NotFoundError, ValidationError, ForbiddenError,
    ConflictError
)
from src.core.logging import logger


class TeamService:
    """
    Service class for team operations
    
    All methods are static to avoid state management
    Each method represents a single business operation
    """
    
    # ========================================================================
    # TEAM OPERATIONS
    # ========================================================================
    
    @staticmethod
    async def create_team(
        user_id: UUID,
        request: TeamCreateRequest,
        db: AsyncSession
    ) -> TeamResponse:
        """
        Create a new team
        
        Business Rules:
        - User becomes team creator and gets team_admin role automatically
        - short_name is auto-generated if not provided (first 3 chars uppercase)
        - Team is active by default
        
        Args:
            user_id: UUID of user creating the team
            request: Team creation data
            db: Database session
        
        Returns:
            TeamResponse: Created team data
        
        Raises:
            NotFoundError: If user doesn't exist
            ConflictError: If user already has profile for this sport
        
        Example:
            team = await TeamService.create_team(
                user_id=UUID("..."),
                request=TeamCreateRequest(name="Mumbai Indians", ...),
                db=db_session
            )
        """
        logger.info(
            f"Creating team",
            extra={"user_id": str(user_id), "team_name": request.name}
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
            
            # Check for duplicate team name (same sport)
            existing_result = await db.execute(
                select(Team).where(
                    and_(
                        Team.name == request.name,
                        Team.sport_type == request.sport_type
                    )
                )
            )
            existing_team = existing_result.scalar_one_or_none()
            if existing_team:
                raise ConflictError(
                    message=f"Team with name '{request.name}' already exists",
                    error_code="DUPLICATE_TEAM_NAME",
                    details={"team_name": request.name}
                )
            
            # Auto-generate short_name if not provided
            short_name = request.short_name
            if not short_name:
                # Take first 3 letters of each word, uppercase
                words = request.name.split()
                if len(words) == 1:
                    short_name = request.name[:3].upper()
                else:
                    short_name = ''.join([word[0].upper() for word in words[:3]])
            
            # Create team
            team = Team(
                name=request.name,
                short_name=short_name,
                sport_type=request.sport_type,
                team_type=request.team_type,
                created_by_user_id=user_id,
                logo_url=request.logo_url,
                team_colors=request.team_colors.model_dump() if request.team_colors else None,
                home_ground=request.home_ground.model_dump() if request.home_ground else None,
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(team)
            await db.flush()  # Get team ID
            
            # Get user's sport profile for this sport type (if exists)
            sport_profile_result = await db.execute(
                select(SportProfile).where(
                    and_(
                        SportProfile.user_id == user_id,
                        SportProfile.sport_type == request.sport_type
                    )
                )
            )
            sport_profile = sport_profile_result.scalar_one_or_none()
            
            # Auto-add creator as team admin
            creator_membership = TeamMembership(
                team_id=team.id,
                user_id=user_id,
                sport_profile_id=sport_profile.id if sport_profile else None,
                roles=[TeamMemberRole.TEAM_ADMIN.value],
                status=MembershipStatus.ACTIVE,
                joined_at=datetime.utcnow()
            )
            db.add(creator_membership)
            
            await db.commit()
            await db.refresh(team)
            
            logger.info(
                f"Team created successfully",
                extra={"team_id": str(team.id), "team_name": team.name}
            )
            
            # Get creator name for response
            user_profile_result = await db.execute(
                select(UserProfile).where(UserProfile.user_id == user_id)
            )
            user_profile = user_profile_result.scalar_one_or_none()
            creator_name = user_profile.display_name if user_profile else None
            
            return TeamResponse(
                id=team.id,
                name=team.name,
                short_name=team.short_name,
                sport_type=team.sport_type,
                team_type=team.team_type,
                created_by=team.created_by_user_id,
                logo_url=team.logo_url,
                team_colors=request.team_colors,
                home_ground=request.home_ground,
                is_active=team.is_active,
                created_at=team.created_at,
                updated_at=team.updated_at,
                member_count=1,  # Creator is first member
                creator_name=creator_name
            )
            
        except (NotFoundError, ConflictError):
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            logger.error(
                f"Failed to create team",
                extra={"user_id": str(user_id), "error": str(e)},
                exc_info=True
            )
            raise
    
    @staticmethod
    async def update_team(
        team_id: UUID,
        user_id: UUID,
        request: TeamUpdateRequest,
        db: AsyncSession
    ) -> TeamResponse:
        """
        Update team details
        
        Business Rules:
        - Only creator or team_admins can update
        - Cannot change sport_type or created_by
        
        Args:
            team_id: UUID of team to update
            user_id: UUID of user making update
            request: Update data (only provided fields updated)
            db: Database session
        
        Returns:
            TeamResponse: Updated team data
        
        Raises:
            NotFoundError: If team doesn't exist
            ForbiddenError: If user not authorized
        """
        logger.info(
            f"Updating team",
            extra={"team_id": str(team_id), "user_id": str(user_id)}
        )
        
        try:
            # Get team
            team_result = await db.execute(
                select(Team).where(Team.id == team_id)
            )
            team = team_result.scalar_one_or_none()
            if not team:
                raise NotFoundError(
                    message=f"Team not found",
                    error_code="TEAM_NOT_FOUND",
                    details={"team_id": str(team_id)}
                )
            
            # Check permissions (creator or team_admin)
            is_authorized = await TeamService._is_team_admin(team_id, user_id, db)
            if not is_authorized:
                raise ForbiddenError(
                    message="Only team creator or admins can update team",
                    error_code="TEAM_UPDATE_NOT_ALLOWED",
                    details={"team_id": str(team_id), "user_id": str(user_id)}
                )
            
            # Update fields (only if provided)
            if request.name is not None:
                team.name = request.name
            if request.short_name is not None:
                team.short_name = request.short_name
            if request.team_type is not None:
                team.team_type = request.team_type
            if request.logo_url is not None:
                team.logo_url = request.logo_url
            if request.team_colors is not None:
                team.team_colors = request.team_colors.model_dump()
            if request.home_ground is not None:
                team.home_ground = request.home_ground.model_dump()
            if request.is_active is not None:
                team.is_active = request.is_active
            
            team.updated_at = datetime.utcnow()
            
            await db.commit()
            await db.refresh(team)
            
            logger.info(
                f"Team updated successfully",
                extra={"team_id": str(team_id)}
            )
            
            # Get member count
            member_count_result = await db.execute(
                select(func.count(TeamMembership.id)).where(
                    and_(
                        TeamMembership.team_id == team_id,
                        TeamMembership.status == MembershipStatus.ACTIVE
                    )
                )
            )
            member_count = member_count_result.scalar() or 0
            
            # Build response using model_validate with from_attributes
            response_data = TeamResponse.model_validate(team)
            response_data.member_count = member_count
            return response_data
            
        except (NotFoundError, ForbiddenError):
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            logger.error(
                f"Failed to update team",
                extra={"team_id": str(team_id), "error": str(e)},
                exc_info=True
            )
            raise
    
    @staticmethod
    async def get_team(
        team_id: UUID,
        db: AsyncSession,
        include_members: bool = False
    ) -> TeamResponse | TeamDetailResponse:
        """
        Get team by ID
        
        Args:
            team_id: UUID of team
            db: Database session
            include_members: If True, return TeamDetailResponse with members
        
        Returns:
            TeamResponse or TeamDetailResponse
        
        Raises:
            NotFoundError: If team doesn't exist
        """
        logger.info(
            f"Fetching team",
            extra={"team_id": str(team_id), "include_members": include_members}
        )
        
        # Get team with creator relationship
        team_result = await db.execute(
            select(Team)
            .options(joinedload(Team.creator))
            .where(Team.id == team_id)
        )
        team = team_result.scalar_one_or_none()
        
        if not team:
            raise NotFoundError(
                message=f"Team not found",
                error_code="TEAM_NOT_FOUND",
                details={"team_id": str(team_id)}
            )
        
        # Get member count
        member_count_result = await db.execute(
            select(func.count(TeamMembership.id)).where(
                and_(
                    TeamMembership.team_id == team_id,
                    TeamMembership.status == MembershipStatus.ACTIVE
                )
            )
        )
        member_count = member_count_result.scalar() or 0
        
        # Get creator name
        creator_name = None
        if hasattr(team, 'creator') and team.creator:
            # Try to get display name from UserProfile
            user_profile_result = await db.execute(
                select(UserProfile).where(UserProfile.user_id == team.created_by)
            )
            user_profile = user_profile_result.scalar_one_or_none()
            creator_name = user_profile.display_name if user_profile else team.creator.email
        
        if include_members:
            # Get members with user details
            members_result = await db.execute(
                select(TeamMembership)
                .options(
                    joinedload(TeamMembership.user),
                    joinedload(TeamMembership.cricket_profile)
                )
                .where(TeamMembership.team_id == team_id)
                .order_by(TeamMembership.joined_at)
            )
            members = members_result.scalars().all()
            
            # Convert to response schemas
            member_responses = []
            for member in members:
                # Get user/profile names
                user_name = None
                cricket_profile_name = None
                
                if hasattr(member, 'user') and member.user:
                    user_profile_result = await db.execute(
                        select(UserProfile).where(UserProfile.user_id == member.user_id)
                    )
                    user_profile = user_profile_result.scalar_one_or_none()
                    user_name = user_profile.display_name if user_profile else member.user.email
                
                if hasattr(member, 'cricket_profile') and member.cricket_profile:
                    cricket_profile_name = member.cricket_profile.player_name
                
                member_responses.append(TeamMembershipResponse(
                    id=member.id,
                    team_id=member.team_id,
                    user_id=member.user_id,
                    sport_profile_id=member.sport_profile_id,
                    cricket_profile_id=member.cricket_profile_id,
                    roles=[TeamMemberRole(role) for role in member.roles],
                    jersey_number=member.jersey_number,
                    status=member.status,
                    joined_at=member.joined_at,
                    user_name=user_name,
                    cricket_profile_name=cricket_profile_name
                ))
            
            member_responses.append(TeamMembershipResponse.model_validate(member))
            
            # Build TeamDetailResponse with manual field setting
            response_data = TeamDetailResponse.model_validate(team, from_attributes=True)
            response_data.member_count = member_count
            response_data.creator_name = creator_name
            response_data.members = member_responses
            return response_data
        else:
            response_data = TeamResponse.model_validate(team, from_attributes=True)
            response_data.member_count = member_count
            response_data.creator_name = creator_name
            return response_data
    
    @staticmethod
    async def list_teams(
        db: AsyncSession,
        sport_type: Optional[SportType] = None,
        team_type: Optional[TeamType] = None,
        search: Optional[str] = None,
        is_active: bool = True,
        page: int = 1,
        page_size: int = 10
    ) -> TeamListResponse:
        """
        List teams with filtering and pagination
        
        Args:
            db: Database session
            sport_type: Filter by sport
            team_type: Filter by team organization level
            search: Search in name/short_name
            is_active: Filter by active status
            page: Page number (1-indexed)
            page_size: Items per page
        
        Returns:
            TeamListResponse: Paginated team list
        """
        logger.info(
            f"Listing teams",
            extra={
                "sport_type": sport_type.value if sport_type else None,
                "page": page,
                "page_size": page_size
            }
        )
        
        # Build filters
        filters = [Team.is_active == is_active]
        
        if sport_type:
            filters.append(Team.sport_type == sport_type)
        
        if team_type:
            filters.append(Team.team_type == team_type)
        
        if search:
            search_pattern = f"%{search}%"
            filters.append(
                or_(
                    Team.name.ilike(search_pattern),
                    Team.short_name.ilike(search_pattern)
                )
            )
        
        # Get total count
        count_result = await db.execute(
            select(func.count(Team.id)).where(and_(*filters))
        )
        total = count_result.scalar() or 0
        
        # Get paginated teams
        offset = (page - 1) * page_size
        teams_result = await db.execute(
            select(Team)
            .where(and_(*filters))
            .order_by(Team.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        teams = teams_result.scalars().all()
        
        # Build response with member counts
        team_responses = []
        for team in teams:
            # Get member count
            member_count_result = await db.execute(
                select(func.count(TeamMembership.id)).where(
                    and_(
                        TeamMembership.team_id == team.id,
                        TeamMembership.status == MembershipStatus.ACTIVE
                    )
                )
            )
            member_count = member_count_result.scalar() or 0
            
            response_data = TeamResponse.model_validate(team, from_attributes=True)
            response_data.member_count = member_count
            team_responses.append(response_data)
        
        return TeamListResponse(
            teams=team_responses,
            total=total,
            page=page,
            page_size=page_size
        )
    
    # ========================================================================
    # TEAM MEMBERSHIP OPERATIONS
    # ========================================================================
    
    @staticmethod
    async def add_member(
        team_id: UUID,
        admin_user_id: UUID,
        request: TeamMembershipCreateRequest,
        db: AsyncSession
    ) -> TeamMembershipResponse:
        """
        Add a member to team
        
        Business Rules:
        - Only team creator or team_admins can add members
        - User must not already be an active member
        - If cricket_profile_id not provided, will auto-link if user has one cricket profile
        
        Args:
            team_id: UUID of team
            admin_user_id: UUID of admin adding member
            request: Membership creation data
            db: Database session
        
        Returns:
            TeamMembershipResponse: Created membership
        
        Raises:
            NotFoundError: If team or user doesn't exist
            ForbiddenError: If not authorized
            ConflictError: If user already active member
        """
        logger.info(
            f"Adding member to team",
            extra={"team_id": str(team_id), "new_user_id": str(request.user_id)}
        )
        
        try:
            # Check team exists
            team_result = await db.execute(
                select(Team).where(Team.id == team_id)
            )
            team = team_result.scalar_one_or_none()
            if not team:
                raise NotFoundError(
                    message=f"Team not found",
                    error_code="TEAM_NOT_FOUND",
                    details={"team_id": str(team_id)}
                )
            
            # Check permissions
            is_authorized = await TeamService._is_team_admin(team_id, admin_user_id, db)
            if not is_authorized:
                raise ForbiddenError(
                    message="Only team admins can add members",
                    error_code="ADD_MEMBER_NOT_ALLOWED",
                    details={"team_id": str(team_id)}
                )
            
            # Check user exists
            user_result = await db.execute(
                select(UserAuth).where(UserAuth.user_id == request.user_id)
            )
            user = user_result.scalar_one_or_none()
            if not user:
                raise NotFoundError(
                    message=f"User not found",
                    error_code="USER_NOT_FOUND",
                    details={"user_id": str(request.user_id)}
                )
            
            # Check for existing active membership
            existing_result = await db.execute(
                select(TeamMembership).where(
                    and_(
                        TeamMembership.team_id == team_id,
                        TeamMembership.user_id == request.user_id,
                        TeamMembership.status == MembershipStatus.ACTIVE
                    )
                )
            )
            existing_membership = existing_result.scalar_one_or_none()
            if existing_membership:
                raise ConflictError(
                    message=f"User is already an active member of this team",
                    error_code="DUPLICATE_TEAM_MEMBER",
                    details={"team_id": str(team_id), "user_id": str(request.user_id)}
                )
            
            # Get sport profile for user (if exists)
            sport_profile_result = await db.execute(
                select(SportProfile).where(
                    and_(
                        SportProfile.user_id == request.user_id,
                        SportProfile.sport_type == team.sport_type
                    )
                )
            )
            sport_profile = sport_profile_result.scalar_one_or_none()
            
            # Get cricket profile (auto-link if only one exists)
            cricket_profile_id = request.cricket_profile_id
            if not cricket_profile_id and team.sport_type == SportType.CRICKET and sport_profile:
                cricket_profile_result = await db.execute(
                    select(CricketPlayerProfile).where(
                        CricketPlayerProfile.sport_profile_id == sport_profile.id
                    )
                )
                cricket_profile = cricket_profile_result.scalar_one_or_none()
                if cricket_profile:
                    cricket_profile_id = cricket_profile.id
            
            # Check jersey number uniqueness (if provided)
            if request.jersey_number is not None:
                jersey_result = await db.execute(
                    select(TeamMembership).where(
                        and_(
                            TeamMembership.team_id == team_id,
                            TeamMembership.jersey_number == request.jersey_number,
                            TeamMembership.status == MembershipStatus.ACTIVE
                        )
                    )
                )
                existing_jersey = jersey_result.scalar_one_or_none()
                if existing_jersey:
                    raise ValidationError(
                        message=f"Jersey number {request.jersey_number} already assigned",
                        error_code="DUPLICATE_JERSEY_NUMBER",
                        details={"jersey_number": request.jersey_number}
                    )
            
            # Create membership
            membership = TeamMembership(
                team_id=team_id,
                user_id=request.user_id,
                sport_profile_id=sport_profile.id if sport_profile else None,
                cricket_profile_id=cricket_profile_id,
                roles=[role.value for role in request.roles],
                jersey_number=request.jersey_number,
                status=MembershipStatus.ACTIVE,
                joined_at=datetime.utcnow()
            )
            
            db.add(membership)
            await db.commit()
            await db.refresh(membership)
            
            logger.info(
                f"Member added to team successfully",
                extra={"membership_id": str(membership.id)}
            )
            
            return TeamMembershipResponse.model_validate(membership)
            
        except (NotFoundError, ForbiddenError, ConflictError, ValidationError):
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            logger.error(
                f"Failed to add member to team",
                extra={"team_id": str(team_id), "error": str(e)},
                exc_info=True
            )
            raise
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    @staticmethod
    async def _is_team_admin(team_id: UUID, user_id: UUID, db: AsyncSession) -> bool:
        """
        Check if user is team creator or has team_admin role
        
        Args:
            team_id: UUID of team
            user_id: UUID of user
            db: Database session
        
        Returns:
            bool: True if user is admin
        """
        # Check if creator
        team_result = await db.execute(
            select(Team).where(Team.id == team_id)
        )
        team = team_result.scalar_one_or_none()
        if team and team.created_by == user_id:
            return True
        
        # Check if has team_admin role
        membership_result = await db.execute(
            select(TeamMembership).where(
                and_(
                    TeamMembership.team_id == team_id,
                    TeamMembership.user_id == user_id,
                    TeamMembership.status == MembershipStatus.ACTIVE
                )
            )
        )
        membership = membership_result.scalar_one_or_none()
        
        if membership and TeamMemberRole.TEAM_ADMIN.value in membership.roles:
            return True
        
        return False
