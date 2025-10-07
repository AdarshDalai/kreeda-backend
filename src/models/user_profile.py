import uuid
from datetime import datetime, date
from sqlalchemy import Column, String, Text, Date, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import ForeignKey
from src.models.base import Base

class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user_auth.user_id"), unique=True, nullable=False)
    name = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    location = Column(String, nullable=True)
    date_of_birth = Column(Date, nullable=True)
    bio = Column(Text, nullable=True)
    preferences = Column(JSON, default=dict)
    roles = Column(JSON, default=dict)  # e.g., {"player": true, "coach": false}
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)