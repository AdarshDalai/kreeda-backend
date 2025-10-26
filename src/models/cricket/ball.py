"""
Ball and Wicket Models
The atomic unit of cricket scoring
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, Numeric, CheckConstraint, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from src.models.base import Base
from src.models.enums import ExtraType, BoundaryType, ShotType, DismissalType


class Ball(Base):
    """
    The atomic unit of cricket - each ball bowled
    """
    __tablename__ = "balls"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    innings_id = Column(UUID(as_uuid=True), ForeignKey("innings.id", ondelete="CASCADE"), nullable=False)
    over_id = Column(UUID(as_uuid=True), ForeignKey("overs.id"), nullable=False)
    ball_number = Column(Numeric(4, 1), nullable=False)  # e.g., 15.4 (over 15, ball 4)
    
    # Who's Involved
    bowler_user_id = Column(UUID(as_uuid=True), ForeignKey("user_auth.user_id"), nullable=False)
    batsman_user_id = Column(UUID(as_uuid=True), ForeignKey("user_auth.user_id"), nullable=False)  # Striker
    non_striker_user_id = Column(UUID(as_uuid=True), ForeignKey("user_auth.user_id"), nullable=True)
    
    # Ball Outcome
    runs_scored = Column(Integer, default=0)
    is_wicket = Column(Boolean, default=False)
    is_boundary = Column(Boolean, default=False)
    boundary_type = Column(SQLEnum(BoundaryType, name="boundary_type"), nullable=True)
    
    # Extras
    is_legal_delivery = Column(Boolean, default=True)
    extra_type = Column(SQLEnum(ExtraType, name="extra_type"), default=ExtraType.NONE)
    extra_runs = Column(Integer, default=0)
    
    # Advanced Analytics (Optional)
    shot_type = Column(SQLEnum(ShotType, name="shot_type"), nullable=True)
    fielding_position = Column(String(50), nullable=True)
    wagon_wheel_data = Column(JSONB, nullable=True)  # {angle: 45, distance: 75}
    
    # Milestones
    is_milestone = Column(Boolean, default=False)
    milestone_type = Column(String(50), nullable=True)  # "fifty", "hundred", "hat_trick"
    
    # Validation Metadata
    validation_source = Column(String(50), default="dual_scorer")
    validation_confidence = Column(Numeric(3, 2), default=1.00)  # 0.00 to 1.00
    
    # Timestamp
    bowled_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    innings = relationship("Innings", back_populates="balls")
    over = relationship("Over", back_populates="balls")
    bowler = relationship("UserAuth", foreign_keys=[bowler_user_id])
    batsman = relationship("UserAuth", foreign_keys=[batsman_user_id])
    non_striker = relationship("UserAuth", foreign_keys=[non_striker_user_id])
    wicket = relationship("Wicket", back_populates="ball", uselist=False, cascade="all, delete-orphan")
    
    __table_args__ = (
        CheckConstraint('runs_scored >= 0', name='runs_non_negative'),
    )

    def __repr__(self):
        return f"<Ball(innings_id={self.innings_id}, ball={self.ball_number})>"


class Wicket(Base):
    """
    Detailed dismissal information
    """
    __tablename__ = "wickets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ball_id = Column(UUID(as_uuid=True), ForeignKey("balls.id", ondelete="CASCADE"), unique=True, nullable=False)
    innings_id = Column(UUID(as_uuid=True), ForeignKey("innings.id"), nullable=False)
    batsman_out_user_id = Column(UUID(as_uuid=True), ForeignKey("user_auth.user_id"), nullable=False)
    
    # Dismissal Details
    dismissal_type = Column(SQLEnum(DismissalType, name="dismissal_type"), nullable=False)
    
    # Credits
    bowler_user_id = Column(UUID(as_uuid=True), ForeignKey("user_auth.user_id"), nullable=True)  # Null for run-outs
    fielder_user_id = Column(UUID(as_uuid=True), ForeignKey("user_auth.user_id"), nullable=True)  # Catcher, keeper
    fielder2_user_id = Column(UUID(as_uuid=True), ForeignKey("user_auth.user_id"), nullable=True)  # For relay catches
    
    # Context
    wicket_number = Column(Integer, nullable=False)
    team_score_at_wicket = Column(Integer, nullable=False)  # e.g., 45 when "45/3"
    partnership_runs = Column(Integer, default=0)
    
    # Timing
    dismissed_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    ball = relationship("Ball", back_populates="wicket")
    innings = relationship("Innings")
    batsman_out = relationship("UserAuth", foreign_keys=[batsman_out_user_id])
    bowler = relationship("UserAuth", foreign_keys=[bowler_user_id])
    fielder = relationship("UserAuth", foreign_keys=[fielder_user_id])
    fielder2 = relationship("UserAuth", foreign_keys=[fielder2_user_id])
    
    __table_args__ = (
        CheckConstraint('wicket_number BETWEEN 1 AND 10', name='wicket_number_check'),
    )

    def __repr__(self):
        return f"<Wicket(innings_id={self.innings_id}, wicket={self.wicket_number})>"
