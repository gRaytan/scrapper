"""Pydantic schemas for Authentication API."""
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    """Schema for user registration."""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100, description="Password must be at least 8 characters")
    full_name: Optional[str] = Field(None, max_length=255)


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class Token(BaseModel):
    """Schema for token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for token payload data."""
    user_id: UUID
    email: str


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request."""
    refresh_token: str


class PasswordChange(BaseModel):
    """Schema for password change."""
    old_password: str
    new_password: str = Field(..., min_length=8, max_length=100)


class PasswordReset(BaseModel):
    """Schema for password reset."""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation."""
    token: str
    new_password: str = Field(..., min_length=8, max_length=100)


class SSOTokenRequest(BaseModel):
    """Schema for SSO token request from Node BFF."""
    provider: str = Field(..., description="OAuth provider: 'google' or 'linkedin'")
    provider_id: str = Field(..., description="User ID from OAuth provider")
    email: EmailStr = Field(..., description="User email from OAuth provider")
    full_name: Optional[str] = Field(None, max_length=255, description="User full name")
    phone_number: Optional[str] = Field(None, max_length=20, description="User phone number (verified via MFA)")


class SSOTokenResponse(BaseModel):
    """Schema for SSO token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Access token expiry in seconds")
    user: "SSOUserInfo"


class SSOUserInfo(BaseModel):
    """User info returned after SSO authentication."""
    id: UUID
    email: str
    full_name: Optional[str]
    oauth_provider: str
    is_new_user: bool = Field(..., description="True if user was just created")


# Required for forward reference
SSOTokenResponse.model_rebuild()
