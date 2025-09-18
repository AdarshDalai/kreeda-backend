"""Add performance indexes for cricket and team queries

Revision ID: 8a48ed4caad4
Revises: eff80602130c
Create Date: 2025-09-18 23:40:58.647005

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8a48ed4caad4'
down_revision: Union[str, None] = 'eff80602130c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### Performance indexes for cricket and team queries ###
    
    # Cricket match performance indexes
    op.create_index('idx_cricket_matches_date', 'cricket_matches', ['match_date'])
    op.create_index('idx_cricket_matches_status', 'cricket_matches', ['status'])
    op.create_index('idx_cricket_matches_teams', 'cricket_matches', ['team_a_id', 'team_b_id'])
    
    # Cricket balls performance indexes
    op.create_index('idx_cricket_balls_match_innings', 'cricket_balls', ['match_id', 'innings'])
    op.create_index('idx_cricket_balls_over', 'cricket_balls', ['match_id', 'over_number', 'ball_number'])
    
    # Team members performance indexes
    op.create_index('idx_team_members_lookup', 'team_members', ['team_id', 'user_id'])
    op.create_index('idx_team_members_user', 'team_members', ['user_id'])
    
    # Team invitations performance indexes
    op.create_index('idx_team_invitations_team_status', 'team_invitations', ['team_id', 'status'])
    op.create_index('idx_team_invitations_expires', 'team_invitations', ['expires_at'])
    
    # Playing XI performance indexes  
    op.create_index('idx_playing_xi_match_team', 'match_playing_xi', ['match_id', 'team_id'])
    op.create_index('idx_playing_xi_batting_order', 'match_playing_xi', ['match_id', 'team_id', 'batting_order'])
    
    # User activity indexes
    op.create_index('idx_users_email_active', 'users', ['email', 'is_active'])
    op.create_index('idx_teams_active', 'teams', ['is_active'])


def downgrade() -> None:
    # ### Remove performance indexes ###
    
    # Cricket match indexes
    op.drop_index('idx_cricket_matches_date')
    op.drop_index('idx_cricket_matches_status')
    op.drop_index('idx_cricket_matches_teams')
    
    # Cricket balls indexes
    op.drop_index('idx_cricket_balls_match_innings')
    op.drop_index('idx_cricket_balls_over')
    
    # Team members indexes
    op.drop_index('idx_team_members_lookup')
    op.drop_index('idx_team_members_user')
    
    # Team invitations indexes
    op.drop_index('idx_team_invitations_team_status')
    op.drop_index('idx_team_invitations_expires')
    
    # Playing XI indexes
    op.drop_index('idx_playing_xi_match_team')
    op.drop_index('idx_playing_xi_batting_order')
    
    # User activity indexes
    op.drop_index('idx_users_email_active')
    op.drop_index('idx_teams_active')
