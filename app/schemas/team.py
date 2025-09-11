import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.user import UserResponse


class TeamBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    short_name: str = Field(..., min_length=1, max_length=10)
    logo_url: Optional[str] = None


class TeamCreate(TeamBase):
    captain_id: uuid.UUID


class TeamUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    short_name: Optional[str] = Field(None, min_length=1, max_length=10)
    logo_url: Optional[str] = None
    captain_id: Optional[uuid.UUID] = None


class TeamMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    role: str
    jersey_number: Optional[str] = None
    joined_at: datetime
    user: UserResponse


class TeamResponse(TeamBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_by_id: uuid.UUID
    captain_id: uuid.UUID
    created_at: datetime
    is_active: bool
    creator: UserResponse
    captain: UserResponse
    members: List[TeamMemberResponse] = []


class TeamMemberAdd(BaseModel):
    username: str = Field(..., min_length=3, max_length=20)
    role: str = Field("player", pattern="^(player|captain|vice_captain)$")
    jersey_number: Optional[str] = Field(None, max_length=10)


class TeamSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    short_name: str
    logo_url: Optional[str] = None
