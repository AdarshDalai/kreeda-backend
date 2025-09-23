import logging
import secrets
import uuid
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.middleware import get_current_active_user
from app.auth.permissions import require_team_permission
from app.models.user import Team, TeamInvitation, TeamMember, User
from app.schemas.team import (
    TeamCreate, 
    TeamInvitationCreate, 
    TeamInvitationResponse,
    TeamJoinRequest,
    TeamMemberResponse, 
    TeamSimpleResponse,
    TeamUpdate
)
from app.utils.database import get_db
from app.utils.error_handler import (
    APIError, 
    AlreadyExistsError, 
    InternalServerError,
    PermissionDeniedError,
    TeamNotFoundError,
    ValidationError
)


logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
async def teams_health():
    return {"success": True, "message": "Teams service healthy"}


@router.post("/", response_model=TeamSimpleResponse)
async def create_team(
    team_data: TeamCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new cricket team"""
    try:
        # Check for duplicate team name
        existing_team = await db.execute(
            select(Team).where(
                Team.name == team_data.name,
                Team.is_active == True
            )
        )
        if existing_team.scalar_one_or_none():
            raise AlreadyExistsError("team name", team_data.name)
        
        # Create new team
        new_team = Team(
            name=team_data.name,
            short_name=team_data.short_name,
            logo_url=team_data.logo_url,
            created_by_id=current_user.id,
            captain_id=current_user.id,  # Creator is captain by default
        )

        db.add(new_team)
        await db.commit()
        await db.refresh(new_team)

        # Add creator as team member
        team_member = TeamMember(
            team_id=new_team.id,
            user_id=current_user.id,
            role="captain",
            joined_at=new_team.created_at,
        )

        db.add(team_member)
        await db.commit()

        logger.info(f"Team created: {new_team.name} by {current_user.username}")
        return new_team

    except APIError:
        # Let APIErrors (including AlreadyExistsError) bubble up
        await db.rollback()
        raise
    except Exception as e:
        logger.error(f"Failed to create team: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create team",
        )


@router.get("/", response_model=List[TeamSimpleResponse])
async def get_user_teams(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get all teams for current user"""
    try:
        # Get teams where user is a member with optimized query
        result = await db.execute(
            select(Team)
            .join(TeamMember)
            .where(TeamMember.user_id == current_user.id)
            .where(Team.is_active == True)
            .order_by(Team.created_at.desc())
        )
        teams = result.scalars().all()

        return teams

    except Exception as e:
        logger.error(f"Failed to get user teams: {e}")
        raise InternalServerError("retrieve teams")


@router.get("/{team_id}", response_model=TeamSimpleResponse)
async def get_team(
    team_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get specific team details"""
    try:
        # Check permission and get team
        team = await require_team_permission(current_user, str(team_id), "view", db)
        return team

    except APIError:
        raise
    except Exception as e:
        logger.error(f"Failed to get team: {e}")
        raise InternalServerError("retrieve team")


@router.put("/{team_id}", response_model=TeamSimpleResponse)
async def update_team(
    team_id: uuid.UUID,
    team_data: TeamUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update team details (only captain can update)"""
    try:
        # Check permission and get team
        team = await require_team_permission(current_user, str(team_id), "manage", db)
        
        # Build update values - only include non-None values
        update_values = {}
        if team_data.name is not None:
            update_values["name"] = team_data.name
        if team_data.short_name is not None:
            update_values["short_name"] = team_data.short_name
        if team_data.logo_url is not None:
            update_values["logo_url"] = team_data.logo_url
        if team_data.captain_id is not None:
            update_values["captain_id"] = team_data.captain_id
        
        # Only update if there are changes
        if update_values:
            await db.execute(
                update(Team)
                .where(Team.id == team_id)
                .values(**update_values)
            )
        
        await db.commit()
        await db.refresh(team)
        
        logger.info(f"Team updated: {team.name} by {current_user.username}")
        return team

    except APIError:
        raise
    except Exception as e:
        logger.error(f"Failed to update team: {e}")
        await db.rollback()
        raise InternalServerError("update team")


@router.get("/{team_id}/members", response_model=List[TeamMemberResponse])
async def get_team_members(
    team_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get all members of a team"""
    try:
        # Check permission using helper
        await require_team_permission(current_user, str(team_id), "view", db)

        # Get all team members with eager loading to avoid N+1 queries
        result = await db.execute(
            select(TeamMember)
            .options(selectinload(TeamMember.user))
            .where(TeamMember.team_id == team_id)
            .order_by(TeamMember.joined_at)
        )
        members = result.scalars().all()

        return members

    except APIError:
        raise
    except Exception as e:
        logger.error(f"Failed to get team members: {e}")
        raise InternalServerError("retrieve team members")


@router.post("/{team_id}/join")
async def join_team(
    team_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Join an existing team (deprecated - use invitation system instead)"""
    try:
        # Check if team exists
        result = await db.execute(
            select(Team).where(Team.id == team_id).where(Team.is_active == True)
        )
        team = result.scalar_one_or_none()

        if not team:
            raise TeamNotFoundError(str(team_id))

        # Check if already a member
        result = await db.execute(
            select(TeamMember)
            .where(TeamMember.team_id == team_id)
            .where(TeamMember.user_id == current_user.id)
        )
        if result.scalar_one_or_none():
            raise AlreadyExistsError("team membership")

        # Add as team member
        team_member = TeamMember(
            team_id=team_id, user_id=current_user.id, role="player"
        )

        db.add(team_member)
        await db.commit()

        logger.info(f"User {current_user.username} joined team {team.name}")
        return {"success": True, "message": "Successfully joined team"}

    except APIError:
        raise
    except Exception as e:
        logger.error(f"Failed to join team: {e}")
        await db.rollback()
        raise InternalServerError("join team")


@router.delete("/{team_id}")
async def delete_team(
    team_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a team (only captain can delete)"""
    try:
        # Check if user is captain of the team
        result = await db.execute(
            select(Team)
            .where(Team.id == team_id)
            .where(Team.captain_id == current_user.id)
            .where(Team.is_active == True)
        )
        team = result.scalar_one_or_none()

        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found or you're not the captain",
            )

        # Soft delete the team
        await db.execute(update(Team).where(Team.id == team_id).values(is_active=False))
        await db.commit()

        logger.info(f"Team {team.name} deleted by {current_user.username}")
        return {"message": "Team deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete team: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete team",
        )


# Team Invitation Endpoints
@router.post("/{team_id}/invite")
async def invite_to_team(
    team_id: uuid.UUID,
    invitation_data: TeamInvitationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Invite users to join team (only captain can invite)"""
    try:
        # Check permission using helper
        team = await require_team_permission(current_user, str(team_id), "manage", db)
        
        # Check if user already invited or is member
        existing_invite = await db.execute(
            select(TeamInvitation)
            .where(TeamInvitation.team_id == team_id)
            .where(TeamInvitation.email == invitation_data.email)
            .where(TeamInvitation.status == "pending")
        )
        
        if existing_invite.scalar_one_or_none():
            raise AlreadyExistsError("pending invitation", invitation_data.email)
        
        # Check if user is already a member
        existing_member = await db.execute(
            select(User)
            .join(TeamMember)
            .where(User.email == invitation_data.email)
            .where(TeamMember.team_id == team_id)
        )
        
        if existing_member.scalar_one_or_none():
            raise AlreadyExistsError("team membership", invitation_data.email)
        
        # Generate secure token
        invitation_token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(days=7)
        
        # Create invitation
        invitation = TeamInvitation(
            team_id=team_id,
            invited_by_id=current_user.id,
            email=invitation_data.email,
            phone=invitation_data.phone,
            message=invitation_data.message,
            token=invitation_token,
            expires_at=expires_at
        )
        
        db.add(invitation)
        await db.commit()
        await db.refresh(invitation)
        
        # TODO: Send email/SMS notification 
        # await notification_service.send_team_invitation(invitation)
        
        logger.info(f"Team invitation sent: {team.name} -> {invitation_data.email}")
        
        return {
            "success": True,
            "message": "Invitation sent successfully",
            "invitation_id": invitation.id,
            "expires_at": expires_at,
            "invitation_token": invitation_token  # For testing purposes
        }
        
    except APIError:
        raise
    except Exception as e:
        logger.error(f"Failed to send invitation: {e}")
        await db.rollback()
        raise InternalServerError("send invitation")


@router.get("/{team_id}/invitations", response_model=List[TeamInvitationResponse])
async def get_team_invitations(
    team_id: uuid.UUID,
    status_filter: Optional[str] = Query(None, alias="status", pattern="^(pending|accepted|rejected|expired)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get team invitations (only captain can view)"""
    try:
        # Check permission
        await require_team_permission(current_user, str(team_id), "manage", db)
        
        # Build query
        query = select(TeamInvitation).where(TeamInvitation.team_id == team_id)
        if status_filter:
            query = query.where(TeamInvitation.status == status_filter)
        
        query = query.order_by(TeamInvitation.created_at.desc())
        
        result = await db.execute(query.options(selectinload(TeamInvitation.invited_by)))
        invitations = result.scalars().all()
        
        return invitations
        
    except APIError:
        raise
    except Exception as e:
        logger.error(f"Failed to get invitations: {e}")
        raise InternalServerError("retrieve invitations")


@router.post("/join/{invitation_token}")
async def accept_invitation(
    invitation_token: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Accept team invitation using token"""
    try:
        # Find invitation
        result = await db.execute(
            select(TeamInvitation)
            .where(TeamInvitation.token == invitation_token)
            .where(TeamInvitation.status == "pending")
            .where(TeamInvitation.expires_at > datetime.utcnow())
            .options(selectinload(TeamInvitation.team))
        )
        invitation = result.scalar_one_or_none()
        
        if not invitation:
            raise ValidationError("invitation_token", "Invitation not found or expired")
        
        # Verify email matches (optional security check)
        if str(invitation.email) != str(current_user.email):
            raise PermissionDeniedError("accept this invitation - email mismatch")
        
        # Check if already member
        existing_member = await db.execute(
            select(TeamMember)
            .where(TeamMember.team_id == invitation.team_id)
            .where(TeamMember.user_id == current_user.id)
        )
        
        if existing_member.scalar_one_or_none():
            raise AlreadyExistsError("team membership")
        
        # Add as team member
        team_member = TeamMember(
            team_id=invitation.team_id,
            user_id=current_user.id,
            role="player"
        )
        
        # Update invitation status using update query
        await db.execute(
            update(TeamInvitation)
            .where(TeamInvitation.id == invitation.id)
            .values(
                status="accepted",
                updated_at=datetime.utcnow()
            )
        )
        
        db.add(team_member)
        await db.commit()
        
        logger.info(f"User {current_user.username} joined team {invitation.team.name}")
        
        return {
            "success": True,
            "message": f"Successfully joined {invitation.team.name}",
            "team": {
                "id": invitation.team.id,
                "name": invitation.team.name,
                "short_name": invitation.team.short_name
            }
        }
        
    except APIError:
        raise
    except Exception as e:
        logger.error(f"Failed to accept invitation: {e}")
        await db.rollback()
        raise InternalServerError("join team")


# Alternative invitation endpoints for test compatibility
@router.post("/{team_id}/invitations")
async def invite_to_team_alt(
    team_id: uuid.UUID,
    invitation_data: TeamInvitationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Alternative endpoint for team invitations (compatibility)"""
    return await invite_to_team(team_id, invitation_data, db, current_user)


@router.get("/invitations/received", response_model=List[TeamInvitationResponse])
async def get_user_invitations(
    status_filter: Optional[str] = Query(None, alias="status", pattern="^(pending|accepted|rejected|expired)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get invitations received by current user"""
    try:
        # Build query
        query = select(TeamInvitation).where(TeamInvitation.email == current_user.email)
        if status_filter:
            query = query.where(TeamInvitation.status == status_filter)
        
        query = query.order_by(TeamInvitation.created_at.desc())
        
        result = await db.execute(query.options(
            selectinload(TeamInvitation.team),
            selectinload(TeamInvitation.invited_by)
        ))
        invitations = result.scalars().all()
        
        return invitations
        
    except Exception as e:
        logger.error(f"Failed to get user invitations: {e}")
        raise InternalServerError("retrieve user invitations")


@router.get("/discover", response_model=List[TeamSimpleResponse])
async def discover_teams(
    search: Optional[str] = Query(None, min_length=2, max_length=50),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Discover public teams to join"""
    try:
        query = select(Team).where(Team.is_active == True)
        
        # Search filter
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                Team.name.ilike(search_pattern) | 
                Team.short_name.ilike(search_pattern)
            )
        
        # Exclude teams user is already member of
        user_teams_subquery = select(TeamMember.team_id).where(
            TeamMember.user_id == current_user.id
        )
        
        # Execute subquery to get actual team IDs
        user_teams_result = await db.execute(user_teams_subquery)
        user_team_ids = [row[0] for row in user_teams_result.fetchall()]
        
        if user_team_ids:
            query = query.where(~Team.id.in_(user_team_ids))
        
        # Order and paginate
        query = query.order_by(Team.created_at.desc()).offset(offset).limit(limit)
        
        result = await db.execute(query)
        teams = result.scalars().all()
        
        return teams
        
    except Exception as e:
        logger.error(f"Failed to discover teams: {e}")
        raise InternalServerError("discover teams")


@router.post("/{team_id}/join-request")
async def request_to_join_team(
    team_id: uuid.UUID,
    request_data: TeamJoinRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Send join request to team captain"""
    try:
        # Check team exists
        result = await db.execute(
            select(Team).where(Team.id == team_id).where(Team.is_active == True)
        )
        team = result.scalar_one_or_none()
        
        if not team:
            raise TeamNotFoundError(str(team_id))
        
        # Check not already member
        existing_member = await db.execute(
            select(TeamMember)
            .where(TeamMember.team_id == team_id)
            .where(TeamMember.user_id == current_user.id)
        )
        
        if existing_member.scalar_one_or_none():
            raise AlreadyExistsError("team membership")
        
        # For now, auto-accept join requests (can be enhanced later with approval system)
        team_member = TeamMember(
            team_id=team_id,
            user_id=current_user.id,
            role="player"
        )
        
        db.add(team_member)
        await db.commit()
        
        logger.info(f"User {current_user.username} joined team {team.name}")
        
        return {
            "success": True,
            "message": f"Successfully joined {team.name}"
        }
        
    except APIError:
        raise
    except Exception as e:
        logger.error(f"Failed join request: {e}")
        await db.rollback()
        raise InternalServerError("process join request")
