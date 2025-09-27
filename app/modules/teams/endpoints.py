"""
Team Management API Endpoints

API routes for team management operations
"""

import math
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.modules.teams.models import TeamType, TeamStatus, MemberRole, MemberStatus
from app.modules.teams.schemas import (
    Team as TeamSchema, TeamCreate, TeamUpdate, TeamSummary, TeamListResponse,
    TeamWithMembers, TeamMember as TeamMemberSchema, TeamMemberCreate, 
    TeamMemberUpdate, TeamMemberListResponse, TeamInvitation as TeamInvitationSchema,
    TeamInvitationCreate, TeamInvitationListResponse
)
from app.modules.teams.service import TeamService

router = APIRouter(prefix="/teams", tags=["teams"])


# Team CRUD endpoints
@router.post("", response_model=TeamSchema, status_code=status.HTTP_201_CREATED)
async def create_team(
    team_data: TeamCreate,
    creator_id: str = Query(..., description="ID of the user creating the team"),
    db: AsyncSession = Depends(get_db_session)
):
    """Create a new team"""
    
    # Check if team name already exists for this sport type
    existing_team = await TeamService.get_team_by_name(db, team_data.name, TeamType(team_data.team_type))
    if existing_team:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Team '{team_data.name}' already exists for {team_data.team_type}"
        )
    
    team = await TeamService.create_team(db, team_data, creator_id)
    return team


@router.get("", response_model=TeamListResponse)
async def list_teams(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    team_type: Optional[TeamType] = Query(None),
    status: Optional[TeamStatus] = Query(None),
    city: Optional[str] = Query(None),
    is_public: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db_session)
):
    """List teams with filtering and pagination"""
    
    teams, total = await TeamService.list_teams(
        db, page, per_page, search, team_type, status, city, is_public
    )
    
    return {
        "items": teams,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": math.ceil(total / per_page) if total > 0 else 1
    }


@router.get("/{team_id}", response_model=TeamWithMembers)
async def get_team(
    team_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Get a specific team by ID"""
    
    team = await TeamService.get_team_by_id(db, team_id)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    return team


@router.put("/{team_id}", response_model=TeamSchema)
async def update_team(
    team_id: str,
    team_data: TeamUpdate,
    db: AsyncSession = Depends(get_db_session)
):
    """Update team information"""
    
    team = await TeamService.update_team(db, team_id, team_data)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    return team


@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_team(
    team_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Delete a team (soft delete)"""
    
    success = await TeamService.delete_team(db, team_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )


# Team Member Management
@router.post("/{team_id}/members", response_model=TeamMemberSchema, status_code=status.HTTP_201_CREATED)
async def add_team_member(
    team_id: str,
    member_data: TeamMemberCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """Add a member to team"""
    
    member = await TeamService.add_team_member(db, team_id, member_data)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot add member (team not found, user not found, already a member, or team is full)"
        )
    
    return member


@router.get("/{team_id}/members", response_model=TeamMemberListResponse)
async def get_team_members(
    team_id: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    role: Optional[MemberRole] = Query(None),
    status: Optional[MemberStatus] = Query(None),
    db: AsyncSession = Depends(get_db_session)
):
    """Get team members with filtering"""
    
    members, total = await TeamService.get_team_members(
        db, team_id, page, per_page, role, status
    )
    
    return {
        "items": members,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": math.ceil(total / per_page) if total > 0 else 1
    }


@router.put("/{team_id}/members/{member_id}", response_model=TeamMemberSchema)
async def update_team_member(
    team_id: str,
    member_id: str,
    member_data: TeamMemberUpdate,
    db: AsyncSession = Depends(get_db_session)
):
    """Update team member"""
    
    member = await TeamService.update_team_member(db, team_id, member_id, member_data)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team member not found"
        )
    
    return member


@router.delete("/{team_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_team_member(
    team_id: str,
    member_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Remove member from team"""
    
    success = await TeamService.remove_team_member(db, team_id, member_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team member not found"
        )


# Team Invitation Management
@router.post("/{team_id}/invitations", response_model=TeamInvitationSchema, status_code=status.HTTP_201_CREATED)
async def create_team_invitation(
    team_id: str,
    invitation_data: TeamInvitationCreate,
    invited_by_id: str = Query(..., description="ID of the user sending the invitation"),
    db: AsyncSession = Depends(get_db_session)
):
    """Create team invitation"""
    
    invitation = await TeamService.create_invitation(db, team_id, invitation_data, invited_by_id)
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create invitation (team not found)"
        )
    
    return invitation


@router.get("/{team_id}/invitations", response_model=TeamInvitationListResponse)
async def get_team_invitations(
    team_id: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, regex="^(pending|accepted|declined|expired)$"),
    db: AsyncSession = Depends(get_db_session)
):
    """Get team invitations"""
    
    invitations, total = await TeamService.get_team_invitations(
        db, team_id, page, per_page, status
    )
    
    return {
        "items": invitations,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": math.ceil(total / per_page) if total > 0 else 1
    }


@router.put("/invitations/{invitation_id}/respond")
async def respond_to_invitation(
    invitation_id: str,
    accept: bool = Query(..., description="True to accept, False to decline"),
    user_id: str = Query(..., description="ID of the user responding"),
    db: AsyncSession = Depends(get_db_session)
):
    """Respond to team invitation"""
    
    invitation = await TeamService.respond_to_invitation(db, invitation_id, accept, user_id)
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot respond to invitation (not found, not for this user, or expired)"
        )
    
    return {
        "message": f"Invitation {'accepted' if accept else 'declined'} successfully",
        "invitation": invitation
    }


# Utility endpoints
@router.get("/search/available-names")
async def check_team_name_availability(
    name: str = Query(..., min_length=2),
    team_type: TeamType = Query(...),
    db: AsyncSession = Depends(get_db_session)
):
    """Check if team name is available for a sport type"""
    
    existing = await TeamService.get_team_by_name(db, name, team_type)
    return {"available": existing is None}