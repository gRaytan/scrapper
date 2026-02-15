"""Split interview stage into multiple stages

Revision ID: h2i3j4k5l6m7
Revises: g1h2i3j4k5l6
Create Date: 2026-02-15 21:00:00.000000

This migration:
1. Migrates existing 'interviewing' status to 'phone_screen'
2. No schema changes needed (status is a varchar field)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'h2i3j4k5l6m7'
down_revision: Union[str, None] = 'g1h2i3j4k5l6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Migrate 'interviewing' status to 'phone_screen'."""
    # Update all applications with 'interviewing' status to 'phone_screen'
    op.execute(
        "UPDATE user_job_applications SET status = 'phone_screen' WHERE status = 'interviewing'"
    )


def downgrade() -> None:
    """Migrate interview stages back to 'interviewing'."""
    # Merge all interview stages back to 'interviewing'
    interview_stages = ['phone_screen', 'technical_1', 'technical_2', 'hr_interview', 'reference_check']
    for stage in interview_stages:
        op.execute(
            f"UPDATE user_job_applications SET status = 'interviewing' WHERE status = '{stage}'"
        )
