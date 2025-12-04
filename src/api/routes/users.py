"""User API endpoints."""
import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session

from src.storage.database import db
from src.services.user_service import UserService
from src.auth.dependencies import get_current_active_user
from src.models.user import User
from src.api.schemas.user import (
    UserUpdate,
    UserResponse,
    UserDetailResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def get_db_session():
    """Dependency to get database session."""
    with db.get_session() as session:
        yield session


@router.get("/me", response_model=UserDetailResponse)
def get_current_user_profile(
    include_stats: bool = False,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_db_session)
):
    """
    Get current user's profile.

    - **include_stats**: Include user statistics (default: false)

    Requires JWT authentication.
    """
    try:
        service = UserService(session)
        result = service.get_user(current_user.id, include_stats=include_stats)

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        if include_stats and isinstance(result, dict):
            return UserDetailResponse(**result)

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user"
        )


@router.get("/{user_id}", response_model=UserDetailResponse)
def get_user(
    user_id: UUID,
    include_stats: bool = False,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_db_session)
):
    """
    Get user by ID.

    - **user_id**: User UUID
    - **include_stats**: Include user statistics (default: false)

    Users can only access their own profile.
    Requires JWT authentication.
    """
    # Users can only access their own profile
    if user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own profile"
        )
    try:
        service = UserService(session)
        result = service.get_user(user_id, include_stats=include_stats)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found"
            )
        
        if include_stats and isinstance(result, dict):
            return UserDetailResponse(
                **result["user"].__dict__,
                stats=result["stats"]
            )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user"
        )


@router.patch("/me", response_model=UserResponse)
def update_current_user(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_db_session)
):
    """
    Update current user's profile.

    - **full_name**: Updated full name (optional)
    - **preferences**: Updated preferences (optional)

    Requires JWT authentication.
    """
    try:
        service = UserService(session)
        user = service.update_user(current_user.id, update_data)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: UUID,
    update_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_db_session)
):
    """
    Update user by ID.

    - **user_id**: User UUID
    - **full_name**: Updated full name (optional)
    - **preferences**: Updated preferences (optional)

    Users can only update their own profile.
    Requires JWT authentication.
    """
    # Users can only update their own profile
    if user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own profile"
        )

    try:
        service = UserService(session)
        user = service.update_user(user_id, update_data)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found"
            )

        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_current_user(
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_db_session)
):
    """
    Delete current user's account.

    Note: This will cascade delete all user's alerts and applications.
    Requires JWT authentication.
    """
    try:
        service = UserService(session)
        success = service.delete_user(current_user.id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: UUID,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_db_session)
):
    """
    Delete user by ID.

    - **user_id**: User UUID

    Users can only delete their own account.
    Note: This will cascade delete all user's alerts and applications.
    Requires JWT authentication.
    """
    # Users can only delete their own account
    if user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own account"
        )
    try:
        service = UserService(session)
        deleted = service.delete_user(user_id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found"
            )
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )

