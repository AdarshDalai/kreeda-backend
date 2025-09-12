import enum
import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.utils.database import Base


class ScorerRole(str, enum.Enum):
    TEAM_A_SCORER = "team_a_scorer"
    TEAM_B_SCORER = "team_b_scorer"
    UMPIRE = "umpire"
    REFEREE = "referee"


class MatchScorer(Base):
    """Authorized scorers for a match - ensures only designated people can update scores"""

    __tablename__ = "match_scorers"

    match_id = Column(
        UUID(as_uuid=True), ForeignKey("cricket_matches.id"), primary_key=True
    )
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    role = Column(Enum(ScorerRole), nullable=False)
    appointed_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    appointed_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    match = relationship("CricketMatch")
    scorer = relationship("User", foreign_keys=[user_id])
    appointed_by = relationship("User", foreign_keys=[appointed_by_id])


class BallScoreEntry(Base):
    """Individual ball score entries - allows multiple scorers to record same ball"""

    __tablename__ = "ball_score_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    match_id = Column(
        UUID(as_uuid=True), ForeignKey("cricket_matches.id"), nullable=False, index=True
    )
    scorer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Ball identification
    innings = Column(Integer, nullable=False)
    over_number = Column(Integer, nullable=False)
    ball_number = Column(Integer, nullable=False)

    # Players involved
    bowler_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    batsman_striker_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    batsman_non_striker_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    # Ball outcome
    runs_scored = Column(Integer, default=0)
    extras = Column(Integer, default=0)
    ball_type = Column(String(20), default="legal")

    # Wicket information
    is_wicket = Column(Boolean, default=False)
    wicket_type = Column(String(20), nullable=True)
    dismissed_player_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    # Additional info
    is_boundary = Column(Boolean, default=False)
    boundary_type = Column(String(10), nullable=True)

    # Metadata
    entry_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    is_verified = Column(Boolean, default=False)
    verification_status = Column(
        String(20), default="pending"
    )  # pending, verified, disputed, rejected

    # Relationships
    match = relationship("CricketMatch")
    scorer = relationship("User", foreign_keys=[scorer_id])
    bowler = relationship("User", foreign_keys=[bowler_id])
    batsman_striker = relationship("User", foreign_keys=[batsman_striker_id])
    batsman_non_striker = relationship("User", foreign_keys=[batsman_non_striker_id])
    dismissed_player = relationship("User", foreign_keys=[dismissed_player_id])


class BallVerification(Base):
    """Verification records for each ball - tracks consensus between scorers"""

    __tablename__ = "ball_verifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    match_id = Column(
        UUID(as_uuid=True), ForeignKey("cricket_matches.id"), nullable=False
    )
    innings = Column(Integer, nullable=False)
    over_number = Column(Integer, nullable=False)
    ball_number = Column(Integer, nullable=False)

    # Verification details
    total_entries = Column(Integer, default=0)
    matching_entries = Column(Integer, default=0)
    consensus_reached = Column(Boolean, default=False)
    final_entry_id = Column(
        UUID(as_uuid=True), ForeignKey("ball_score_entries.id"), nullable=True
    )

    # Dispute handling
    has_dispute = Column(Boolean, default=False)
    dispute_reason = Column(Text, nullable=True)
    resolved_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    resolution_notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    verified_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    match = relationship("CricketMatch")
    final_entry = relationship("BallScoreEntry")
    resolved_by = relationship("User", foreign_keys=[resolved_by_id])


class ScoringAuditLog(Base):
    """Comprehensive audit trail for all scoring activities"""

    __tablename__ = "scoring_audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    match_id = Column(
        UUID(as_uuid=True), ForeignKey("cricket_matches.id"), nullable=False, index=True
    )
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Action details
    action_type = Column(
        String(50), nullable=False
    )  # ball_entry, verification, dispute, resolution
    target_innings = Column(Integer, nullable=True)
    target_over = Column(Integer, nullable=True)
    target_ball = Column(Integer, nullable=True)

    # Data changes
    old_values = Column(Text, nullable=True)  # JSON string of old values
    new_values = Column(Text, nullable=True)  # JSON string of new values

    # Context
    ip_address = Column(String(45), nullable=True)  # IPv4/IPv6 address
    user_agent = Column(Text, nullable=True)
    session_id = Column(String(100), nullable=True)

    # Metadata
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    notes = Column(Text, nullable=True)

    # Relationships
    match = relationship("CricketMatch")
    user = relationship("User")


class MatchIntegrityCheck(Base):
    """Periodic integrity checks for match data consistency"""

    __tablename__ = "match_integrity_checks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    match_id = Column(
        UUID(as_uuid=True), ForeignKey("cricket_matches.id"), nullable=False
    )

    # Check details
    check_type = Column(
        String(50), nullable=False
    )  # ball_sequence, score_calculation, player_validation
    check_result = Column(String(20), nullable=False)  # passed, failed, warning

    # Issues found
    issues_count = Column(Integer, default=0)
    issues_detail = Column(Text, nullable=True)  # JSON string of specific issues

    # Resolution
    auto_resolved = Column(Boolean, default=False)
    manual_resolution_required = Column(Boolean, default=False)
    resolved_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Timestamps
    checked_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    match = relationship("CricketMatch")
    resolved_by = relationship("User")
