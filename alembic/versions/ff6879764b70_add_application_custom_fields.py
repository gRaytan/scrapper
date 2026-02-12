"""add_application_custom_fields

Revision ID: ff6879764b70
Revises: e3b0ad7694c4
Create Date: 2026-02-12 20:42:25.127248

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ff6879764b70'
down_revision: Union[str, None] = 'e3b0ad7694c4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add custom fields to user_job_applications for user overrides and tracking
    op.add_column('user_job_applications', sa.Column('custom_title', sa.String(length=500), nullable=True))
    op.add_column('user_job_applications', sa.Column('custom_company', sa.String(length=255), nullable=True))
    op.add_column('user_job_applications', sa.Column('custom_location', sa.String(length=200), nullable=True))
    op.add_column('user_job_applications', sa.Column('salary_min', sa.Integer(), nullable=True))
    op.add_column('user_job_applications', sa.Column('salary_max', sa.Integer(), nullable=True))
    op.add_column('user_job_applications', sa.Column('salary_currency', sa.String(length=10), nullable=True))
    op.add_column('user_job_applications', sa.Column('next_interview_at', sa.DateTime(timezone=True), nullable=True))
    op.create_index(op.f('ix_user_job_applications_next_interview_at'), 'user_job_applications', ['next_interview_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_user_job_applications_next_interview_at'), table_name='user_job_applications')
    op.drop_column('user_job_applications', 'next_interview_at')
    op.drop_column('user_job_applications', 'salary_currency')
    op.drop_column('user_job_applications', 'salary_max')
    op.drop_column('user_job_applications', 'salary_min')
    op.drop_column('user_job_applications', 'custom_location')
    op.drop_column('user_job_applications', 'custom_company')
    op.drop_column('user_job_applications', 'custom_title')
