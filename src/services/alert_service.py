"""Alert service for business logic."""
import logging
from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from src.storage.repositories.alert_repo import AlertRepository
from src.storage.repositories.user_repo import UserRepository
from src.models.job_position import JobPosition
from src.models.alert import Alert
from src.models.alert_notification import AlertNotification
from src.api.schemas.alert import AlertCreate, AlertUpdate, AlertStats

logger = logging.getLogger(__name__)


class AlertService:
    """Service for alert-related business logic."""
    
    def __init__(self, session: Session):
        """Initialize service with database session."""
        self.session = session
        self.alert_repo = AlertRepository(session)
        self.user_repo = UserRepository(session)
    
    def create_alert(self, user_id: UUID, alert_data: AlertCreate) -> Alert:
        """
        Create a new alert for a user.
        
        Args:
            user_id: User UUID
            alert_data: Alert creation data
            
        Returns:
            Created alert
            
        Raises:
            ValueError: If user not found
        """
        # Verify user exists
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        # Prepare alert data
        alert_dict = {
            "user_id": user_id,
            "name": alert_data.name,
            "is_active": alert_data.is_active,
            "company_ids": alert_data.company_ids,
            "keywords": alert_data.keywords,
            "excluded_keywords": alert_data.excluded_keywords,
            "locations": alert_data.locations,
            "departments": alert_data.departments,
            "employment_types": alert_data.employment_types,
            "remote_types": alert_data.remote_types,
            "seniority_levels": alert_data.seniority_levels,
            "notification_method": alert_data.notification_method,
            "notification_config": alert_data.notification_config,
        }
        
        # Create alert
        alert = self.alert_repo.create(alert_dict)
        return alert
    
    def get_alert(self, alert_id: UUID, include_stats: bool = False) -> Optional[dict]:
        """
        Get alert by ID.
        
        Args:
            alert_id: Alert UUID
            include_stats: Whether to include alert statistics
            
        Returns:
            Alert data with optional stats, or None if not found
        """
        alert = self.alert_repo.get_by_id(alert_id)
        if not alert:
            return None
        
        if include_stats:
            stats = self._get_alert_stats(alert_id)
            return {"alert": alert, "stats": stats}
        
        return alert
    
    def list_user_alerts(self, user_id: UUID, is_active: Optional[bool] = None) -> List[Alert]:
        """
        List all alerts for a user.
        
        Args:
            user_id: User UUID
            is_active: Filter by active status
            
        Returns:
            List of alerts
        """
        return self.alert_repo.get_by_user(user_id, is_active=is_active)
    
    def update_alert(self, alert_id: UUID, update_data: AlertUpdate) -> Optional[Alert]:
        """
        Update alert.
        
        Args:
            alert_id: Alert UUID
            update_data: Update data
            
        Returns:
            Updated alert or None if not found
        """
        # Prepare update dict (only include non-None values)
        update_dict = {}
        if update_data.name is not None:
            update_dict["name"] = update_data.name
        if update_data.is_active is not None:
            update_dict["is_active"] = update_data.is_active
        if update_data.company_ids is not None:
            update_dict["company_ids"] = update_data.company_ids
        if update_data.keywords is not None:
            update_dict["keywords"] = update_data.keywords
        if update_data.excluded_keywords is not None:
            update_dict["excluded_keywords"] = update_data.excluded_keywords
        if update_data.locations is not None:
            update_dict["locations"] = update_data.locations
        if update_data.departments is not None:
            update_dict["departments"] = update_data.departments
        if update_data.employment_types is not None:
            update_dict["employment_types"] = update_data.employment_types
        if update_data.remote_types is not None:
            update_dict["remote_types"] = update_data.remote_types
        if update_data.seniority_levels is not None:
            update_dict["seniority_levels"] = update_data.seniority_levels
        if update_data.notification_method is not None:
            update_dict["notification_method"] = update_data.notification_method
        if update_data.notification_config is not None:
            update_dict["notification_config"] = update_data.notification_config
        
        if not update_dict:
            # No updates provided
            return self.alert_repo.get_by_id(alert_id)
        
        return self.alert_repo.update(alert_id, update_dict)
    
    def delete_alert(self, alert_id: UUID) -> bool:
        """
        Delete alert.

        Args:
            alert_id: Alert UUID

        Returns:
            True if deleted, False if not found
        """
        return self.alert_repo.delete(alert_id)

    def test_alert(self, alert_id: UUID, limit: int = 10) -> Dict[str, Any]:
        """
        Test alert by finding matching jobs.

        Args:
            alert_id: Alert UUID
            limit: Maximum number of sample jobs to return

        Returns:
            Dictionary with matching jobs count and samples

        Raises:
            ValueError: If alert not found
        """
        alert = self.alert_repo.get_by_id(alert_id)
        if not alert:
            raise ValueError(f"Alert {alert_id} not found")

        # Get all active jobs
        active_jobs = self.session.query(JobPosition).filter(
            JobPosition.is_active == True
        ).options(joinedload(JobPosition.company)).all()

        # Find matching jobs
        matching_jobs = []
        for job in active_jobs:
            if alert.matches_position(job):
                matching_jobs.append(job)

        # Get sample jobs (limited)
        sample_jobs = matching_jobs[:limit]

        return {
            "matching_jobs_count": len(matching_jobs),
            "sample_jobs": sample_jobs,
            "total_active_jobs": len(active_jobs),
        }

    def get_all_matching_jobs(self, alert_id: UUID) -> Dict[str, Any]:
        """
        Get ALL jobs matching an alert (not just samples).

        Args:
            alert_id: Alert UUID

        Returns:
            Dictionary with all matching jobs

        Raises:
            ValueError: If alert not found
        """
        alert = self.alert_repo.get_by_id(alert_id)
        if not alert:
            raise ValueError(f"Alert {alert_id} not found")

        # Get all active jobs
        active_jobs = self.session.query(JobPosition).filter(
            JobPosition.is_active == True
        ).options(joinedload(JobPosition.company)).all()

        # Find ALL matching jobs
        matching_jobs = []
        for job in active_jobs:
            if alert.matches_position(job):
                matching_jobs.append(job)

        return {
            "matching_jobs_count": len(matching_jobs),
            "jobs": matching_jobs,
            "total_active_jobs": len(active_jobs),
        }

    def _get_alert_stats(self, alert_id: UUID) -> AlertStats:
        """
        Get alert statistics.

        Args:
            alert_id: Alert UUID

        Returns:
            Alert statistics
        """
        alert = self.alert_repo.get_by_id(alert_id)
        if not alert:
            return AlertStats()

        # Count matching jobs
        active_jobs = self.session.query(JobPosition).filter(
            JobPosition.is_active == True
        ).all()

        matching_count = sum(1 for job in active_jobs if alert.matches_position(job))

        # Count notifications sent
        notifications_sent = self.session.query(AlertNotification).filter(
            AlertNotification.alert_id == alert_id
        ).count()

        return AlertStats(
            matching_jobs_count=matching_count,
            last_triggered_at=alert.last_triggered_at,
            trigger_count=alert.trigger_count,
            notifications_sent=notifications_sent,
        )

