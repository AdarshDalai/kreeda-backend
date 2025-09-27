"""
Team Management Schemas

Pydantic schemas for team management API serialization
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from uuid import UUID

from .models import TeamType, TeamStatus, MemberRole, MemberStatus


# Base schemas
class TeamBase(BaseModel):
    """Base team schema with common fields"""
    name: str = Field(..., min_length=2, max_length=100)
    short_name: Optional[str] = Field(None, max_length=10)
    description: Optional[str] = None
    team_type: TeamType
    logo_url: Optional[str] = None
    home_ground: Optional[str] = Field(None, max_length=200)
    founded_year: Optional[int] = Field(None, ge=1800, le=2030)
    website: Optional[str] = Field(None, max_length=200)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: str = "India"
    is_public: bool = True
    auto_accept_members: bool = False
    max_members: int = Field(50, ge=5, le=200)
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = Field(None, pattern=r'^\+?[1-9]\d{1,14}$')
    settings: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)


class TeamCreate(TeamBase):
    """Schema for creating a new team"""
    pass


class TeamUpdate(BaseModel):
    """Schema for updating team information"""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    short_name: Optional[str] = Field(None, max_length=10)
    description: Optional[str] = None
    status: Optional[TeamStatus] = None
    logo_url: Optional[str] = None
    home_ground: Optional[str] = Field(None, max_length=200)
    founded_year: Optional[int] = Field(None, ge=1800, le=2030)
    website: Optional[str] = Field(None, max_length=200)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = None
    is_public: Optional[bool] = None
    auto_accept_members: Optional[bool] = None
    max_members: Optional[int] = Field(None, ge=5, le=200)
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = Field(None, pattern=r'^\+?[1-9]\d{1,14}$')
    settings: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None


class TeamSummary(BaseModel):
    """Basic team information for lists"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    name: str
    short_name: Optional[str]
    team_type: str
    status: str
    logo_url: Optional[str]
    city: Optional[str]
    state: Optional[str]
    is_public: bool
    member_count: Optional[int] = 0
    created_at: datetime
    updated_at: datetime


class Team(TeamBase):
    """Full team schema with all fields"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    status: str
    created_at: datetime
    updated_at: datetime


# Team Member schemas
class TeamMemberBase(BaseModel):
    """Base team member schema"""
    role: MemberRole = MemberRole.PLAYER
    jersey_number: Optional[int] = Field(None, ge=1, le=999)
    position: Optional[str] = Field(None, max_length=50)
    permissions: Dict[str, Any] = Field(default_factory=dict)
    notes: Optional[str] = None
    stats: Dict[str, Any] = Field(default_factory=dict)


class TeamMemberCreate(BaseModel):
    """Schema for adding a member to team"""
    user_id: str  # Changed from UUID to str to match model
    role: MemberRole = MemberRole.PLAYER
    jersey_number: Optional[int] = Field(None, ge=1, le=999)
    position: Optional[str] = Field(None, max_length=50)
    permissions: Dict[str, Any] = Field(default_factory=dict)
    notes: Optional[str] = None
    stats: Dict[str, Any] = Field(default_factory=dict)


class TeamMemberUpdate(BaseModel):
    """Schema for updating team member"""
    role: Optional[MemberRole] = None
    status: Optional[MemberStatus] = None
    jersey_number: Optional[int] = Field(None, ge=1, le=999)
    position: Optional[str] = Field(None, max_length=50)
    permissions: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None
    stats: Optional[Dict[str, Any]] = None


class UserSummary(BaseModel):
    """Basic user info for team member display"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    username: str
    email: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None


class TeamMember(TeamMemberBase):
    """Full team member schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    team_id: str
    user_id: str
    status: str
    joined_date: datetime
    left_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    # Nested user data
    user: Optional[UserSummary] = None


class TeamWithMembers(Team):
    """Team schema with member details"""
    members: List[TeamMember] = Field(default_factory=list)


# Team Invitation schemas
class TeamInvitationBase(BaseModel):
    """Base invitation schema"""
    proposed_role: MemberRole = MemberRole.PLAYER
    message: Optional[str] = None


class TeamInvitationCreate(TeamInvitationBase):
    """Schema for creating team invitations"""
    email: Optional[EmailStr] = None
    user_id: Optional[str] = None
    
    @classmethod
    def model_validate(cls, obj, *, strict=None, from_attributes=None, context=None):
        """Ensure either email or user_id is provided"""
        values = super().model_validate(obj, strict=strict, from_attributes=from_attributes, context=context)
        if not values.email and not values.user_id:
            raise ValueError('Either email or user_id must be provided')
        return values


class TeamInvitation(TeamInvitationBase):
    """Full invitation schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    team_id: str
    invited_user_id: Optional[str]
    invited_by_id: Optional[str]
    email: Optional[str]
    status: str  # pending, accepted, declined, expired
    expires_at: Optional[datetime]
    responded_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    # Nested data
    team: Optional[TeamSummary] = None
    invited_user: Optional[UserSummary] = None
    invited_by: Optional[UserSummary] = None


# Response schemas
class TeamListResponse(BaseModel):
    """Paginated team list response"""
    items: List[TeamSummary]
    total: int
    page: int
    per_page: int
    pages: int


class TeamMemberListResponse(BaseModel):
    """Paginated team member list response"""
    items: List[TeamMember]
    total: int
    page: int
    per_page: int
    pages: int


class TeamInvitationListResponse(BaseModel):
    """Paginated invitation list response"""
    items: List[TeamInvitation]
    total: int
    page: int
    per_page: int
    pages: int