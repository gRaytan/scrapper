"""
Repository for JobPosition model operations.
"""
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from src.models.job_position import JobPosition
from src.utils.logger import logger


class JobPositionRepository:
    """Repository for JobPosition CRUD operations."""
    
    def __init__(self, session: Session):
        """Initialize repository with database session."""
        self.session = session
    
    def create(self, job_data: dict) -> JobPosition:
        """
        Create a new job position.
        
        Args:
            job_data: Dictionary with job fields
            
        Returns:
            Created JobPosition instance
        """
        job = JobPosition(**job_data)
        self.session.add(job)
        self.session.commit()
        self.session.refresh(job)
        logger.info(f"Created job: {job.title} at {job.company.name} ({job.id})")
        return job
    
    def get_by_id(self, job_id: UUID) -> Optional[JobPosition]:
        """Get job by ID."""
        return self.session.query(JobPosition).filter(JobPosition.id == job_id).first()
    
    def get_by_external_id(self, external_id: str, company_id: UUID) -> Optional[JobPosition]:
        """Get job by external ID and company."""
        return self.session.query(JobPosition).filter(
            and_(
                JobPosition.external_id == external_id,
                JobPosition.company_id == company_id
            )
        ).first()
    
    def get_by_company(
        self,
        company_id: UUID,
        is_active: Optional[bool] = None,
        limit: Optional[int] = None
    ) -> List[JobPosition]:
        """
        Get all jobs for a company.
        
        Args:
            company_id: Company UUID
            is_active: Filter by active status
            limit: Maximum number of results
            
        Returns:
            List of JobPosition instances
        """
        query = self.session.query(JobPosition).filter(JobPosition.company_id == company_id)
        
        if is_active is not None:
            query = query.filter(JobPosition.is_active == is_active)
        
        query = query.order_by(JobPosition.posted_date.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def get_recent_jobs(self, company_id: UUID, hours: int = 24) -> List[JobPosition]:
        """
        Get jobs posted or updated in the last N hours.
        
        Args:
            company_id: Company UUID
            hours: Number of hours to look back
            
        Returns:
            List of JobPosition instances
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        return self.session.query(JobPosition).filter(
            and_(
                JobPosition.company_id == company_id,
                or_(
                    JobPosition.posted_date >= cutoff_time,
                    JobPosition.updated_at >= cutoff_time
                )
            )
        ).all()
    
    def update(self, job_id: UUID, update_data: dict) -> Optional[JobPosition]:
        """
        Update job position.
        
        Args:
            job_id: Job UUID
            update_data: Dictionary with fields to update
            
        Returns:
            Updated JobPosition instance or None if not found
        """
        job = self.get_by_id(job_id)
        if not job:
            logger.warning(f"Job not found: {job_id}")
            return None
        
        for key, value in update_data.items():
            if hasattr(job, key):
                setattr(job, key, value)
        
        self.session.commit()
        self.session.refresh(job)
        logger.info(f"Updated job: {job.title} ({job.id})")
        return job
    
    def bulk_create(self, jobs_data: List[dict]) -> List[JobPosition]:
        """
        Create multiple job positions.
        
        Args:
            jobs_data: List of dictionaries with job fields
            
        Returns:
            List of created JobPosition instances
        """
        jobs = [JobPosition(**job_data) for job_data in jobs_data]
        self.session.bulk_save_objects(jobs, return_defaults=True)
        self.session.commit()
        logger.info(f"Bulk created {len(jobs)} jobs")
        return jobs
    
    def deactivate_missing_jobs(
        self,
        company_id: UUID,
        current_external_ids: List[str]
    ) -> int:
        """
        Deactivate jobs that are no longer in the current scrape.
        
        Args:
            company_id: Company UUID
            current_external_ids: List of external IDs from current scrape
            
        Returns:
            Number of jobs deactivated
        """
        # Find active jobs not in current list
        jobs_to_deactivate = self.session.query(JobPosition).filter(
            and_(
                JobPosition.company_id == company_id,
                JobPosition.is_active == True,
                JobPosition.external_id.notin_(current_external_ids)
            )
        ).all()
        
        count = 0
        for job in jobs_to_deactivate:
            job.is_active = False
            count += 1
        
        if count > 0:
            self.session.commit()
            logger.info(f"Deactivated {count} jobs for company {company_id}")
        
        return count
    
    def get_or_create(
        self,
        external_id: str,
        company_id: UUID,
        defaults: dict
    ) -> tuple[JobPosition, bool]:
        """
        Get existing job or create new one.
        
        Args:
            external_id: External job ID
            company_id: Company UUID
            defaults: Default values for creation
            
        Returns:
            Tuple of (JobPosition instance, created boolean)
        """
        job = self.get_by_external_id(external_id, company_id)
        if job:
            return job, False
        
        job_data = {
            "external_id": external_id,
            "company_id": company_id,
            **defaults
        }
        job = self.create(job_data)
        return job, True

