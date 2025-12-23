"""Add personalized jobs tables

Revision ID: a1b2c3d4e5f6
Revises: edb29ef49b3e
Create Date: 2025-12-23 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'edb29ef49b3e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create user_job_interactions table
    op.create_table(
        'user_job_interactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('is_starred', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_archived', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('starred_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('archived_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['job_id'], ['job_positions.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id', 'job_id', name='uq_user_job_interactions_user_job')
    )
    
    # Create indexes for user_job_interactions
    op.create_index('ix_user_job_interactions_user_id', 'user_job_interactions', ['user_id'])
    op.create_index('ix_user_job_interactions_job_id', 'user_job_interactions', ['job_id'])
    op.create_index(
        'ix_user_job_interactions_user_starred',
        'user_job_interactions',
        ['user_id', 'is_starred'],
        postgresql_where=sa.text('is_starred = true')
    )
    op.create_index(
        'ix_user_job_interactions_user_archived',
        'user_job_interactions',
        ['user_id', 'is_archived'],
        postgresql_where=sa.text('is_archived = true')
    )
    
    # Create job_embeddings table
    op.create_table(
        'job_embeddings',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title_embedding', sa.LargeBinary(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['job_id'], ['job_positions.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('job_id', name='uq_job_embeddings_job_id')
    )
    
    # Create index for job_embeddings
    op.create_index('ix_job_embeddings_job_id', 'job_embeddings', ['job_id'])


def downgrade() -> None:
    # Drop job_embeddings table
    op.drop_index('ix_job_embeddings_job_id', table_name='job_embeddings')
    op.drop_table('job_embeddings')
    
    # Drop user_job_interactions table
    op.drop_index('ix_user_job_interactions_user_archived', table_name='user_job_interactions')
    op.drop_index('ix_user_job_interactions_user_starred', table_name='user_job_interactions')
    op.drop_index('ix_user_job_interactions_job_id', table_name='user_job_interactions')
    op.drop_index('ix_user_job_interactions_user_id', table_name='user_job_interactions')
    op.drop_table('user_job_interactions')

