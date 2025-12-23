"""Authentication API routes."""
from datetime import datetime
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.schemas.auth import (
    Token,
    RefreshTokenRequest,
    SSOTokenRequest,
    SSOTokenResponse,
    SSOUserInfo,
    DevTokenRequest,
)
from src.api.schemas.user import UserResponse
from src.auth.security import create_access_token, create_refresh_token, decode_token
from src.auth.dependencies import get_current_active_user, get_db_session, require_internal_api_key
from src.models.user import User
from config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/sso/token",
    response_model=SSOTokenResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_internal_api_key)],
)
async def sso_token(
    sso_data: SSOTokenRequest,
    db: Session = Depends(get_db_session)
):
    """
    Issue JWT tokens after SSO authentication.
    
    This endpoint is called by the Node BFF after successful OAuth + MFA.
    It creates or updates the user and returns JWT tokens.
    
    **Security**: Requires X-Internal-API-Key header.
    
    - **provider**: OAuth provider ('google' or 'linkedin')
    - **provider_id**: User ID from OAuth provider
    - **email**: User email from OAuth provider
    - **full_name**: Optional user full name
    - **phone_number**: Optional phone number (verified via MFA)
    
    Returns JWT access and refresh tokens.
    """
    is_new_user = False
    
    # Try to find existing user by provider ID first
    user = db.query(User).filter(
        User.oauth_provider == sso_data.provider,
        User.oauth_provider_id == sso_data.provider_id
    ).first()
    
    if not user:
        # Try to find by email (user might have registered before SSO)
        user = db.query(User).filter(User.email == sso_data.email).first()
        
        if user:
            # Link OAuth to existing account
            user.oauth_provider = sso_data.provider
            user.oauth_provider_id = sso_data.provider_id
            logger.info(f"Linked {sso_data.provider} OAuth to existing user: {user.email}")
        else:
            # Create new user
            user = User(
                email=sso_data.email,
                full_name=sso_data.full_name,
                oauth_provider=sso_data.provider,
                oauth_provider_id=sso_data.provider_id,
                is_active=True,
                subscription_tier="free",
                phone_verified=bool(sso_data.phone_number),  # MFA verified phone
                phone_number=sso_data.phone_number,
                preferences={}
            )
            db.add(user)
            is_new_user = True
            logger.info(f"Created new user via {sso_data.provider} SSO: {sso_data.email}")
    
    # Update user info if provided
    if sso_data.full_name and not user.full_name:
        user.full_name = sso_data.full_name
    
    if sso_data.phone_number and not user.phone_number:
        user.phone_number = sso_data.phone_number
        user.phone_verified = True  # Phone was verified via MFA
    
    # Update last login
    user.last_login_at = datetime.utcnow()
    
    db.commit()
    db.refresh(user)
    
    # Create tokens
    token_data = {
        "user_id": user.id,
        "email": user.email,
        "oauth_provider": user.oauth_provider,
    }
    
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    return SSOTokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.jwt_access_token_expire_minutes * 60,
        user=SSOUserInfo(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            oauth_provider=user.oauth_provider,
            is_new_user=is_new_user,
        )
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db_session)
):
    """
    Refresh access token using refresh token.
    
    Returns new access and refresh tokens.
    """
    try:
        payload = decode_token(refresh_data.refresh_token)
        
        # Verify it's a refresh token
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        user_id = payload.get("user_id")
        email = payload.get("email")
        
        if not user_id or not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )

    # Create new tokens
    token_data = {
        "user_id": user_id,
        "email": email
    }

    access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)

    return Token(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer"
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current authenticated user information.

    Requires valid JWT token in Authorization header.
    """
    return current_user


@router.post(
    "/dev/token",
    response_model=SSOTokenResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=True,  # Show in Swagger
)
async def dev_token(
    dev_data: DevTokenRequest,
    db: Session = Depends(get_db_session)
):
    """
    🔧 **Quick Token** - Get JWT tokens for Swagger testing.

    This endpoint allows you to get JWT tokens without going through OAuth/SSO.
    Useful for testing API endpoints in Swagger UI.

    **Usage in Swagger:**
    1. Enter any email address
    2. Click Execute
    3. Copy the access_token
    4. Click "Authorize" button at the top
    5. Paste the token and click "Authorize"
    """

    is_new_user = False

    # Find or create user
    user = db.query(User).filter(User.email == dev_data.email).first()

    if not user:
        # Create dev user
        user = User(
            email=dev_data.email,
            full_name=f"Dev User ({dev_data.email.split('@')[0]})",
            oauth_provider="dev",
            oauth_provider_id=f"dev-{dev_data.email}",
            is_active=True,
            subscription_tier="free",
            phone_verified=False,
            preferences={}
        )
        db.add(user)
        is_new_user = True
        logger.info(f"Created dev user: {dev_data.email}")

    # Update last login
    user.last_login_at = datetime.utcnow()

    db.commit()
    db.refresh(user)

    # Create tokens
    token_data = {
        "user_id": user.id,
        "email": user.email,
        "oauth_provider": user.oauth_provider or "dev",
    }

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return SSOTokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.jwt_access_token_expire_minutes * 60,
        user=SSOUserInfo(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            oauth_provider=user.oauth_provider or "dev",
            is_new_user=is_new_user,
        )
    )
