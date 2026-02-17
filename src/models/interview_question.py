"""Interview Question data model."""
from typing import Optional
from uuid import UUID

from sqlalchemy import String, Text, Integer, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin


class InterviewQuestion(Base, UUIDMixin, TimestampMixin):
    """Interview question model for storing interview questions and answers."""

    __tablename__ = "interview_questions"

    # Foreign keys
    company_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Question details
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    difficulty: Mapped[Optional[str]] = mapped_column(String(50))  # Easy, Medium, Hard
    interview_stage: Mapped[Optional[str]] = mapped_column(String(100))  # Phone Screen, Technical, Onsite, HR

    # Answers stored as JSON array
    # Format: [{"id": "uuid", "text": "...", "user_id": "uuid", "user_name": "...", "created_at": "...", "upvotes": 0}]
    answers: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    # Engagement metrics
    upvotes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    company = relationship("Company", backref="interview_questions")
    user = relationship("User", backref="interview_questions")

    def __repr__(self) -> str:
        return f"<InterviewQuestion(id={self.id}, role='{self.role}', company_id={self.company_id})>"

    @property
    def answer_count(self) -> int:
        """Get the number of answers."""
        return len(self.answers) if self.answers else 0

