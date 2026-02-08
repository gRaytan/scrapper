"""User job application service."""
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from sqlalchemy.orm import Session

from src.storage.repositories.application_repo import ApplicationRepository
from src.storage.repositories.job_repo import JobPositionRepository
from src.models.user_job_application import UserJobApplication


class ApplicationService:
    """Service for managing user job applications."""
    
    def __init__(self, session: Session):
        self.session = session
        self.app_repo = ApplicationRepository(session)
        self.job_repo = JobPositionRepository(session)
    
    def track_job(
        self,
        user_id: UUID,
        job_position_id: UUID,
        status: str = 'interested',
        notes: Optional[str] = None
    ) -> UserJobApplication:
        """
        Track a job (add to user's tracked jobs).
        
        Args:
            user_id: User UUID
            job_position_id: Job position UUID
            status: Initial status (default: interested)
            notes: Optional notes
            
        Returns:
            Created application
            
        Raises:
            ValueError: If job already tracked or job not found
        """
        # Check if already tracked
        existing = self.app_repo.get_by_user_and_job(user_id, job_position_id)
        if existing:
            raise ValueError("Job already tracked")
        
        # Verify job exists
        job = self.job_repo.get_by_id(job_position_id)
        if not job:
            raise ValueError("Job not found")
        
        # Create application
        data = {
            'user_id': user_id,
            'job_position_id': job_position_id,
            'status': status,
            'notes': notes,
        }
        
        if status != 'interested':
            data['applied_at'] = datetime.utcnow()
        
        return self.app_repo.create(data)
    
    def get_application(self, application_id: UUID, user_id: UUID) -> Optional[UserJobApplication]:
        """Get application by ID, verifying ownership."""
        application = self.app_repo.get_by_id(application_id)
        if application and application.user_id == user_id:
            return application
        return None
    
    def list_applications(
        self,
        user_id: UUID,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> dict:
        """
        List user's tracked jobs/applications.
        
        Returns:
            Dict with applications, total, page info
        """
        applications, total = self.app_repo.list_by_user(
            user_id=user_id,
            status=status,
            page=page,
            page_size=page_size
        )
        
        total_pages = (total + page_size - 1) // page_size
        
        return {
            'applications': applications,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': total_pages,
        }
    
    def update_application(
        self,
        application_id: UUID,
        user_id: UUID,
        status: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Optional[UserJobApplication]:
        """
        Update application status or notes.
        
        Args:
            application_id: Application UUID
            user_id: User UUID (for ownership verification)
            status: New status
            notes: New notes
            
        Returns:
            Updated application or None if not found/not owned
        """
        application = self.get_application(application_id, user_id)
        if not application:
            return None
        
        update_data = {}
        if status is not None:
            update_data['status'] = status
            # Set applied_at when moving from interested to applied
            if status != 'interested' and application.status == 'interested':
                update_data['applied_at'] = datetime.utcnow()
        
        if notes is not None:
            update_data['notes'] = notes
        
        if not update_data:
            return application
        
        return self.app_repo.update(application_id, update_data)
    
    def untrack_job(self, application_id: UUID, user_id: UUID) -> bool:
        """
        Remove job from tracking.
        
        Args:
            application_id: Application UUID
            user_id: User UUID (for ownership verification)
            
        Returns:
            True if deleted, False if not found/not owned
        """
        application = self.get_application(application_id, user_id)
        if not application:
            return False
        
        return self.app_repo.delete(application_id)
    
    def get_stats(self, user_id: UUID) -> dict:
        """Get application statistics for user."""
        return self.app_repo.get_stats_by_user(user_id)
    
    def is_job_tracked(self, user_id: UUID, job_position_id: UUID) -> Optional[UserJobApplication]:
        """Check if a job is tracked by user."""
        return self.app_repo.get_by_user_and_job(user_id, job_position_id)
