"""add_saved_filters_table

Revision ID: 7cbf2854c6fd
Revises: h2i3j4k5l6m7
Create Date: 2026-02-17 16:52:39.536987

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '7cbf2854c6fd'
down_revision: Union[str, None] = 'h2i3j4k5l6m7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create saved_filters table
    op.create_table('saved_filters',
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('filters', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'name', name='uq_user_saved_filter_name')
    )
    op.create_index(op.f('ix_saved_filters_user_id'), 'saved_filters', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_saved_filters_user_id'), table_name='saved_filters')
    op.drop_table('saved_filters')
