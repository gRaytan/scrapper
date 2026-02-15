"""Add comments field and interviews table

Revision ID: g1h2i3j4k5l6
Revises: ff6879764b70
Create Date: 2026-02-15 10:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'g1h2i3j4k5l6'
down_revision: Union[str, None] = 'ff6879764b70'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add comments column to user_job_applications
    op.add_column('user_job_applications', sa.Column('comments', sa.String(500), nullable=True))
    
    # Create application_interviews table
    op.create_table(
        'application_interviews',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('application_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('user_job_applications.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column('interview_type', sa.String(50), nullable=True),
        sa.Column('interviewer', sa.String(255), nullable=True),
        sa.Column('location', sa.String(500), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='scheduled'),
        sa.Column('feedback', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
    )


def downgrade() -> None:
    # Drop application_interviews table
    op.drop_table('application_interviews')
    
    # Remove comments column from user_job_applications
    op.drop_column('user_job_applications', 'comments')
