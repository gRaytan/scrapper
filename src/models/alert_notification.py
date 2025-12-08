"""Alert notification data model."""
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from sqlalchemy import String, Text, DateTime, ForeignKey, Index, Integer
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base, UUIDMixin, TimestampMixin


class AlertNotification(Base, UUIDMixin, TimestampMixin):
    """
    Alert notification model for tracking sent notifications.

    Each notification represents a batch of jobs to be sent for a single alert.
    Multiple jobs can be included in one notification (e.g., for digest emails).
    """

    __tablename__ = "alert_notifications"

    # Foreign keys
    alert_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("alerts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # List of job position IDs included in this notification
    job_position_ids: Mapped[List[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list
    )

    # Count of jobs for quick access without parsing JSONB
    job_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Notification details
    # sent_at is set when the notification is actually sent, not when created
    sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True
    )

    delivery_status: Mapped[str] = mapped_column(
        String(50),
        default='pending',
        nullable=False,
        index=True
    )  # pending, sent, delivered, failed, bounced

    delivery_method: Mapped[str] = mapped_column(String(50), nullable=False)  # email, sms, push, webhook

    # Error tracking
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(default=0, nullable=False)
    last_retry_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    alert = relationship("Alert", back_populates="notifications")
    user = relationship("User", back_populates="notifications")

    # Indexes for common queries
    __table_args__ = (
        Index('ix_alert_notifications_user_sent', 'user_id', 'sent_at'),
        Index('ix_alert_notifications_alert_sent', 'alert_id', 'sent_at'),
        Index('ix_alert_notifications_status_sent', 'delivery_status', 'sent_at'),
    )
    
    def __repr__(self) -> str:
        return f"<AlertNotification(id={self.id}, alert_id={self.alert_id}, job_count={self.job_count}, status='{self.delivery_status}')>"

    @property
    def is_successful(self) -> bool:
        """Check if notification was successfully delivered."""
        return self.delivery_status in ['sent', 'delivered']

    @property
    def is_failed(self) -> bool:
        """Check if notification failed."""
        return self.delivery_status in ['failed', 'bounced']

    @property
    def can_retry(self) -> bool:
        """Check if notification can be retried."""
        max_retries = 3
        return self.is_failed and self.retry_count < max_retries

    def get_job_position_uuids(self) -> List[UUID]:
        """Get job position IDs as UUID objects."""
        from uuid import UUID as PyUUID
        return [PyUUID(job_id) for job_id in self.job_position_ids]

    def add_job(self, job_id: UUID) -> None:
        """Add a job ID to the notification."""
        job_id_str = str(job_id)
        if job_id_str not in self.job_position_ids:
            self.job_position_ids = self.job_position_ids + [job_id_str]
            self.job_count = len(self.job_position_ids)

    def has_job(self, job_id: UUID) -> bool:
        """Check if a job ID is already in this notification."""
        return str(job_id) in self.job_position_ids

