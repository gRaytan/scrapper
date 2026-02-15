"""User job application repository."""
from typing import Optional, List
from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from src.models.user_job_application import UserJobApplication
from src.models.job_position import JobPosition


class ApplicationRepository:
    """Repository for user job application operations."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create(self, data: dict) -> UserJobApplication:
        """Create a new application."""
        application = UserJobApplication(**data)
        self.session.add(application)
        self.session.commit()
        self.session.refresh(application)
        return application
    
    def get_by_id(self, application_id: UUID) -> Optional[UserJobApplication]:
        """Get application by ID."""
        return self.session.query(UserJobApplication).filter_by(id=application_id).first()
    
    def get_by_user_and_job(self, user_id: UUID, job_position_id: UUID) -> Optional[UserJobApplication]:
        """Get application by user and job position."""
        return self.session.query(UserJobApplication).filter_by(
            user_id=user_id,
            job_position_id=job_position_id
        ).first()
    
    def list_by_user(
        self,
        user_id: UUID,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[UserJobApplication], int]:
        """List applications for a user with optional status filter."""
        query = self.session.query(UserJobApplication).options(
            joinedload(UserJobApplication.job_position).joinedload(JobPosition.company)
        ).filter_by(user_id=user_id)
        
        if status:
            query = query.filter_by(status=status)
        
        # Get total count
        total = query.count()
        
        # Apply pagination and ordering
        applications = query.order_by(
            UserJobApplication.updated_at.desc()
        ).offset((page - 1) * page_size).limit(page_size).all()
        
        return applications, total
    
    def update(self, application_id: UUID, data: dict) -> Optional[UserJobApplication]:
        """Update an application."""
        application = self.get_by_id(application_id)
        if not application:
            return None
        
        for key, value in data.items():
            if hasattr(application, key):
                setattr(application, key, value)
        
        self.session.commit()
        self.session.refresh(application)
        return application
    
    def delete(self, application_id: UUID) -> bool:
        """Delete an application."""
        application = self.get_by_id(application_id)
        if not application:
            return False
        
        self.session.delete(application)
        self.session.commit()
        return True
    
    def get_stats_by_user(self, user_id: UUID) -> dict:
        """Get application statistics for a user."""
        applications = self.session.query(UserJobApplication).filter_by(user_id=user_id).all()

        # Interview stages for calculating legacy 'interviewing' count
        interview_stages = ['phone_screen', 'technical_1', 'technical_2', 'hr_interview', 'reference_check']

        stats = {
            'total': len(applications),
            'interested': 0,
            'applied': 0,
            # Interview stages
            'phone_screen': 0,
            'technical_1': 0,
            'technical_2': 0,
            'hr_interview': 0,
            'reference_check': 0,
            # Final stages
            'offered': 0,
            'accepted': 0,
            'rejected': 0,
            'withdrawn': 0,
            # Legacy field (sum of all interview stages)
            'interviewing': 0,
        }

        for app in applications:
            if app.status in stats:
                stats[app.status] += 1
            # Also count interview stages in legacy 'interviewing' field
            if app.status in interview_stages:
                stats['interviewing'] += 1

        return stats
