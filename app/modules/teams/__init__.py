"""
Team Management Module

This module handles team creation, membership, and invitation management
"""

from .models import Team, TeamMember, TeamInvitation, TeamType, TeamStatus, MemberRole, MemberStatus
from .schemas import (
    Team as TeamSchema, TeamCreate, TeamUpdate, TeamSummary, TeamListResponse,
    TeamWithMembers, TeamMember as TeamMemberSchema, TeamMemberCreate, 
    TeamMemberUpdate, TeamMemberListResponse, TeamInvitation as TeamInvitationSchema,
    TeamInvitationCreate, TeamInvitationListResponse
)
from .service import TeamService
from .endpoints import router as team_router

__all__ = [
    # Models
    "Team", "TeamMember", "TeamInvitation", 
    "TeamType", "TeamStatus", "MemberRole", "MemberStatus",
    
    # Schemas
    "TeamSchema", "TeamCreate", "TeamUpdate", "TeamSummary", "TeamListResponse",
    "TeamWithMembers", "TeamMemberSchema", "TeamMemberCreate", "TeamMemberUpdate", 
    "TeamMemberListResponse", "TeamInvitationSchema", "TeamInvitationCreate", 
    "TeamInvitationListResponse",
    
    # Service
    "TeamService",
    
    # Router
    "team_router"
]