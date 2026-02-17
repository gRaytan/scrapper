"""Saved Filters API endpoints."""
import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from src.storage.database import db
from src.auth.dependencies import get_current_active_user
from src.models.user import User
from src.models.saved_filter import SavedFilter
from src.api.schemas.saved_filter import (
    SavedFilterCreate,
    SavedFilterUpdate,
    SavedFilterResponse,
    SavedFilterListResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def get_db_session():
    """Dependency to get database session."""
    with db.get_session() as session:
        yield session


@router.get("", response_model=SavedFilterListResponse)
def list_saved_filters(
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_db_session)
):
    """
    List all saved filters for the current user.
    
    Requires JWT authentication.
    """
    try:
        filters = session.query(SavedFilter).filter(
            SavedFilter.user_id == current_user.id
        ).order_by(SavedFilter.created_at.desc()).all()
        
        return SavedFilterListResponse(
            filters=filters,
            total=len(filters)
        )
    except Exception as e:
        logger.error(f"Error listing saved filters: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list saved filters"
        )


@router.post("", response_model=SavedFilterResponse, status_code=status.HTTP_201_CREATED)
def create_saved_filter(
    filter_data: SavedFilterCreate,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_db_session)
):
    """
    Create a new saved filter.
    
    - **name**: Name for the filter preset (max 100 chars)
    - **filters**: Filter configuration object
    
    Requires JWT authentication.
    """
    try:
        saved_filter = SavedFilter(
            user_id=current_user.id,
            name=filter_data.name,
            filters=filter_data.filters.model_dump()
        )
        session.add(saved_filter)
        session.commit()
        session.refresh(saved_filter)
        
        return saved_filter
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A filter with name '{filter_data.name}' already exists"
        )
    except Exception as e:
        session.rollback()
        logger.error(f"Error creating saved filter: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create saved filter"
        )


@router.get("/{filter_id}", response_model=SavedFilterResponse)
def get_saved_filter(
    filter_id: UUID,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_db_session)
):
    """
    Get a saved filter by ID.
    
    Requires JWT authentication.
    """
    saved_filter = session.query(SavedFilter).filter(
        SavedFilter.id == filter_id,
        SavedFilter.user_id == current_user.id
    ).first()
    
    if not saved_filter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved filter not found"
        )
    
    return saved_filter


@router.patch("/{filter_id}", response_model=SavedFilterResponse)
def update_saved_filter(
    filter_id: UUID,
    update_data: SavedFilterUpdate,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_db_session)
):
    """
    Update a saved filter.
    
    Requires JWT authentication.
    """
    saved_filter = session.query(SavedFilter).filter(
        SavedFilter.id == filter_id,
        SavedFilter.user_id == current_user.id
    ).first()
    
    if not saved_filter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved filter not found"
        )
    
    try:
        if update_data.name is not None:
            saved_filter.name = update_data.name
        if update_data.filters is not None:
            saved_filter.filters = update_data.filters.model_dump()
        
        session.commit()
        session.refresh(saved_filter)
        
        return saved_filter
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A filter with name '{update_data.name}' already exists"
        )
    except Exception as e:
        session.rollback()
        logger.error(f"Error updating saved filter: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update saved filter"
        )


@router.delete("/{filter_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_saved_filter(
    filter_id: UUID,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_db_session)
):
    """
    Delete a saved filter.
    
    Requires JWT authentication.
    """
    saved_filter = session.query(SavedFilter).filter(
        SavedFilter.id == filter_id,
        SavedFilter.user_id == current_user.id
    ).first()
    
    if not saved_filter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved filter not found"
        )
    
    try:
        session.delete(saved_filter)
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Error deleting saved filter: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete saved filter"
        )

