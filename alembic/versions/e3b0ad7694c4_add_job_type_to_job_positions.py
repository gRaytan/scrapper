"""add_job_type_to_job_positions

Revision ID: e3b0ad7694c4
Revises: a1b2c3d4e5f6
Create Date: 2026-02-08 20:45:15.547393

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e3b0ad7694c4'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add job_type column with default 'fulltime'
    op.add_column(
        'job_positions',
        sa.Column('job_type', sa.String(50), nullable=False, server_default='fulltime')
    )
    # Add index for filtering by job_type
    op.create_index('ix_job_positions_job_type', 'job_positions', ['job_type'])


def downgrade() -> None:
    op.drop_index('ix_job_positions_job_type', table_name='job_positions')
    op.drop_column('job_positions', 'job_type')
