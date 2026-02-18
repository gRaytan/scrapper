"""add_interview_questions_table

Revision ID: i3j4k5l6m7n8
Revises: 7cbf2854c6fd
Create Date: 2026-02-17 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'i3j4k5l6m7n8'
down_revision: Union[str, None] = '7cbf2854c6fd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create interview_questions table
    op.create_table('interview_questions',
        sa.Column('company_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('role', sa.String(length=255), nullable=False),
        sa.Column('difficulty', sa.String(length=50), nullable=True),
        sa.Column('interview_stage', sa.String(length=100), nullable=True),
        sa.Column('answers', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('upvotes', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_interview_questions_company_id'), 'interview_questions', ['company_id'], unique=False)
    op.create_index(op.f('ix_interview_questions_role'), 'interview_questions', ['role'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_interview_questions_role'), table_name='interview_questions')
    op.drop_index(op.f('ix_interview_questions_company_id'), table_name='interview_questions')
    op.drop_table('interview_questions')

