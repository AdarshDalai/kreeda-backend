"""
Authorization and permission checking utilities
"""
import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, Team, TeamMember
from app.models.cricket import CricketMatch

logger = logging.getLogger(__name__)


class MatchPermissions:
    """Permission checking for cricket matches"""
    
    @staticmethod
    async def can_view_match(user: User, match: CricketMatch, db: AsyncSession) -> bool:
        """Check if user can view match details"""
        try:
            # User can view if they're part of either team or match creator
            if str(match.created_by_id) == str(user.id):
                return True
                
            result = await db.execute(
                select(TeamMember).where(
                    TeamMember.user_id == user.id,
                    TeamMember.team_id.in_([match.team_a_id, match.team_b_id])
                )
            )
            return result.scalar_one_or_none() is not None
        except Exception as e:
            logger.error(f"Error checking match view permission: {e}")
            return False
    
    @staticmethod
    async def can_manage_match(user: User, match: CricketMatch, db: AsyncSession) -> bool:
        """Check if user can manage match (record toss, edit details, etc.)"""
        try:
            # Match creator can always manage
            if str(match.created_by_id) == str(user.id):
                return True
            
            # Team captains can manage
            team_a_result = await db.execute(
                select(Team).where(
                    Team.id == match.team_a_id,
                    Team.captain_id == user.id
                )
            )
            
            team_b_result = await db.execute(
                select(Team).where(
                    Team.id == match.team_b_id, 
                    Team.captain_id == user.id
                )
            )
            
            return (team_a_result.scalar_one_or_none() is not None or 
                   team_b_result.scalar_one_or_none() is not None)
        except Exception as e:
            logger.error(f"Error checking match manage permission: {e}")
            return False
    
    @staticmethod
    async def can_score_match(user: User, match: CricketMatch, db: AsyncSession) -> bool:
        """Check if user can score in match (more restrictive)"""
        try:
            # Match creator can score
            if str(match.created_by_id) == str(user.id):
                return True
            
            # Team captains can score
            return await MatchPermissions.can_manage_match(user, match, db)
        except Exception as e:
            logger.error(f"Error checking match scoring permission: {e}")
            return False


class TeamPermissions:
    """Permission checking for teams"""
    
    @staticmethod
    async def can_manage_team(user: User, team: Team, db: AsyncSession) -> bool:
        """Check if user can manage team (invite members, edit details, etc.)"""
        try:
            # Team captain or creator can manage
            return str(team.captain_id) == str(user.id) or str(team.created_by_id) == str(user.id)
        except Exception as e:
            logger.error(f"Error checking team manage permission: {e}")
            return False
    
    @staticmethod
    async def can_view_team(user: User, team: Team, db: AsyncSession) -> bool:
        """Check if user can view team details"""
        try:
            # Public teams can be viewed by anyone (for discovery)
            # Private teams only by members
            result = await db.execute(
                select(TeamMember).where(
                    TeamMember.team_id == team.id,
                    TeamMember.user_id == user.id
                )
            )
            return result.scalar_one_or_none() is not None
        except Exception as e:
            logger.error(f"Error checking team view permission: {e}")
            return False
    
    @staticmethod
    async def is_team_member(user: User, team_id: str, db: AsyncSession) -> bool:
        """Check if user is a member of the team"""
        try:
            result = await db.execute(
                select(TeamMember).where(
                    TeamMember.team_id == team_id,
                    TeamMember.user_id == user.id
                )
            )
            return result.scalar_one_or_none() is not None
        except Exception as e:
            logger.error(f"Error checking team membership: {e}")
            return False
    
    @staticmethod
    async def is_team_captain(user: User, team_id: str, db: AsyncSession) -> bool:
        """Check if user is captain of the team"""
        try:
            result = await db.execute(
                select(Team).where(
                    Team.id == team_id,
                    Team.captain_id == user.id
                )
            )
            return result.scalar_one_or_none() is not None
        except Exception as e:
            logger.error(f"Error checking team captain status: {e}")
            return False


async def require_team_permission(
    user: User, 
    team_id: str, 
    permission_type: str,
    db: AsyncSession
) -> Team:
    """
    Helper function to check team permissions and return team if allowed
    Raises PermissionDeniedError if not allowed
    """
    import uuid
    from app.utils.error_handler import TeamNotFoundError, PermissionDeniedError
    
    # Convert team_id to UUID for database query
    try:
        team_uuid = uuid.UUID(team_id)
    except ValueError:
        raise TeamNotFoundError(team_id)
    
    # Get team
    result = await db.execute(
        select(Team).where(Team.id == team_uuid, Team.is_active == True)
    )
    team = result.scalar_one_or_none()
    
    if not team:
        raise TeamNotFoundError(team_id)
    
    # Check permission based on type
    if permission_type == "manage":
        can_access = await TeamPermissions.can_manage_team(user, team, db)
    elif permission_type == "view":
        can_access = await TeamPermissions.can_view_team(user, team, db)
    else:
        can_access = False
    
    if not can_access:
        raise PermissionDeniedError(f"{permission_type} this team")
    
    return team


async def require_match_permission(
    user: User,
    match_id: str, 
    permission_type: str,
    db: AsyncSession
) -> CricketMatch:
    """
    Helper function to check match permissions and return match if allowed
    Raises PermissionDeniedError if not allowed
    """
    import uuid
    from app.utils.error_handler import MatchNotFoundError, PermissionDeniedError
    
    # Get match
    result = await db.execute(
        select(CricketMatch).where(CricketMatch.id == uuid.UUID(match_id))
    )
    match = result.scalar_one_or_none()
    
    if not match:
        raise MatchNotFoundError(match_id)
    
    # Check permission based on type
    if permission_type == "manage":
        can_access = await MatchPermissions.can_manage_match(user, match, db)
    elif permission_type == "view":
        can_access = await MatchPermissions.can_view_match(user, match, db)
    elif permission_type == "score":
        can_access = await MatchPermissions.can_score_match(user, match, db)
    else:
        can_access = False
    
    if not can_access:
        raise PermissionDeniedError(f"{permission_type} this match")
    
    return match