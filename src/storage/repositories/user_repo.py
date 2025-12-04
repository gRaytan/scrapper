"""User repository for database operations."""
import logging
from typing import Optional, List
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import and_

from src.models.user import User

logger = logging.getLogger(__name__)


class UserRepository:
    """Repository for User CRUD operations."""
    
    def __init__(self, session: Session):
        """Initialize repository with database session."""
        self.session = session
    
    def create(self, user_data: dict) -> User:
        """
        Create a new user.
        
        Args:
            user_data: Dictionary with user fields
            
        Returns:
            Created User instance
        """
        user = User(**user_data)
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        logger.info(f"Created user: {user.email} ({user.id})")
        return user
    
    def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID."""
        return self.session.query(User).filter(User.id == user_id).first()
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return self.session.query(User).filter(User.email == email).first()
    
    def get_all(self, is_active: Optional[bool] = None, limit: Optional[int] = None) -> List[User]:
        """
        Get all users.
        
        Args:
            is_active: Filter by active status (None = all)
            limit: Maximum number of results
            
        Returns:
            List of User instances
        """
        query = self.session.query(User)
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def update(self, user_id: UUID, update_data: dict) -> Optional[User]:
        """
        Update user.
        
        Args:
            user_id: User UUID
            update_data: Dictionary with fields to update
            
        Returns:
            Updated User instance or None if not found
        """
        user = self.get_by_id(user_id)
        if not user:
            logger.warning(f"User not found: {user_id}")
            return None
        
        for key, value in update_data.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        self.session.commit()
        self.session.refresh(user)
        logger.info(f"Updated user: {user.email} ({user.id})")
        return user
    
    def delete(self, user_id: UUID) -> bool:
        """
        Delete user (hard delete).
        
        Args:
            user_id: User UUID
            
        Returns:
            True if deleted, False if not found
        """
        user = self.get_by_id(user_id)
        if not user:
            logger.warning(f"User not found: {user_id}")
            return False
        
        self.session.delete(user)
        self.session.commit()
        logger.info(f"Deleted user: {user.email} ({user_id})")
        return True
    
    def soft_delete(self, user_id: UUID) -> Optional[User]:
        """
        Soft delete user (mark as inactive).
        
        Args:
            user_id: User UUID
            
        Returns:
            Updated User instance or None if not found
        """
        return self.update(user_id, {"is_active": False})
    
    def get_or_create(self, email: str, defaults: dict) -> tuple[User, bool]:
        """
        Get existing user or create new one.
        
        Args:
            email: User email
            defaults: Default values for creation
            
        Returns:
            Tuple of (User instance, created boolean)
        """
        user = self.get_by_email(email)
        if user:
            return user, False
        
        user_data = {"email": email, **defaults}
        user = self.create(user_data)
        return user, True

