"""User data model."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import Boolean, String, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin


class User(Base, UUIDMixin, TimestampMixin):
    """User model for storing user information and preferences."""
    
    __tablename__ = "users"
    
    # Basic information
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    full_name: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    
    # Activity tracking
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # User preferences (stored as JSON)
    preferences: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    
    # Relationships
    alerts = relationship("Alert", back_populates="user", cascade="all, delete-orphan")
    applications = relationship("UserJobApplication", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("AlertNotification", back_populates="user")
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}')>"
    
    @property
    def notification_email(self) -> str:
        """Get notification email from preferences or use primary email."""
        return self.preferences.get("notification_email", self.email)
    
    @property
    def notification_enabled(self) -> bool:
        """Check if notifications are enabled."""
        return self.preferences.get("notifications_enabled", True)
    
    @property
    def digest_mode(self) -> bool:
        """Check if user prefers daily digest over immediate notifications."""
        return self.preferences.get("digest_mode", False)

