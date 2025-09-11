"""Add scoring integrity tables

Revision ID: add_scoring_integrity
Revises:
Create Date: 2025-09-02 12:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "add_scoring_integrity"
down_revision = None
depends_on = None


def upgrade():
    # Create scorer role enum
    scorer_role_enum = postgresql.ENUM(
        "team_a_scorer", "team_b_scorer", "umpire", "referee", name="scorerrole"
    )
    scorer_role_enum.create(op.get_bind())

    # Create match_scorers table
    op.create_table(
        "match_scorers",
        sa.Column("match_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", scorer_role_enum, nullable=False),
        sa.Column("appointed_by_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column(
            "appointed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["appointed_by_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["match_id"],
            ["cricket_matches.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("match_id", "user_id"),
    )

    # Create ball_score_entries table
    op.create_table(
        "ball_score_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("match_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("scorer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("innings", sa.Integer(), nullable=False),
        sa.Column("over_number", sa.Integer(), nullable=False),
        sa.Column("ball_number", sa.Integer(), nullable=False),
        sa.Column("bowler_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("batsman_striker_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "batsman_non_striker_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column("runs_scored", sa.Integer(), nullable=True),
        sa.Column("extras", sa.Integer(), nullable=True),
        sa.Column("ball_type", sa.String(length=20), nullable=True),
        sa.Column("is_wicket", sa.Boolean(), nullable=True),
        sa.Column("wicket_type", sa.String(length=20), nullable=True),
        sa.Column("dismissed_player_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_boundary", sa.Boolean(), nullable=True),
        sa.Column("boundary_type", sa.String(length=10), nullable=True),
        sa.Column(
            "entry_timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("is_verified", sa.Boolean(), nullable=True),
        sa.Column("verification_status", sa.String(length=20), nullable=True),
        sa.ForeignKeyConstraint(
            ["batsman_non_striker_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["batsman_striker_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["bowler_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["dismissed_player_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["match_id"],
            ["cricket_matches.id"],
        ),
        sa.ForeignKeyConstraint(
            ["scorer_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_ball_score_entries_match_id",
        "ball_score_entries",
        ["match_id"],
        unique=False,
    )

    # Create ball_verifications table
    op.create_table(
        "ball_verifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("match_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("innings", sa.Integer(), nullable=False),
        sa.Column("over_number", sa.Integer(), nullable=False),
        sa.Column("ball_number", sa.Integer(), nullable=False),
        sa.Column("total_entries", sa.Integer(), nullable=True),
        sa.Column("matching_entries", sa.Integer(), nullable=True),
        sa.Column("consensus_reached", sa.Boolean(), nullable=True),
        sa.Column("final_entry_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("has_dispute", sa.Boolean(), nullable=True),
        sa.Column("dispute_reason", sa.Text(), nullable=True),
        sa.Column("resolved_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["final_entry_id"],
            ["ball_score_entries.id"],
        ),
        sa.ForeignKeyConstraint(
            ["match_id"],
            ["cricket_matches.id"],
        ),
        sa.ForeignKeyConstraint(
            ["resolved_by_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create scoring_audit_logs table
    op.create_table(
        "scoring_audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("match_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action_type", sa.String(length=50), nullable=False),
        sa.Column("target_innings", sa.Integer(), nullable=True),
        sa.Column("target_over", sa.Integer(), nullable=True),
        sa.Column("target_ball", sa.Integer(), nullable=True),
        sa.Column("old_values", sa.Text(), nullable=True),
        sa.Column("new_values", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("session_id", sa.String(length=100), nullable=True),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["match_id"],
            ["cricket_matches.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_scoring_audit_logs_match_id",
        "scoring_audit_logs",
        ["match_id"],
        unique=False,
    )

    # Create match_integrity_checks table
    op.create_table(
        "match_integrity_checks",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("match_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("check_type", sa.String(length=50), nullable=False),
        sa.Column("check_result", sa.String(length=20), nullable=False),
        sa.Column("issues_count", sa.Integer(), nullable=True),
        sa.Column("issues_detail", sa.Text(), nullable=True),
        sa.Column("auto_resolved", sa.Boolean(), nullable=True),
        sa.Column("manual_resolution_required", sa.Boolean(), nullable=True),
        sa.Column("resolved_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "checked_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["match_id"],
            ["cricket_matches.id"],
        ),
        sa.ForeignKeyConstraint(
            ["resolved_by_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    op.drop_table("match_integrity_checks")
    op.drop_index("ix_scoring_audit_logs_match_id", "scoring_audit_logs")
    op.drop_table("scoring_audit_logs")
    op.drop_table("ball_verifications")
    op.drop_index("ix_ball_score_entries_match_id", "ball_score_entries")
    op.drop_table("ball_score_entries")
    op.drop_table("match_scorers")

    # Drop enum
    scorer_role_enum = postgresql.ENUM(
        "team_a_scorer", "team_b_scorer", "umpire", "referee", name="scorerrole"
    )
    scorer_role_enum.drop(op.get_bind())
