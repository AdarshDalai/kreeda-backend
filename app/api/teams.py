from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import List, Optional
import logging
import uuid
from pydantic import BaseModel, ConfigDict
from datetime import datetime

from app.utils.database import get_db
from app.models.user import User, Team, TeamMember
from app.schemas.team import TeamCreate, TeamMemberResponse
from app.auth.middleware import get_current_active_user


# Simple response schema without relationships to avoid async issues
class TeamSimpleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    short_name: str
    logo_url: Optional[str] = None
    created_by_id: uuid.UUID
    captain_id: uuid.UUID
    created_at: datetime
    is_active: bool


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
        # Get teams where user is a member
        result = await db.execute(
            select(Team)
            .join(TeamMember)
            .where(TeamMember.user_id == current_user.id)
            .where(Team.is_active == True)
        )
        teams = result.scalars().all()

        return teams

    except Exception as e:
        logger.error(f"Failed to get user teams: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve teams",
        )


@router.get("/{team_id}", response_model=TeamSimpleResponse)
async def get_team(
    team_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get specific team details"""
    try:
        # Check if user is member of the team
        result = await db.execute(
            select(Team)
            .join(TeamMember)
            .where(Team.id == team_id)
            .where(TeamMember.user_id == current_user.id)
            .where(Team.is_active == True)
        )
        team = result.scalar_one_or_none()

        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found or access denied",
            )

        return team

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get team: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve team",
        )


@router.get("/{team_id}/members", response_model=List[TeamMemberResponse])
async def get_team_members(
    team_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get all members of a team"""
    try:
        # Check if user is member of the team
        result = await db.execute(
            select(TeamMember)
            .where(TeamMember.team_id == team_id)
            .where(TeamMember.user_id == current_user.id)
        )
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
            )

        # Get all team members
        result = await db.execute(
            select(TeamMember).join(User).where(TeamMember.team_id == team_id)
        )
        members = result.scalars().all()

        return members

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get team members: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve team members",
        )


@router.post("/{team_id}/join")
async def join_team(
    team_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Join an existing team"""
    try:
        # Check if team exists
        result = await db.execute(
            select(Team).where(Team.id == team_id).where(Team.is_active == True)
        )
        team = result.scalar_one_or_none()

        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Team not found"
            )

        # Check if already a member
        result = await db.execute(
            select(TeamMember)
            .where(TeamMember.team_id == team_id)
            .where(TeamMember.user_id == current_user.id)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Already a member of this team",
            )

        # Add as team member
        team_member = TeamMember(
            team_id=team_id, user_id=current_user.id, role="player"
        )

        db.add(team_member)
        await db.commit()

        logger.info(f"User {current_user.username} joined team {team.name}")
        return {"message": "Successfully joined team"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to join team: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to join team",
        )


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
