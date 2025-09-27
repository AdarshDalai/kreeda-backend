"""
Team Management Service

Business logic for team management operations
"""

import math
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from .models import Team, TeamMember, TeamInvitation, TeamType, TeamStatus, MemberRole, MemberStatus
from .schemas import TeamCreate, TeamUpdate, TeamMemberCreate, TeamMemberUpdate, TeamInvitationCreate
from ..users.models import User


class TeamService:
    """Service class for team management operations"""
    
    @staticmethod
    async def create_team(db: AsyncSession, team_data: TeamCreate, creator_id: str) -> Team:
        """Create a new team"""
        team = Team(**team_data.model_dump())
        
        db.add(team)
        await db.commit()
        await db.refresh(team)
        
        # Auto-add creator as captain
        member_data = TeamMemberCreate(
            user_id=creator_id,
            role=MemberRole.CAPTAIN,
            jersey_number=None,
            position=None
        )
        await TeamService.add_team_member(db, team.id, member_data, auto_approve=True)
        
        return team
    
    @staticmethod
    async def get_team_by_id(db: AsyncSession, team_id: str) -> Optional[Team]:
        """Get team by ID with members"""
        result = await db.execute(
            select(Team)
            .options(
                selectinload(Team.members).selectinload(TeamMember.user)
            )
            .where(Team.id == team_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_team_by_name(db: AsyncSession, name: str, team_type: TeamType) -> Optional[Team]:
        """Get team by name and type"""
        result = await db.execute(
            select(Team)
            .where(and_(Team.name == name, Team.team_type == team_type))
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def list_teams(
        db: AsyncSession,
        page: int = 1,
        per_page: int = 20,
        search: Optional[str] = None,
        team_type: Optional[TeamType] = None,
        status: Optional[TeamStatus] = None,
        city: Optional[str] = None,
        is_public: Optional[bool] = None
    ) -> Tuple[List[Team], int]:
        """List teams with filtering and pagination"""
        
        # Build base query
        query = select(Team)
        count_query = select(func.count(Team.id))
        
        # Apply filters
        conditions = []
        
        if search:
            search_filter = or_(
                Team.name.ilike(f"%{search}%"),
                Team.description.ilike(f"%{search}%"),
                Team.city.ilike(f"%{search}%")
            )
            conditions.append(search_filter)
        
        if team_type:
            conditions.append(Team.team_type == team_type)
        
        if status:
            conditions.append(Team.status == status)
        
        if city:
            conditions.append(Team.city.ilike(f"%{city}%"))
        
        if is_public is not None:
            conditions.append(Team.is_public == is_public)
        
        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))
        
        # Get total count
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Apply pagination and ordering
        query = (
            query
            .order_by(Team.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        
        # Execute query
        result = await db.execute(query)
        teams = list(result.scalars().all())
        
        return teams, total
    
    @staticmethod
    async def update_team(db: AsyncSession, team_id: str, team_data: TeamUpdate) -> Optional[Team]:
        """Update team information"""
        result = await db.execute(select(Team).where(Team.id == team_id))
        team = result.scalar_one_or_none()
        
        if not team:
            return None
        
        # Update fields
        update_data = team_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(team, field, value)
        
        await db.commit()
        await db.refresh(team)
        return team
    
    @staticmethod
    async def delete_team(db: AsyncSession, team_id: str) -> bool:
        """Delete team (soft delete by changing status)"""
        result = await db.execute(select(Team).where(Team.id == team_id))
        team = result.scalar_one_or_none()
        
        if not team:
            return False
        
        team.status = "disbanded"
        await db.commit()
        return True
    
    # Team Member Management
    @staticmethod
    async def add_team_member(
        db: AsyncSession, 
        team_id: str, 
        member_data: TeamMemberCreate,
        auto_approve: bool = False
    ) -> Optional[TeamMember]:
        """Add a member to team"""
        
        # Check if team exists
        team = await TeamService.get_team_by_id(db, team_id)
        if not team:
            return None
        
        # Check if user exists
        user_result = await db.execute(select(User).where(User.id == member_data.user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            return None
        
        # Check if already a member
        existing_result = await db.execute(
            select(TeamMember).where(
                and_(
                    TeamMember.team_id == team_id,
                    TeamMember.user_id == member_data.user_id,
                    TeamMember.status != "left"
                )
            )
        )
        if existing_result.scalar_one_or_none():
            return None  # Already a member
        
        # Check team capacity
        member_count_result = await db.execute(
            select(func.count(TeamMember.id)).where(
                and_(
                    TeamMember.team_id == team_id,
                    TeamMember.status == "active"
                )
            )
        )
        current_members = member_count_result.scalar() or 0
        
        if current_members >= team.max_members:
            return None  # Team is full
        
        # Create member
        member = TeamMember(
            team_id=team_id,
            user_id=member_data.user_id,
            role=member_data.role.value,
            jersey_number=member_data.jersey_number,
            position=member_data.position,
            permissions=member_data.permissions,
            notes=member_data.notes,
            stats=member_data.stats,
            status="active" if auto_approve else "pending",
            joined_date=datetime.utcnow()
        )
        
        db.add(member)
        await db.commit()
        await db.refresh(member)
        
        # Load user relationship
        await db.refresh(member, ["user"])
        
        return member
    
    @staticmethod
    async def get_team_members(
        db: AsyncSession,
        team_id: str,
        page: int = 1,
        per_page: int = 20,
        role: Optional[MemberRole] = None,
        status: Optional[MemberStatus] = None
    ) -> Tuple[List[TeamMember], int]:
        """Get team members with filtering"""
        
        query = (
            select(TeamMember)
            .options(selectinload(TeamMember.user))
            .where(TeamMember.team_id == team_id)
        )
        count_query = select(func.count(TeamMember.id)).where(TeamMember.team_id == team_id)
        
        # Apply filters
        conditions = [TeamMember.team_id == team_id]
        
        if role:
            conditions.append(TeamMember.role == role)
        
        if status:
            conditions.append(TeamMember.status == status)
        
        if len(conditions) > 1:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))
        
        # Get total count
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Apply pagination
        query = (
            query
            .order_by(TeamMember.joined_date.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        
        result = await db.execute(query)
        members = list(result.scalars().all())
        
        return members, total
    
    @staticmethod
    async def update_team_member(
        db: AsyncSession,
        team_id: str,
        member_id: str,
        member_data: TeamMemberUpdate
    ) -> Optional[TeamMember]:
        """Update team member"""
        result = await db.execute(
            select(TeamMember)
            .options(selectinload(TeamMember.user))
            .where(
                and_(
                    TeamMember.id == member_id,
                    TeamMember.team_id == team_id
                )
            )
        )
        member = result.scalar_one_or_none()
        
        if not member:
            return None
        
        # Update fields
        update_data = member_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None:
                setattr(member, field, value)
        
        await db.commit()
        await db.refresh(member)
        return member
    
    @staticmethod
    async def remove_team_member(db: AsyncSession, team_id: str, member_id: str) -> bool:
        """Remove member from team"""
        result = await db.execute(
            select(TeamMember).where(
                and_(
                    TeamMember.id == member_id,
                    TeamMember.team_id == team_id
                )
            )
        )
        member = result.scalar_one_or_none()
        
        if not member:
            return False
        
        member.status = "left"
        member.left_date = datetime.utcnow()
        
        await db.commit()
        return True
    
    # Team Invitation Management
    @staticmethod
    async def create_invitation(
        db: AsyncSession,
        team_id: str,
        invitation_data: TeamInvitationCreate,
        invited_by_id: str
    ) -> Optional[TeamInvitation]:
        """Create team invitation"""
        
        # Check if team exists
        team = await TeamService.get_team_by_id(db, team_id)
        if not team:
            return None
        
        # Create invitation
        invitation = TeamInvitation(
            team_id=team_id,
            invited_user_id=invitation_data.user_id if invitation_data.user_id else None,
            invited_by_id=invited_by_id,
            email=invitation_data.email,
            proposed_role=invitation_data.proposed_role.value,
            message=invitation_data.message,
            expires_at=datetime.utcnow() + timedelta(days=7)  # 7 days expiry
        )
        
        db.add(invitation)
        await db.commit()
        await db.refresh(invitation)
        
        return invitation
    
    @staticmethod
    async def get_team_invitations(
        db: AsyncSession,
        team_id: str,
        page: int = 1,
        per_page: int = 20,
        status: Optional[str] = None
    ) -> Tuple[List[TeamInvitation], int]:
        """Get team invitations"""
        
        query = (
            select(TeamInvitation)
            .options(
                selectinload(TeamInvitation.team),
                selectinload(TeamInvitation.invited_user),
                selectinload(TeamInvitation.invited_by)
            )
            .where(TeamInvitation.team_id == team_id)
        )
        count_query = select(func.count(TeamInvitation.id)).where(TeamInvitation.team_id == team_id)
        
        if status:
            query = query.where(TeamInvitation.status == status)
            count_query = count_query.where(TeamInvitation.status == status)
        
        # Get total count
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Apply pagination
        query = (
            query
            .order_by(TeamInvitation.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        
        result = await db.execute(query)
        invitations = list(result.scalars().all())
        
        return invitations, total
    
    @staticmethod
    async def respond_to_invitation(
        db: AsyncSession,
        invitation_id: str,
        accept: bool,
        user_id: str
    ) -> Optional[TeamInvitation]:
        """Respond to team invitation"""
        
        result = await db.execute(
            select(TeamInvitation)
            .options(selectinload(TeamInvitation.team))
            .where(TeamInvitation.id == invitation_id)
        )
        invitation = result.scalar_one_or_none()
        
        if not invitation:
            return None
        
        # Check if invitation is for this user
        if invitation.invited_user_id != user_id:
            return None
        
        # Check if invitation is still valid
        if invitation.status != "pending" or (invitation.expires_at and invitation.expires_at < datetime.utcnow()):
            return None
        
        # Update invitation status
        invitation.status = "accepted" if accept else "declined"
        invitation.responded_at = datetime.utcnow()
        
        # If accepted, add user to team
        if accept:
            member_data = TeamMemberCreate(
                user_id=user_id,
                role=MemberRole(invitation.proposed_role),
                jersey_number=None,
                position=None
            )
            await TeamService.add_team_member(db, invitation.team_id, member_data, auto_approve=True)
        
        await db.commit()
        await db.refresh(invitation)
        
        return invitation