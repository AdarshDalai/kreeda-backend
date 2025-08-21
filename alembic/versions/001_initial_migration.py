"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2025-01-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum types
    op.execute("""
        CREATE TYPE authprovider AS ENUM ('email', 'google', 'apple');
        CREATE TYPE userrole AS ENUM ('player', 'scorekeeper', 'organizer', 'spectator', 'admin');
    """)
    
    # Create users table
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=True),
        sa.Column('auth_provider', sa.Enum('email', 'google', 'apple', name='authprovider'), nullable=False),
        sa.Column('provider_id', sa.String(length=255), nullable=True),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('avatar_url', sa.Text(), nullable=True),
        sa.Column('role', sa.Enum('player', 'scorekeeper', 'organizer', 'spectator', 'admin', name='userrole'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('email_verified', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('refresh_token_hash', sa.String(length=255), nullable=True),
        sa.Column('reset_token_hash', sa.String(length=255), nullable=True),
        sa.Column('reset_token_expires', sa.DateTime(timezone=True), nullable=True),
        sa.Column('email_verification_token_hash', sa.String(length=255), nullable=True),
        sa.Column('email_verification_token_expires', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    
    # Drop table
    op.drop_table('users')
    
    # Drop enum types
    op.execute("DROP TYPE IF EXISTS userrole;")
    op.execute("DROP TYPE IF EXISTS authprovider;")
