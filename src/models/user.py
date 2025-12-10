"""User data model."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import Boolean, String, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
import bcrypt

from .base import Base, TimestampMixin, UUIDMixin


class User(Base, UUIDMixin, TimestampMixin):
    """User model for storing user information and preferences."""

    __tablename__ = "users"

    # Basic information
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    full_name: Mapped[Optional[str]] = mapped_column(String(255))

    # Authentication (temporary - will be replaced by OAuth)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255))

    # Phone number for MFA (future)
    phone_number: Mapped[Optional[str]] = mapped_column(String(20))
    phone_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Subscription (for future paying users)
    subscription_tier: Mapped[str] = mapped_column(
        String(50),
        default="free",
        nullable=False,
        index=True
    )  # free, basic, premium, enterprise

    # PayMe subscription ID
    payme_subscription_id: Mapped[Optional[str]] = mapped_column(String(255))

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

    def set_password(self, password: str) -> None:
        """Hash and set user password."""
        # Bcrypt has a 72-byte limit, truncate if necessary
        password_bytes = password.encode('utf-8')[:72]
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        self.password_hash = hashed.decode('utf-8')

    def verify_password(self, password: str) -> bool:
        """Verify password against hash."""
        if not self.password_hash:
            return False
        # Bcrypt has a 72-byte limit, truncate if necessary
        password_bytes = password.encode('utf-8')[:72]
        hash_bytes = self.password_hash.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hash_bytes)

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

