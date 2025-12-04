"""User API endpoints."""
import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session

from src.storage.database import db
from src.services.user_service import UserService
from src.api.schemas.user import (
    UserCreate,
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


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_data: UserCreate,
    session: Session = Depends(get_db_session)
):
    """
    Create a new user.
    
    - **email**: User email (must be unique)
    - **full_name**: User's full name (optional)
    - **preferences**: User preferences (optional)
    """
    try:
        service = UserService(session)
        user = service.create_user(user_data)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )


@router.get("/{user_id}", response_model=UserDetailResponse)
def get_user(
    user_id: UUID,
    include_stats: bool = False,
    session: Session = Depends(get_db_session)
):
    """
    Get user by ID.
    
    - **user_id**: User UUID
    - **include_stats**: Include user statistics (default: false)
    """
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


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: UUID,
    update_data: UserUpdate,
    session: Session = Depends(get_db_session)
):
    """
    Update user.
    
    - **user_id**: User UUID
    - **full_name**: Updated full name (optional)
    - **preferences**: Updated preferences (optional)
    - **is_active**: Updated active status (optional)
    """
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


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: UUID,
    session: Session = Depends(get_db_session)
):
    """
    Delete user.
    
    - **user_id**: User UUID
    
    Note: This will cascade delete all user's alerts and applications.
    """
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

