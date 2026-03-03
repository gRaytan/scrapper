"""add_composite_indexes_for_job_queries

Revision ID: 430dfcdfa250
Revises: f4539b4f174a
Create Date: 2026-03-03 22:07:40.263612

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '430dfcdfa250'
down_revision: Union[str, None] = 'f4539b4f174a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add composite indexes to optimize common job query patterns.

    These indexes significantly improve performance for:
    1. Dashboard queries (is_active + job_type + created_at)
    2. Posted date sorting (is_active + job_type + posted_date)
    3. Company filtering (company_id + is_active + job_type)
    4. Location filtering (location + is_active + job_type)
    """

    # Most important - covers the default dashboard query
    # Supports: WHERE is_active = true AND job_type = 'fulltime' ORDER BY created_at DESC
    op.create_index(
        'idx_job_positions_active_type_created',
        'job_positions',
        ['is_active', 'job_type', sa.text('created_at DESC')],
        postgresql_where=sa.text('is_active = true')
    )

    # For posted_date sorting (alternative sort option)
    # Supports: WHERE is_active = true AND job_type = 'fulltime' ORDER BY posted_date DESC
    op.create_index(
        'idx_job_positions_active_type_posted',
        'job_positions',
        ['is_active', 'job_type', sa.text('posted_date DESC')],
        postgresql_where=sa.text('is_active = true')
    )

    # For company + type filtering
    # Supports: WHERE company_id = X AND is_active = true AND job_type = 'fulltime'
    op.create_index(
        'idx_job_positions_company_active_type',
        'job_positions',
        ['company_id', 'is_active', 'job_type']
    )

    # For location + type filtering
    # Supports: WHERE location = X AND is_active = true AND job_type = 'fulltime'
    op.create_index(
        'idx_job_positions_location_active_type',
        'job_positions',
        ['location', 'is_active', 'job_type']
    )


def downgrade() -> None:
    """Remove the composite indexes."""
    op.drop_index('idx_job_positions_location_active_type', table_name='job_positions')
    op.drop_index('idx_job_positions_company_active_type', table_name='job_positions')
    op.drop_index('idx_job_positions_active_type_posted', table_name='job_positions')
    op.drop_index('idx_job_positions_active_type_created', table_name='job_positions')
