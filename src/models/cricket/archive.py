"""
Match Summary and Archive Models
Aggregates and cold storage
"""
import uuid
from datetime import datetime, date
from sqlalchemy import Column, String, Boolean, DateTime, Date, ForeignKey, Integer, BigInteger, Text, Numeric, Enum as SQLEnum, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from src.models.base import Base
from src.models.enums import ArchiveStatus, MatchType


class MatchSummary(Base):
    """
    Pre-computed match statistics for fast retrieval
    """
    __tablename__ = "match_summaries"

    match_id = Column(UUID(as_uuid=True), ForeignKey("matches.id", ondelete="CASCADE"), primary_key=True)
    
    # Team A Stats
    team_a_runs = Column(Integer, default=0)
    team_a_wickets = Column(Integer, default=0)
    team_a_overs = Column(Numeric(4, 1), default=0.0)
    team_a_run_rate = Column(Numeric(4, 2), nullable=True)
    
    # Team B Stats
    team_b_runs = Column(Integer, default=0)
    team_b_wickets = Column(Integer, default=0)
    team_b_overs = Column(Numeric(4, 1), default=0.0)
    team_b_run_rate = Column(Numeric(4, 2), nullable=True)
    
    # Top Performers
    highest_scorer_user_id = Column(UUID(as_uuid=True), ForeignKey("user_auth.user_id"), nullable=True)
    highest_score = Column(Integer, nullable=True)
    best_bowler_user_id = Column(UUID(as_uuid=True), ForeignKey("user_auth.user_id"), nullable=True)
    best_bowling_figures = Column(String(10), nullable=True)  # "5/23"
    
    # Match Highlights
    total_boundaries = Column(Integer, default=0)
    total_sixes = Column(Integer, default=0)
    total_fours = Column(Integer, default=0)
    highest_partnership = Column(Integer, default=0)
    
    # Scoring Integrity Metrics
    total_balls = Column(Integer, default=0)
    disputed_balls = Column(Integer, default=0)
    dispute_rate = Column(Numeric(4, 2), nullable=True)  # Percentage
    avg_validation_time_ms = Column(Integer, nullable=True)
    
    # Data Quality
    completeness_score = Column(Numeric(3, 2), nullable=True)  # 0.00 to 1.00
    
    # Computed/Updated
    last_updated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    match = relationship("Match")
    highest_scorer = relationship("UserAuth", foreign_keys=[highest_scorer_user_id])
    best_bowler = relationship("UserAuth", foreign_keys=[best_bowler_user_id])

    def __repr__(self):
        return f"<MatchSummary(match_id={self.match_id})>"


class MatchArchive(Base):
    """
    Lightweight index for archived matches (full data in S3/MinIO)
    """
    __tablename__ = "match_archives"

    match_id = Column(UUID(as_uuid=True), ForeignKey("matches.id"), primary_key=True)
    
    # Archive Location
    archive_status = Column(SQLEnum(ArchiveStatus, name="archive_status"), default=ArchiveStatus.ACTIVE)
    archive_location = Column(String(500), nullable=True)  # S3/MinIO URL
    archive_size_bytes = Column(BigInteger, nullable=True)
    compression_format = Column(String(20), default="gzip")
    
    # Match Summary (for search without fetching full archive)
    match_summary = Column(JSONB, nullable=False)  # {teams, date, result, venue, key_stats}
    
    # Participants (for "my matches" queries)
    participant_user_ids = Column(ARRAY(UUID(as_uuid=True)), nullable=False)
    team_ids = Column(ARRAY(UUID(as_uuid=True)), nullable=False)
    
    # Match Metadata (for filtering)
    match_date = Column(Date, nullable=False)
    venue_city = Column(String(100), nullable=True)
    match_type = Column(SQLEnum(MatchType, name="match_type"), nullable=True)
    
    # Retention
    retain_permanently = Column(Boolean, default=False)
    retention_reason = Column(Text, nullable=True)
    scheduled_deletion_at = Column(DateTime, nullable=True)
    
    # Timing
    archived_at = Column(DateTime, nullable=True)
    last_accessed_at = Column(DateTime, nullable=True)
    access_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    match = relationship("Match")

    def __repr__(self):
        return f"<MatchArchive(match_id={self.match_id}, status={self.archive_status})>"
