"""User job application data model."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import String, Text, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin


class UserJobApplication(Base, UUIDMixin, TimestampMixin):
    """User job application model for tracking user applications to job positions."""
    
    __tablename__ = "user_job_applications"
    
    # Foreign keys
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    job_position_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("job_positions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Application status
    status: Mapped[str] = mapped_column(
        String(50),
        default='interested',
        nullable=False,
        index=True
    )  # interested, applied, interviewing, offered, accepted, rejected, withdrawn
    
    # Application date
    applied_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text)
    
    # Relationships
    user = relationship("User", back_populates="applications")
    job_position = relationship("JobPosition")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'job_position_id', name='uq_user_job'),
        Index('ix_user_job_applications_user_status', 'user_id', 'status'),
    )
    
    def __repr__(self) -> str:
        return f"<UserJobApplication(id={self.id}, user_id={self.user_id}, job_position_id={self.job_position_id}, status='{self.status}')>"
    
    @property
    def is_active(self) -> bool:
        """Check if application is in an active state."""
        active_statuses = ['interested', 'applied', 'interviewing', 'offered']
        return self.status in active_statuses
    
    @property
    def is_closed(self) -> bool:
        """Check if application is in a closed state."""
        closed_statuses = ['accepted', 'rejected', 'withdrawn']
        return self.status in closed_statuses

