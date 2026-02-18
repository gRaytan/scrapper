"""SavedFilter model for storing user's saved filter presets."""
from typing import Optional
from uuid import UUID

from sqlalchemy import ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin


class SavedFilter(Base, UUIDMixin, TimestampMixin):
    """SavedFilter model for storing user's saved filter configurations."""

    __tablename__ = "saved_filters"

    # Foreign key
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Filter name
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Filter configuration (JSON)
    # Structure: {
    #   "companies": ["uuid1", "uuid2"],
    #   "locations": ["Tel Aviv", "Remote"],
    #   "work_types": ["remote", "hybrid"],
    #   "departments": ["Engineering", "Product"],
    #   "seniority_levels": ["senior", "lead"],
    #   "search_query": "python developer"
    # }
    filters: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # Relationships
    user = relationship("User", back_populates="saved_filters")

    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'name', name='uq_user_saved_filter_name'),
        Index('ix_saved_filters_user_id', 'user_id'),
    )

    def __repr__(self) -> str:
        return f"<SavedFilter(id={self.id}, user_id={self.user_id}, name='{self.name}')>"

