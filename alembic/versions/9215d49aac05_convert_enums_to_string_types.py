"""Convert enums to string types

Revision ID: 9215d49aac05
Revises: 73afea7cfa87
Create Date: 2025-08-21 10:04:39.407427

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9215d49aac05'
down_revision: Union[str, None] = '73afea7cfa87'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Convert auth_provider enum to string
    op.alter_column('users', 'auth_provider',
                   existing_type=sa.Enum('EMAIL', 'GOOGLE', 'APPLE', name='authprovider'),
                   type_=sa.String(50),
                   nullable=False)
    
    # Convert role enum to string  
    op.alter_column('users', 'role',
                   existing_type=sa.Enum('PLAYER', 'SCOREKEEPER', 'ORGANIZER', 'SPECTATOR', 'ADMIN', name='userrole'),
                   type_=sa.String(50),
                   nullable=False)
    
    # Drop the enum types
    op.execute('DROP TYPE IF EXISTS authprovider CASCADE')
    op.execute('DROP TYPE IF EXISTS userrole CASCADE')


def downgrade() -> None:
    # Recreate enum types
    op.execute("CREATE TYPE authprovider AS ENUM ('EMAIL', 'GOOGLE', 'APPLE')")
    op.execute("CREATE TYPE userrole AS ENUM ('PLAYER', 'SCOREKEEPER', 'ORGANIZER', 'SPECTATOR', 'ADMIN')")
    
    # Convert string columns back to enums
    op.alter_column('users', 'auth_provider',
                   existing_type=sa.String(50),
                   type_=sa.Enum('EMAIL', 'GOOGLE', 'APPLE', name='authprovider'),
                   nullable=False)
    
    op.alter_column('users', 'role',
                   existing_type=sa.String(50),
                   type_=sa.Enum('PLAYER', 'SCOREKEEPER', 'ORGANIZER', 'SPECTATOR', 'ADMIN', name='userrole'),
                   nullable=False)
