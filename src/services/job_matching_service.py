"""Job matching service for matching jobs to user alerts."""
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from src.models.alert import Alert
from src.models.alert_notification import AlertNotification
from src.models.job_position import JobPosition


logger = logging.getLogger(__name__)


class JobMatchingService:
    """Service for matching jobs to user alerts and creating notifications."""

    def __init__(self, session: Session):
        """Initialize service with database session."""
        self.session = session

    def _create_notification(
        self,
        alert: Alert,
        jobs: List[JobPosition],
        user_id: UUID,
        delivery_method: str = 'email'
    ) -> AlertNotification:
        """
        Create a notification record with multiple jobs.

        Args:
            alert: The alert that matched
            jobs: List of jobs that matched
            user_id: User to notify
            delivery_method: Fallback delivery method

        Returns:
            Created AlertNotification (not yet committed)
        """
        job_ids = [str(job.id) for job in jobs]
        notification = AlertNotification(
            alert_id=alert.id,
            user_id=user_id,
            job_position_ids=job_ids,
            job_count=len(job_ids),
            delivery_method=alert.notification_method or delivery_method,
            delivery_status='pending'
            # sent_at is set when notification is actually sent
        )
        self.session.add(notification)
        return notification

    def _update_alert_triggered(self, alert: Alert) -> None:
        """Update alert tracking after it's triggered."""
        alert.last_triggered_at = datetime.utcnow()
        alert.trigger_count = (alert.trigger_count or 0) + 1

    def _get_notified_pairs(
        self,
        alert_ids: List[UUID],
        job_ids: List[UUID]
    ) -> set:
        """
        Get set of (alert_id, job_id) pairs that already have notifications.

        Args:
            alert_ids: List of alert IDs to check
            job_ids: List of job IDs to check

        Returns:
            Set of (alert_id, job_id_str) tuples
        """
        if not alert_ids or not job_ids:
            return set()

        # Query notifications for these alerts
        existing = self.session.query(
            AlertNotification.alert_id,
            AlertNotification.job_position_ids
        ).filter(
            AlertNotification.alert_id.in_(alert_ids)
        ).all()

        # Build set of (alert_id, job_id) pairs from JSONB arrays
        pairs = set()
        job_id_strs = set(str(jid) for jid in job_ids)
        for notification in existing:
            for job_id_str in notification.job_position_ids:
                if job_id_str in job_id_strs:
                    pairs.add((notification.alert_id, job_id_str))
        return pairs

    def _get_notified_job_ids_for_alert(
        self,
        alert_id: UUID,
        job_ids: List[UUID]
    ) -> set:
        """
        Get set of job IDs that already have notifications for a specific alert.

        Args:
            alert_id: Alert ID to check
            job_ids: List of job IDs to check

        Returns:
            Set of job_id strings
        """
        if not job_ids:
            return set()

        existing = self.session.query(
            AlertNotification.job_position_ids
        ).filter(
            AlertNotification.alert_id == alert_id
        ).all()

        # Collect all job IDs from JSONB arrays
        notified = set()
        job_id_strs = set(str(jid) for jid in job_ids)
        for notification in existing:
            for job_id_str in notification.job_position_ids:
                if job_id_str in job_id_strs:
                    notified.add(job_id_str)
        return notified

    def match_jobs_to_alerts(
        self,
        jobs: List[JobPosition],
        alerts: Optional[List[Alert]] = None
    ) -> Dict[UUID, List[Dict[str, Any]]]:
        """
        Match a list of jobs against all active alerts (or specified alerts).

        Args:
            jobs: List of job positions to match
            alerts: Optional list of alerts to match against (defaults to all active alerts)

        Returns:
            Dictionary mapping user_id to list of {alert, jobs} matches
        """
        if not jobs:
            return {}

        # Get all active alerts if not specified
        if alerts is None:
            alerts = self.session.query(Alert).filter(
                Alert.is_active == True
            ).options(joinedload(Alert.user)).all()

        if not alerts:
            logger.info("No active alerts found")
            return {}

        # Batch-load existing notifications to avoid N+1 queries
        alert_ids = [a.id for a in alerts]
        job_ids = [j.id for j in jobs]
        notified_pairs = self._get_notified_pairs(alert_ids, job_ids)

        # Match jobs to alerts
        user_matches: Dict[UUID, List[Dict[str, Any]]] = {}

        for alert in alerts:
            matching_jobs = []
            for job in jobs:
                if alert.matches_position(job):
                    # Check if we already notified about this job for this alert
                    # notified_pairs uses string job IDs
                    if (alert.id, str(job.id)) not in notified_pairs:
                        matching_jobs.append(job)

            if matching_jobs:
                if alert.user_id not in user_matches:
                    user_matches[alert.user_id] = []

                user_matches[alert.user_id].append({
                    'alert': alert,
                    'jobs': matching_jobs
                })

                logger.info(
                    f"Alert '{alert.name}' (user {alert.user_id}) matched {len(matching_jobs)} jobs"
                )

        return user_matches
    
    def create_notifications(
        self,
        user_matches: Dict[UUID, List[Dict[str, Any]]],
        delivery_method: str = 'email'
    ) -> Dict[str, Any]:
        """
        Create notification records for matched jobs.
        
        Args:
            user_matches: Dictionary from match_jobs_to_alerts
            delivery_method: Notification delivery method
            
        Returns:
            Statistics about created notifications
        """
        total_notifications = 0
        total_jobs = 0
        alerts_triggered = 0

        for user_id, alert_matches in user_matches.items():
            for match in alert_matches:
                alert = match['alert']
                jobs = match['jobs']

                # Create one notification per alert with all matching jobs
                self._create_notification(alert, jobs, user_id, delivery_method)
                total_notifications += 1
                total_jobs += len(jobs)

                # Update alert tracking
                self._update_alert_triggered(alert)
                alerts_triggered += 1

        self.session.commit()

        return {
            'notifications_created': total_notifications,
            'total_jobs_matched': total_jobs,
            'alerts_triggered': alerts_triggered,
            'users_notified': len(user_matches)
        }
    
    def process_new_jobs(self, jobs: List[JobPosition]) -> Dict[str, Any]:
        """
        Process new jobs: match to alerts and create notifications.
        
        Args:
            jobs: List of new job positions
            
        Returns:
            Processing statistics
        """
        if not jobs:
            return {'status': 'success', 'message': 'No jobs to process'}
        
        # Match jobs to alerts
        user_matches = self.match_jobs_to_alerts(jobs)
        
        if not user_matches:
            return {
                'status': 'success',
                'jobs_processed': len(jobs),
                'matches_found': 0
            }
        
        # Create notifications
        notification_stats = self.create_notifications(user_matches)
        
        return {
            'status': 'success',
            'jobs_processed': len(jobs),
            **notification_stats
        }
    
    def process_alert_against_existing_jobs(
        self,
        alert: Alert,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """
        Process a new/updated alert against existing jobs in the database.
        
        This is called when a new alert is created to find matching jobs
        that were scraped before the alert existed.
        
        Args:
            alert: The alert to process
            days_back: How many days back to look for jobs (default: 30)
            
        Returns:
            Processing statistics
        """
        from datetime import timedelta
        
        cutoff = datetime.utcnow() - timedelta(days=days_back)
        
        # Get active jobs from the last N days
        existing_jobs = self.session.query(JobPosition).filter(
            JobPosition.is_active == True,
            JobPosition.created_at >= cutoff
        ).options(joinedload(JobPosition.company)).all()
        
        if not existing_jobs:
            return {
                'status': 'success',
                'message': 'No existing jobs found',
                'jobs_checked': 0,
                'matches_found': 0
            }
        
        # Batch-load existing notifications for this alert to avoid N+1 queries
        job_ids = [j.id for j in existing_jobs]
        notified_job_ids = self._get_notified_job_ids_for_alert(alert.id, job_ids)

        # Match jobs to this specific alert
        # notified_job_ids contains string job IDs
        matching_jobs = []
        for job in existing_jobs:
            if alert.matches_position(job):
                # Check if already notified using pre-loaded set
                if str(job.id) not in notified_job_ids:
                    matching_jobs.append(job)

        if not matching_jobs:
            return {
                'status': 'success',
                'jobs_checked': len(existing_jobs),
                'matches_found': 0
            }

        # Create one notification with all matching jobs
        self._create_notification(alert, matching_jobs, alert.user_id)

        # Update alert tracking
        self._update_alert_triggered(alert)

        self.session.commit()

        logger.info(
            f"Alert '{alert.name}' matched {len(matching_jobs)} existing jobs "
            f"(checked {len(existing_jobs)} jobs from last {days_back} days)"
        )

        return {
            'status': 'success',
            'jobs_checked': len(existing_jobs),
            'matches_found': len(matching_jobs),
            'notifications_created': 1  # One notification with all jobs
        }

