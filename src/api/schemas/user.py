"""Pydantic schemas for User API."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserPreferences(BaseModel):
    """User preferences schema."""
    notification_email: Optional[EmailStr] = None
    notifications_enabled: bool = True
    digest_mode: bool = False
    notification_frequency: str = Field(default="immediate", pattern="^(immediate|daily|weekly)$")


class UserBase(BaseModel):
    """Base user schema with common fields."""
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """Schema for creating a new user."""
    preferences: Optional[UserPreferences] = Field(default_factory=UserPreferences)


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    preferences: Optional[dict] = None
    is_active: Optional[bool] = None
    payme_subscription_id: Optional[str] = None


class UserStats(BaseModel):
    """User statistics."""
    active_alerts: int = 0
    total_applications: int = 0
    notifications_sent: int = 0


class UserResponse(UserBase):
    """Schema for user response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    is_active: bool
    subscription_tier: str
    payme_subscription_id: Optional[str] = None
    phone_number: Optional[str] = None
    phone_verified: bool
    last_login_at: Optional[datetime] = None
    preferences: dict
    created_at: datetime
    updated_at: datetime


class UserDetailResponse(UserResponse):
    """Schema for detailed user response with stats."""
    stats: Optional[UserStats] = None

