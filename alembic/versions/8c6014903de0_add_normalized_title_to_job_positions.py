"""add_normalized_title_to_job_positions

Revision ID: 8c6014903de0
Revises: 430dfcdfa250
Create Date: 2026-03-03 23:05:50.210224

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8c6014903de0'
down_revision: Union[str, None] = '430dfcdfa250'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add normalized_title column to job_positions table
    op.add_column('job_positions', sa.Column('normalized_title', sa.String(length=500), nullable=True))

    # Add index on normalized_title for faster filtering
    op.create_index('ix_job_positions_normalized_title', 'job_positions', ['normalized_title'])


def downgrade() -> None:
    # Remove index
    op.drop_index('ix_job_positions_normalized_title', table_name='job_positions')

    # Remove column
    op.drop_column('job_positions', 'normalized_title')
