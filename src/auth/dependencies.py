"""FastAPI dependencies for JWT authentication."""
from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from src.auth.security import decode_token
from src.models.user import User
from src.storage.database import db
from config.settings import settings

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_db_session():
    """Dependency to get database session."""
    with db.get_session() as session:
        yield session


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_db_session)
) -> User:
    """
    Get the current authenticated user from JWT token.
    
    Args:
        token: JWT token from Authorization header
        db: Database session
        
    Returns:
        User object
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = decode_token(token)
        user_id_str: Optional[str] = payload.get("user_id")
        
        if user_id_str is None:
            raise credentials_exception
        
        # Convert string to UUID
        try:
            user_id = UUID(user_id_str)
        except ValueError:
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    
    # Get user from database
    user = session.query(User).filter(User.id == user_id).first()
    
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get the current active user.
    
    Args:
        current_user: User from get_current_user dependency
        
    Returns:
        Active user object
        
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    return current_user


async def require_internal_api_key(
    x_internal_api_key: str = Header(..., alias="X-Internal-API-Key")
) -> None:
    """
    Require valid internal API key for Node BFF endpoints.
    
    This dependency validates the X-Internal-API-Key header against
    the configured internal_api_key setting.
    
    Usage:
        @router.post("/sso/token", dependencies=[Depends(require_internal_api_key)])
        async def sso_token(...):
            ...
    
    Raises:
        HTTPException: If API key is missing or invalid
    """
    if not x_internal_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing internal API key",
        )
    
    if x_internal_api_key != settings.internal_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid internal API key",
        )
