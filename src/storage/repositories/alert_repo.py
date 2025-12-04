"""Alert repository for database operations."""
import logging
from typing import Optional, List
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import and_

from src.models.alert import Alert

logger = logging.getLogger(__name__)


class AlertRepository:
    """Repository for Alert CRUD operations."""
    
    def __init__(self, session: Session):
        """Initialize repository with database session."""
        self.session = session
    
    def create(self, alert_data: dict) -> Alert:
        """
        Create a new alert.
        
        Args:
            alert_data: Dictionary with alert fields
            
        Returns:
            Created Alert instance
        """
        alert = Alert(**alert_data)
        self.session.add(alert)
        self.session.commit()
        self.session.refresh(alert)
        logger.info(f"Created alert: {alert.name} for user {alert.user_id} ({alert.id})")
        return alert
    
    def get_by_id(self, alert_id: UUID) -> Optional[Alert]:
        """Get alert by ID."""
        return self.session.query(Alert).filter(Alert.id == alert_id).first()
    
    def get_by_user(
        self,
        user_id: UUID,
        is_active: Optional[bool] = None,
        limit: Optional[int] = None
    ) -> List[Alert]:
        """
        Get all alerts for a user.
        
        Args:
            user_id: User UUID
            is_active: Filter by active status
            limit: Maximum number of results
            
        Returns:
            List of Alert instances
        """
        query = self.session.query(Alert).filter(Alert.user_id == user_id)
        
        if is_active is not None:
            query = query.filter(Alert.is_active == is_active)
        
        query = query.order_by(Alert.created_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def get_all_active(self) -> List[Alert]:
        """Get all active alerts across all users."""
        return self.session.query(Alert).filter(Alert.is_active == True).all()
    
    def update(self, alert_id: UUID, update_data: dict) -> Optional[Alert]:
        """
        Update alert.
        
        Args:
            alert_id: Alert UUID
            update_data: Dictionary with fields to update
            
        Returns:
            Updated Alert instance or None if not found
        """
        alert = self.get_by_id(alert_id)
        if not alert:
            logger.warning(f"Alert not found: {alert_id}")
            return None
        
        for key, value in update_data.items():
            if hasattr(alert, key):
                setattr(alert, key, value)
        
        self.session.commit()
        self.session.refresh(alert)
        logger.info(f"Updated alert: {alert.name} ({alert.id})")
        return alert
    
    def delete(self, alert_id: UUID) -> bool:
        """
        Delete alert.
        
        Args:
            alert_id: Alert UUID
            
        Returns:
            True if deleted, False if not found
        """
        alert = self.get_by_id(alert_id)
        if not alert:
            logger.warning(f"Alert not found: {alert_id}")
            return False
        
        self.session.delete(alert)
        self.session.commit()
        logger.info(f"Deleted alert: {alert.name} ({alert_id})")
        return True
    
    def increment_trigger_count(self, alert_id: UUID) -> Optional[Alert]:
        """
        Increment trigger count and update last_triggered_at.
        
        Args:
            alert_id: Alert UUID
            
        Returns:
            Updated Alert instance or None if not found
        """
        from datetime import datetime
        
        alert = self.get_by_id(alert_id)
        if not alert:
            return None
        
        alert.trigger_count += 1
        alert.last_triggered_at = datetime.utcnow()
        
        self.session.commit()
        self.session.refresh(alert)
        return alert

