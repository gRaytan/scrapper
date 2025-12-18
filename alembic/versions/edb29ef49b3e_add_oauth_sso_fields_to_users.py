"""add_oauth_sso_fields_to_users

Revision ID: edb29ef49b3e
Revises: 1635f1436b42
Create Date: 2025-12-18

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'edb29ef49b3e'
down_revision: Union[str, None] = '1635f1436b42'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add OAuth SSO fields
    op.add_column('users', sa.Column('oauth_provider', sa.String(length=50), nullable=True))
    op.add_column('users', sa.Column('oauth_provider_id', sa.String(length=255), nullable=True))
    
    # Create index for faster lookups by provider + provider_id
    op.create_index(
        'ix_users_oauth_provider_id', 
        'users', 
        ['oauth_provider', 'oauth_provider_id'], 
        unique=False
    )


def downgrade() -> None:
    op.drop_index('ix_users_oauth_provider_id', table_name='users')
    op.drop_column('users', 'oauth_provider_id')
    op.drop_column('users', 'oauth_provider')
