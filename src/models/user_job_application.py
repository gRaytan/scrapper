"""User job application data model."""
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from sqlalchemy import String, Text, DateTime, ForeignKey, UniqueConstraint, Index, Integer
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

    # Comments (short comment visible in table)
    comments: Mapped[Optional[str]] = mapped_column(String(500))

    # Custom overrides (user can edit these to override job_position values)
    custom_title: Mapped[Optional[str]] = mapped_column(String(500))
    custom_company: Mapped[Optional[str]] = mapped_column(String(255))
    custom_location: Mapped[Optional[str]] = mapped_column(String(200))

    # Salary expectations/offer (user-entered)
    salary_min: Mapped[Optional[int]] = mapped_column(Integer)
    salary_max: Mapped[Optional[int]] = mapped_column(Integer)
    salary_currency: Mapped[Optional[str]] = mapped_column(String(10), default='USD')

    # Interview tracking
    next_interview_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)

    # Relationships
    user = relationship("User", back_populates="applications")
    job_position = relationship("JobPosition")
    interviews: Mapped[List["ApplicationInterview"]] = relationship(
        "ApplicationInterview",
        back_populates="application",
        cascade="all, delete-orphan",
        order_by="ApplicationInterview.scheduled_at"
    )

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


class ApplicationInterview(Base, UUIDMixin, TimestampMixin):
    """Interview record for a job application."""

    __tablename__ = "application_interviews"

    # Foreign key to application
    application_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("user_job_applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Interview details
    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )

    interview_type: Mapped[Optional[str]] = mapped_column(
        String(50)
    )  # phone, video, onsite, technical, behavioral, final, etc.

    interviewer: Mapped[Optional[str]] = mapped_column(String(255))

    location: Mapped[Optional[str]] = mapped_column(String(500))  # Can be URL for video calls

    notes: Mapped[Optional[str]] = mapped_column(Text)

    # Status: scheduled, completed, cancelled, rescheduled
    status: Mapped[str] = mapped_column(
        String(20),
        default='scheduled',
        nullable=False
    )

    # Feedback after interview
    feedback: Mapped[Optional[str]] = mapped_column(Text)

    # Relationship back to application
    application = relationship("UserJobApplication", back_populates="interviews")

    def __repr__(self) -> str:
        return f"<ApplicationInterview(id={self.id}, application_id={self.application_id}, scheduled_at={self.scheduled_at}, type='{self.interview_type}')>"

    @property
    def is_past(self) -> bool:
        """Check if interview is in the past."""
        return self.scheduled_at < datetime.now(self.scheduled_at.tzinfo)

    @property
    def is_upcoming(self) -> bool:
        """Check if interview is upcoming."""
        return self.scheduled_at >= datetime.now(self.scheduled_at.tzinfo) and self.status == 'scheduled'
