"""Alert notification data model."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import String, Text, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base, UUIDMixin, TimestampMixin


class AlertNotification(Base, UUIDMixin, TimestampMixin):
    """Alert notification model for tracking sent notifications."""
    
    __tablename__ = "alert_notifications"
    
    # Foreign keys
    alert_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("alerts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    job_position_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("job_positions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
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
    job_position = relationship("JobPosition")
    user = relationship("User", back_populates="notifications")
    
    # Indexes for common queries
    __table_args__ = (
        Index('ix_alert_notifications_user_sent', 'user_id', 'sent_at'),
        Index('ix_alert_notifications_alert_sent', 'alert_id', 'sent_at'),
        Index('ix_alert_notifications_status_sent', 'delivery_status', 'sent_at'),
        # Unique constraint to prevent duplicate notifications for same alert+job
        Index('ix_alert_notifications_alert_job', 'alert_id', 'job_position_id', unique=True),
    )
    
    def __repr__(self) -> str:
        return f"<AlertNotification(id={self.id}, alert_id={self.alert_id}, job_position_id={self.job_position_id}, status='{self.delivery_status}')>"
    
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

