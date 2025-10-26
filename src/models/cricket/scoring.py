"""
Scoring Integrity Models
Event sourcing and consensus validation for tamper-proof scoring
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, BigInteger, Text, Numeric, Enum as SQLEnum, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from src.models.base import Base
from src.models.enums import (
    EventType, ValidationStatus, ScorerTeamSide,
    DisputeType, ResolutionStatus, ConsensusMethod
)


class ScoringEvent(Base):
    """
    Immutable event log - every scoring action recorded
    The foundation of our tamper-proof scoring system
    """
    __tablename__ = "scoring_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    match_id = Column(UUID(as_uuid=True), ForeignKey("matches.id", ondelete="CASCADE"), nullable=False)
    innings_id = Column(UUID(as_uuid=True), ForeignKey("innings.id"), nullable=True)
    ball_id = Column(UUID(as_uuid=True), ForeignKey("balls.id"), nullable=True)
    
    # Who Recorded This?
    scorer_user_id = Column(UUID(as_uuid=True), ForeignKey("user_auth.user_id"), nullable=False)
    scorer_team_side = Column(SQLEnum(ScorerTeamSide, name="scorer_team_side"), nullable=False)
    
    # Event Type
    event_type = Column(SQLEnum(EventType, name="event_type"), nullable=False)
    
    # Event Data (Flexible JSONB for different event types)
    event_data = Column(JSONB, nullable=False)  # {runs: 4, batsman: "uuid", bowler: "uuid", ...}
    
    # Validation State
    validation_status = Column(SQLEnum(ValidationStatus, name="validation_status"), default=ValidationStatus.PENDING)
    
    # Consensus Tracking
    matching_event_id = Column(UUID(as_uuid=True), ForeignKey("scoring_events.id"), nullable=True)
    validated_at = Column(DateTime, nullable=True)
    validated_by_user_id = Column(UUID(as_uuid=True), ForeignKey("user_auth.user_id"), nullable=True)
    
    # Cryptographic Integrity (Hash Chain)
    event_hash = Column(String(64), nullable=False)  # SHA256(event_data + previous_event_hash)
    previous_event_hash = Column(String(64), nullable=True)
    signature = Column(String(256), nullable=True)  # HMAC of event_data with scorer's JWT
    
    # Timestamp (CRITICAL for ordering)
    event_timestamp = Column(DateTime(timezone=True), nullable=False)
    sequence_number = Column(BigInteger, autoincrement=True, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    match = relationship("Match")
    innings = relationship("Innings")
    ball = relationship("Ball")
    scorer = relationship("UserAuth", foreign_keys=[scorer_user_id])
    validator = relationship("UserAuth", foreign_keys=[validated_by_user_id])
    matching_event = relationship("ScoringEvent", remote_side=[id], foreign_keys=[matching_event_id])

    def __repr__(self):
        return f"<ScoringEvent(id={self.id}, type={self.event_type}, status={self.validation_status})>"


class ScoringDispute(Base):
    """
    Log of all scoring conflicts and their resolution
    """
    __tablename__ = "scoring_disputes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    match_id = Column(UUID(as_uuid=True), ForeignKey("matches.id", ondelete="CASCADE"), nullable=False)
    ball_id = Column(UUID(as_uuid=True), ForeignKey("balls.id"), nullable=True)
    
    # The Conflicting Events
    scorer_a_event_id = Column(UUID(as_uuid=True), ForeignKey("scoring_events.id"), nullable=False)
    scorer_b_event_id = Column(UUID(as_uuid=True), ForeignKey("scoring_events.id"), nullable=False)
    umpire_event_id = Column(UUID(as_uuid=True), ForeignKey("scoring_events.id"), nullable=True)
    
    # Dispute Details
    dispute_type = Column(SQLEnum(DisputeType, name="dispute_type"), nullable=False)
    scorer_a_claim = Column(JSONB, nullable=False)  # What Scorer A said
    scorer_b_claim = Column(JSONB, nullable=False)  # What Scorer B said
    umpire_claim = Column(JSONB, nullable=True)  # What Umpire said (if present)
    
    # Auto-detected Difference
    difference_summary = Column(Text, nullable=True)
    
    # Resolution
    resolution_status = Column(SQLEnum(ResolutionStatus, name="resolution_status"), default=ResolutionStatus.PENDING)
    resolved_by_user_id = Column(UUID(as_uuid=True), ForeignKey("user_auth.user_id"), nullable=True)
    resolution_method = Column(String(50), nullable=True)  # 'umpire_override', 'scorer_concession', etc.
    final_decision = Column(JSONB, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    
    # Timing
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    resolution_time_seconds = Column(Integer, nullable=True)
    
    # Relationships
    match = relationship("Match")
    ball = relationship("Ball")
    scorer_a_event = relationship("ScoringEvent", foreign_keys=[scorer_a_event_id])
    scorer_b_event = relationship("ScoringEvent", foreign_keys=[scorer_b_event_id])
    umpire_event = relationship("ScoringEvent", foreign_keys=[umpire_event_id])
    resolver = relationship("UserAuth", foreign_keys=[resolved_by_user_id])

    def __repr__(self):
        return f"<ScoringDispute(id={self.id}, type={self.dispute_type}, status={self.resolution_status})>"


class ScoringConsensus(Base):
    """
    Tracks validation outcomes for matched events
    """
    __tablename__ = "scoring_consensus"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    match_id = Column(UUID(as_uuid=True), ForeignKey("matches.id"), nullable=False)
    ball_id = Column(UUID(as_uuid=True), ForeignKey("balls.id"), nullable=True)
    
    # Events Being Validated (Array of UUIDs)
    event_ids = Column(ARRAY(UUID(as_uuid=True)), nullable=False)
    
    # Consensus Result
    consensus_reached = Column(Boolean, nullable=False)
    consensus_method = Column(SQLEnum(ConsensusMethod, name="consensus_method"), nullable=False)
    confidence_score = Column(Numeric(3, 2), default=1.00)  # 0.00 to 1.00
    
    # Final State
    final_state = Column(JSONB, nullable=False)  # The accepted event data
    applied_to_ball = Column(Boolean, default=False)
    
    # Who Made Final Decision
    final_authority_user_id = Column(UUID(as_uuid=True), ForeignKey("user_auth.user_id"), nullable=True)
    
    # Timing
    validation_time_ms = Column(Integer, nullable=True)  # How long validation took (milliseconds)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    match = relationship("Match")
    ball = relationship("Ball")
    final_authority = relationship("UserAuth", foreign_keys=[final_authority_user_id])

    def __repr__(self):
        return f"<ScoringConsensus(id={self.id}, method={self.consensus_method})>"
