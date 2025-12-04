"""add_auth_fields_to_users

Revision ID: 723144573053
Revises: b754888d80d2
Create Date: 2025-12-04 16:54:45.494024

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '723144573053'
down_revision: Union[str, None] = 'b754888d80d2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add nullable columns first
    op.add_column('users', sa.Column('password_hash', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('phone_number', sa.String(length=20), nullable=True))
    
    # Add phone_verified with default value for existing rows
    op.add_column('users', sa.Column('phone_verified', sa.Boolean(), nullable=True))
    op.execute("UPDATE users SET phone_verified = false WHERE phone_verified IS NULL")
    op.alter_column('users', 'phone_verified', nullable=False)
    
    # Add subscription_tier with default value for existing rows
    op.add_column('users', sa.Column('subscription_tier', sa.String(length=50), nullable=True))
    op.execute("UPDATE users SET subscription_tier = 'free' WHERE subscription_tier IS NULL")
    op.alter_column('users', 'subscription_tier', nullable=False)
    
    # Create index
    op.create_index(op.f('ix_users_subscription_tier'), 'users', ['subscription_tier'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_users_subscription_tier'), table_name='users')
    op.drop_column('users', 'subscription_tier')
    op.drop_column('users', 'phone_verified')
    op.drop_column('users', 'phone_number')
    op.drop_column('users', 'password_hash')
