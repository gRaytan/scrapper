"""User job interaction model for star/archive functionality."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin


class UserJobInteraction(Base, UUIDMixin, TimestampMixin):
    """Model for tracking user interactions with jobs (star/archive)."""

    __tablename__ = "user_job_interactions"

    # Foreign keys
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    job_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("job_positions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Interaction flags
    is_starred: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Timestamps for when actions occurred
    starred_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    archived_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    user = relationship("User", back_populates="job_interactions")
    job = relationship("JobPosition", back_populates="user_interactions")

    # Indexes and constraints
    __table_args__ = (
        Index(
            "ix_user_job_interactions_user_starred",
            "user_id", "is_starred",
            postgresql_where="is_starred = true"
        ),
        Index(
            "ix_user_job_interactions_user_archived",
            "user_id", "is_archived",
            postgresql_where="is_archived = true"
        ),
        # Unique constraint on user_id + job_id
        {"sqlite_autoincrement": True},
    )

    def __repr__(self) -> str:
        return f"<UserJobInteraction(user_id={self.user_id}, job_id={self.job_id}, starred={self.is_starred}, archived={self.is_archived})>"

