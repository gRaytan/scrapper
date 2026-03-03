"""add_alert_reminder_tracking_to_users

Revision ID: f4539b4f174a
Revises: 7d602df3b491
Create Date: 2026-03-03 20:47:00.041326

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f4539b4f174a'
down_revision: Union[str, None] = '7d602df3b491'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add alert reminder tracking fields to users table
    op.add_column('users', sa.Column('alert_reminder_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('users', sa.Column('last_alert_reminder_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    # Remove alert reminder tracking fields from users table
    op.drop_column('users', 'last_alert_reminder_at')
    op.drop_column('users', 'alert_reminder_count')
