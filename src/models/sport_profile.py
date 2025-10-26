"""
Sport Profile Models
Connects users to specific sports and their sport-specific profiles
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from src.models.base import Base
from src.models.enums import SportType, ProfileVisibility


class SportProfile(Base):
    """
    Links users to specific sports - one user can have multiple sport profiles
    e.g., Same person plays cricket AND football
    """
    __tablename__ = "sport_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user_auth.user_id", ondelete="CASCADE"), nullable=False)
    sport_type = Column(SQLEnum(SportType, name="sport_type"), nullable=False)
    
    # Identity Verification (for claiming professional identities)
    is_verified = Column(Boolean, default=False)
    verification_proof = Column(String, nullable=True)  # How they proved identity
    verified_at = Column(DateTime, nullable=True)
    verified_by_user_id = Column(UUID(as_uuid=True), ForeignKey("user_auth.user_id"), nullable=True)
    
    # Privacy
    visibility = Column(SQLEnum(ProfileVisibility, name="profile_visibility"), default=ProfileVisibility.PUBLIC)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("UserAuth", foreign_keys=[user_id], backref="sport_profiles")
    verifier = relationship("UserAuth", foreign_keys=[verified_by_user_id])
    
    __table_args__ = (
        # One profile per sport per user
        {"schema": None},
    )

    def __repr__(self):
        return f"<SportProfile(user_id={self.user_id}, sport={self.sport_type})>"
