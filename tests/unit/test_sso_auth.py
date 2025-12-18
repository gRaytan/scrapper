"""Tests for SSO authentication endpoints."""
import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.api.app import app
from src.models.user import User
from src.auth.security import decode_token, create_access_token, create_refresh_token
from config.settings import settings


# Test client
client = TestClient(app)

# Test data
VALID_API_KEY = settings.internal_api_key
INVALID_API_KEY = "invalid-api-key"

SSO_REQUEST_GOOGLE = {
    "provider": "google",
    "provider_id": "google-user-123",
    "email": "testuser@example.com",
    "full_name": "Test User",
    "phone_number": "+972501234567"
}

SSO_REQUEST_LINKEDIN = {
    "provider": "linkedin",
    "provider_id": "linkedin-user-456",
    "email": "linkedin@example.com",
    "full_name": "LinkedIn User",
    "phone_number": None
}


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    with patch('src.auth.dependencies.db') as mock_db:
        mock_session = MagicMock(spec=Session)
        mock_db.get_session.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_db.get_session.return_value.__exit__ = MagicMock(return_value=False)
        yield mock_session


class TestSSOTokenEndpoint:
    """Tests for POST /api/v1/auth/sso/token endpoint."""

    def test_sso_token_missing_api_key(self):
        """Test that request without API key is rejected."""
        response = client.post(
            "/api/v1/auth/sso/token",
            json=SSO_REQUEST_GOOGLE
        )
        assert response.status_code == 422  # Missing required header

    def test_sso_token_invalid_api_key(self):
        """Test that request with invalid API key is rejected."""
        response = client.post(
            "/api/v1/auth/sso/token",
            json=SSO_REQUEST_GOOGLE,
            headers={"X-Internal-API-Key": INVALID_API_KEY}
        )
        assert response.status_code == 401
        assert "Invalid internal API key" in response.json()["detail"]

    def test_sso_token_creates_new_user(self, mock_db_session):
        """Test that SSO creates a new user when not found."""
        # Mock: no existing user found
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        # Mock refresh to set an ID
        def mock_refresh(user):
            if not hasattr(user, 'id') or user.id is None:
                user.id = uuid4()
        mock_db_session.refresh = mock_refresh
        
        response = client.post(
            "/api/v1/auth/sso/token",
            json=SSO_REQUEST_GOOGLE,
            headers={"X-Internal-API-Key": VALID_API_KEY}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
        assert "user" in data
        assert data["user"]["email"] == SSO_REQUEST_GOOGLE["email"]
        assert data["user"]["oauth_provider"] == "google"
        assert data["user"]["is_new_user"] == True
        
        # Verify user was added to session
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called()

    def test_sso_token_returns_existing_user(self, mock_db_session):
        """Test that SSO returns existing user when found by provider ID."""
        existing_user = User(
            id=uuid4(),
            email=SSO_REQUEST_GOOGLE["email"],
            full_name="Existing User",
            oauth_provider="google",
            oauth_provider_id=SSO_REQUEST_GOOGLE["provider_id"],
            is_active=True,
            phone_number="+972509999999",
            phone_verified=True,
            subscription_tier="premium",
            preferences={}
        )
        
        # Mock: user found by provider ID
        mock_db_session.query.return_value.filter.return_value.first.return_value = existing_user
        mock_db_session.refresh = MagicMock()
        
        response = client.post(
            "/api/v1/auth/sso/token",
            json=SSO_REQUEST_GOOGLE,
            headers={"X-Internal-API-Key": VALID_API_KEY}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["user"]["is_new_user"] == False
        assert data["user"]["email"] == existing_user.email
        
        # Verify no new user was added
        mock_db_session.add.assert_not_called()

    def test_sso_token_jwt_contains_correct_claims(self, mock_db_session):
        """Test that issued JWT contains correct claims."""
        user_id = uuid4()
        existing_user = User(
            id=user_id,
            email=SSO_REQUEST_GOOGLE["email"],
            full_name="Test User",
            oauth_provider="google",
            oauth_provider_id=SSO_REQUEST_GOOGLE["provider_id"],
            is_active=True,
            subscription_tier="free",
            preferences={}
        )
        
        mock_db_session.query.return_value.filter.return_value.first.return_value = existing_user
        mock_db_session.refresh = MagicMock()
        
        response = client.post(
            "/api/v1/auth/sso/token",
            json=SSO_REQUEST_GOOGLE,
            headers={"X-Internal-API-Key": VALID_API_KEY}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Decode and verify access token
        access_payload = decode_token(data["access_token"])
        assert access_payload["user_id"] == str(user_id)
        assert access_payload["email"] == SSO_REQUEST_GOOGLE["email"]
        assert access_payload["type"] == "access"
        
        # Decode and verify refresh token
        refresh_payload = decode_token(data["refresh_token"])
        assert refresh_payload["user_id"] == str(user_id)
        assert refresh_payload["type"] == "refresh"

    def test_sso_token_invalid_email(self):
        """Test that invalid email is rejected."""
        invalid_request = {
            **SSO_REQUEST_GOOGLE,
            "email": "not-an-email"
        }
        
        response = client.post(
            "/api/v1/auth/sso/token",
            json=invalid_request,
            headers={"X-Internal-API-Key": VALID_API_KEY}
        )
        
        assert response.status_code == 422  # Validation error

    def test_sso_token_missing_required_fields(self):
        """Test that missing required fields are rejected."""
        incomplete_request = {
            "provider": "google"
            # Missing provider_id and email
        }
        
        response = client.post(
            "/api/v1/auth/sso/token",
            json=incomplete_request,
            headers={"X-Internal-API-Key": VALID_API_KEY}
        )
        
        assert response.status_code == 422


class TestRefreshTokenEndpoint:
    """Tests for POST /api/v1/auth/refresh endpoint."""

    def test_refresh_token_valid(self):
        """Test refreshing with valid refresh token."""
        user_id = uuid4()
        refresh_token = create_refresh_token({
            "user_id": str(user_id),
            "email": "test@example.com"
        })
        
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_refresh_token_invalid(self):
        """Test refreshing with invalid token."""
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid-token"}
        )
        
        assert response.status_code == 401

    def test_refresh_token_with_access_token(self):
        """Test that access token cannot be used as refresh token."""
        access_token = create_access_token({
            "user_id": str(uuid4()),
            "email": "test@example.com"
        })
        
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": access_token}
        )
        
        assert response.status_code == 401


class TestMeEndpoint:
    """Tests for GET /api/v1/auth/me endpoint."""

    def test_me_without_token(self):
        """Test /me without authentication."""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_me_with_invalid_token(self):
        """Test /me with invalid token."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid-token"}
        )
        assert response.status_code == 401

    def test_me_with_valid_token(self, mock_db_session):
        """Test /me with valid token returns user info."""
        from datetime import datetime
        
        user_id = uuid4()
        user = User(
            id=user_id,
            email="test@example.com",
            full_name="Test User",
            oauth_provider="google",
            oauth_provider_id="google-123",
            is_active=True,
            subscription_tier="free",
            phone_verified=False,
            preferences={}
        )
        # Add required timestamp fields for response validation
        user.created_at = datetime.utcnow()
        user.updated_at = datetime.utcnow()
        
        mock_db_session.query.return_value.filter.return_value.first.return_value = user
        
        access_token = create_access_token({
            "user_id": str(user_id),
            "email": user.email
        })
        
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == user.email
