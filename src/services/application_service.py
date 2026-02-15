"""User job application service."""
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from sqlalchemy.orm import Session

from src.storage.repositories.application_repo import ApplicationRepository
from src.storage.repositories.job_repo import JobPositionRepository
from src.models.user_job_application import UserJobApplication, ApplicationInterview


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
        notes: Optional[str] = None,
        comments: Optional[str] = None,
        applied_at: Optional[datetime] = None,
        custom_title: Optional[str] = None,
        custom_company: Optional[str] = None,
        custom_location: Optional[str] = None,
        salary_min: Optional[int] = None,
        salary_max: Optional[int] = None,
        salary_currency: Optional[str] = None,
        next_interview_at: Optional[datetime] = None
    ) -> Optional[UserJobApplication]:
        """
        Update application fields.

        Args:
            application_id: Application UUID
            user_id: User UUID (for ownership verification)
            status: New status
            notes: New notes
            comments: Short comment visible in table
            applied_at: Date when application was submitted
            custom_title: Custom job title override
            custom_company: Custom company name override
            custom_location: Custom location override
            salary_min: Minimum salary
            salary_max: Maximum salary
            salary_currency: Salary currency
            next_interview_at: Date/time of next interview

        Returns:
            Updated application or None if not found/not owned
        """
        application = self.get_application(application_id, user_id)
        if not application:
            return None

        update_data = {}
        if status is not None:
            update_data['status'] = status
            # Auto-set applied_at when moving from interested to applied (if not explicitly provided)
            if status != 'interested' and application.status == 'interested' and applied_at is None and application.applied_at is None:
                update_data['applied_at'] = datetime.utcnow()

        if notes is not None:
            update_data['notes'] = notes

        if comments is not None:
            update_data['comments'] = comments

        # Allow explicit setting of applied_at
        if applied_at is not None:
            update_data['applied_at'] = applied_at

        # Custom overrides
        if custom_title is not None:
            update_data['custom_title'] = custom_title
        if custom_company is not None:
            update_data['custom_company'] = custom_company
        if custom_location is not None:
            update_data['custom_location'] = custom_location

        # Salary fields
        if salary_min is not None:
            update_data['salary_min'] = salary_min
        if salary_max is not None:
            update_data['salary_max'] = salary_max
        if salary_currency is not None:
            update_data['salary_currency'] = salary_currency

        # Interview tracking
        if next_interview_at is not None:
            update_data['next_interview_at'] = next_interview_at

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

    def create_manual_job_and_track(
        self,
        user_id: UUID,
        title: str,
        company_name: str,
        location: Optional[str] = None,
        job_url: Optional[str] = None,
        application_url: Optional[str] = None,
        salary_min: Optional[int] = None,
        salary_max: Optional[int] = None,
        salary_currency: str = "USD",
        remote_type: Optional[str] = None,
        employment_type: Optional[str] = None,
        status: str = 'interested',
        notes: Optional[str] = None
    ) -> UserJobApplication:
        """
        Create a manual job position and track it.
        
        This is for jobs that users find outside the platform and want to track.
        """
        from src.storage.repositories.company_repo import CompanyRepository
        import uuid
        
        company_repo = CompanyRepository(self.session)
        
        # Find or create company
        company = company_repo.get_by_name(company_name)
        if not company:
            company = company_repo.create({
                'name': company_name,
                'website': '',  # Manual companies don't have website
                'careers_url': '',  # Manual companies don't have careers URL
                'scraping_config': {},
            })
        
        # Build salary range if provided
        salary_range = None
        if salary_min is not None or salary_max is not None:
            salary_range = {
                'min': salary_min,
                'max': salary_max,
                'currency': salary_currency,
            }
        
        # Generate unique external_id for manual jobs
        external_id = f"manual_{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow()
        
        # Create job position
        job_data = {
            'title': title,
            'company_id': company.id,
            'external_id': external_id,
            'location': location,
            'job_url': job_url or '',
            'application_url': application_url,
            'salary_range': salary_range,
            'remote_type': remote_type,
            'employment_type': employment_type,
            'job_type': 'manual',
            'source_type': 'manual',
            'is_active': True,
            'status': 'active',
            'posted_date': now,
            'scraped_at': now,
            'first_seen_at': now,
            'last_seen_at': now,
        }
        
        job = self.job_repo.create(job_data)
        
        # Track the job
        app_data = {
            'user_id': user_id,
            'job_position_id': job.id,
            'status': status,
            'notes': notes,
        }

        if status != 'interested':
            app_data['applied_at'] = now

        return self.app_repo.create(app_data)

    # Interview CRUD methods
    def add_interview(
        self,
        application_id: UUID,
        user_id: UUID,
        scheduled_at: datetime,
        interview_type: Optional[str] = None,
        interviewer: Optional[str] = None,
        location: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Optional[ApplicationInterview]:
        """Add an interview to an application."""
        application = self.get_application(application_id, user_id)
        if not application:
            return None

        interview = ApplicationInterview(
            application_id=application_id,
            scheduled_at=scheduled_at,
            interview_type=interview_type,
            interviewer=interviewer,
            location=location,
            notes=notes,
            status='scheduled'
        )
        self.session.add(interview)
        self.session.commit()
        self.session.refresh(interview)

        # Update next_interview_at if this is the earliest upcoming interview
        self._update_next_interview(application)

        return interview

    def update_interview(
        self,
        interview_id: UUID,
        user_id: UUID,
        scheduled_at: Optional[datetime] = None,
        interview_type: Optional[str] = None,
        interviewer: Optional[str] = None,
        location: Optional[str] = None,
        notes: Optional[str] = None,
        status: Optional[str] = None,
        feedback: Optional[str] = None
    ) -> Optional[ApplicationInterview]:
        """Update an interview."""
        interview = self.session.query(ApplicationInterview).filter(
            ApplicationInterview.id == interview_id
        ).first()

        if not interview:
            return None

        # Verify ownership through application
        application = self.get_application(interview.application_id, user_id)
        if not application:
            return None

        if scheduled_at is not None:
            interview.scheduled_at = scheduled_at
        if interview_type is not None:
            interview.interview_type = interview_type
        if interviewer is not None:
            interview.interviewer = interviewer
        if location is not None:
            interview.location = location
        if notes is not None:
            interview.notes = notes
        if status is not None:
            interview.status = status
        if feedback is not None:
            interview.feedback = feedback

        self.session.commit()
        self.session.refresh(interview)

        # Update next_interview_at
        self._update_next_interview(application)

        return interview

    def delete_interview(self, interview_id: UUID, user_id: UUID) -> bool:
        """Delete an interview."""
        interview = self.session.query(ApplicationInterview).filter(
            ApplicationInterview.id == interview_id
        ).first()

        if not interview:
            return False

        # Verify ownership through application
        application = self.get_application(interview.application_id, user_id)
        if not application:
            return False

        self.session.delete(interview)
        self.session.commit()

        # Update next_interview_at
        self._update_next_interview(application)

        return True

    def _update_next_interview(self, application: UserJobApplication) -> None:
        """Update the next_interview_at field based on scheduled interviews."""
        now = datetime.utcnow()
        upcoming = self.session.query(ApplicationInterview).filter(
            ApplicationInterview.application_id == application.id,
            ApplicationInterview.scheduled_at > now,
            ApplicationInterview.status == 'scheduled'
        ).order_by(ApplicationInterview.scheduled_at).first()

        application.next_interview_at = upcoming.scheduled_at if upcoming else None
        self.session.commit()
