"""User service for business logic."""
import base64
import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

import numpy as np
from sqlalchemy.orm import Session

from src.storage.repositories.user_repo import UserRepository
from src.storage.repositories.alert_repo import AlertRepository
from src.models.alert import Alert
from src.models.alert_notification import AlertNotification
from src.models.user_job_application import UserJobApplication
from src.api.schemas.user import UserCreate, UserUpdate, UserStats

logger = logging.getLogger(__name__)


class UserService:
    """Service for user-related business logic."""
    
    def __init__(self, session: Session):
        """Initialize service with database session."""
        self.session = session
        self.user_repo = UserRepository(session)
        self.alert_repo = AlertRepository(session)
    
    def create_user(self, user_data: UserCreate) -> dict:
        """
        Create a new user.
        
        Args:
            user_data: User creation data
            
        Returns:
            Created user as dict
            
        Raises:
            ValueError: If email already exists
        """
        # Check if email already exists
        existing_user = self.user_repo.get_by_email(user_data.email)
        if existing_user:
            raise ValueError(f"User with email {user_data.email} already exists")
        
        # Prepare user data
        user_dict = {
            "email": user_data.email,
            "full_name": user_data.full_name,
            "preferences": user_data.preferences.model_dump() if user_data.preferences else {},
        }
        
        # Create user
        user = self.user_repo.create(user_dict)
        return user
    
    def get_user(self, user_id: UUID, include_stats: bool = False) -> Optional[dict]:
        """
        Get user by ID.
        
        Args:
            user_id: User UUID
            include_stats: Whether to include user statistics
            
        Returns:
            User data with optional stats, or None if not found
        """
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return None
        
        if include_stats:
            stats = self._get_user_stats(user_id)
            return {"user": user, "stats": stats}
        
        return user
    
    def update_user(self, user_id: UUID, update_data: UserUpdate) -> Optional[dict]:
        """
        Update user.

        Args:
            user_id: User UUID
            update_data: Update data

        Returns:
            Updated user or None if not found
        """
        # Prepare update dict (only include non-None values)
        update_dict = {}
        if update_data.full_name is not None:
            update_dict["full_name"] = update_data.full_name
        if update_data.phone_number is not None:
            update_dict["phone_number"] = update_data.phone_number
        if update_data.preferences is not None:
            # Check if job_title is being updated - compute embedding for semantic matching
            preferences = update_data.preferences
            job_title = preferences.get("job_title", "") if isinstance(preferences, dict) else ""

            if job_title:
                # Compute query embedding for personalized feed
                try:
                    from src.services.embedding_service import EmbeddingService
                    embedding_service = EmbeddingService()
                    query_embedding = embedding_service.encode(job_title)

                    # Store as base64 for JSON compatibility
                    preferences["query_embedding"] = base64.b64encode(
                        query_embedding.astype(np.float32).tobytes()
                    ).decode("utf-8")
                    preferences["updated_at"] = datetime.utcnow().isoformat() + "Z"
                    logger.info(f"Computed query embedding for user {user_id} with job_title: {job_title}")
                except Exception as e:
                    logger.warning(f"Failed to compute query embedding for user {user_id}: {e}")

            update_dict["preferences"] = preferences
        if update_data.is_active is not None:
            update_dict["is_active"] = update_data.is_active
        if update_data.payme_subscription_id is not None:
            update_dict["payme_subscription_id"] = update_data.payme_subscription_id

        if not update_dict:
            # No updates provided
            return self.user_repo.get_by_id(user_id)

        return self.user_repo.update(user_id, update_dict)
    
    def delete_user(self, user_id: UUID) -> bool:
        """
        Delete user (cascade deletes alerts and applications).
        
        Args:
            user_id: User UUID
            
        Returns:
            True if deleted, False if not found
        """
        return self.user_repo.delete(user_id)
    
    def _get_user_stats(self, user_id: UUID) -> UserStats:
        """
        Get user statistics.
        
        Args:
            user_id: User UUID
            
        Returns:
            User statistics
        """
        # Count active alerts
        active_alerts = self.session.query(Alert).filter_by(
            user_id=user_id, is_active=True
        ).count()
        
        # Count total applications
        total_applications = self.session.query(UserJobApplication).filter_by(
            user_id=user_id
        ).count()
        
        # Count notifications sent
        notifications_sent = self.session.query(AlertNotification).filter_by(
            user_id=user_id
        ).count()
        
        return UserStats(
            active_alerts=active_alerts,
            total_applications=total_applications,
            notifications_sent=notifications_sent,
        )

