"""Job service for business logic."""
import logging
import math
from typing import Optional, List, Dict, Any, Set
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func

from src.storage.repositories.job_repo import JobPositionRepository
from src.storage.repositories.alert_repo import AlertRepository
from src.models.job_position import JobPosition
from src.models.company import Company

logger = logging.getLogger(__name__)


class JobService:
    """Service for job-related business logic."""
    
    def __init__(self, session: Session):
        """Initialize service with database session."""
        self.session = session
        self.job_repo = JobPositionRepository(session)
        self.alert_repo = AlertRepository(session)
    
    def list_jobs(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        company_ids: Optional[List[UUID]] = None,
        locations: Optional[List[str]] = None,
        departments: Optional[List[str]] = None,
        remote_type: Optional[List[str]] = None,
        employment_type: Optional[List[str]] = None,
        seniority_level: Optional[List[str]] = None,
        posted_after: Optional[datetime] = None,
        is_active: Optional[bool] = True,
        sort_by: str = "posted_date",
        sort_order: str = "desc",
    ) -> Dict[str, Any]:
        """
        List jobs with filtering, pagination, and sorting.
        
        Args:
            page: Page number (1-indexed)
            page_size: Number of items per page
            search: Search query for title and description
            company_ids: Filter by company IDs
            locations: Filter by locations
            departments: Filter by departments
            remote_type: Filter by remote types
            employment_type: Filter by employment types
            seniority_level: Filter by seniority levels
            posted_after: Filter by posted date
            is_active: Filter by active status
            sort_by: Field to sort by
            sort_order: Sort order (asc/desc)
            
        Returns:
            Dictionary with jobs, pagination info, and applied filters
        """
        # Build query
        query = self.session.query(JobPosition).options(joinedload(JobPosition.company))
        
        # Apply filters
        filters = []
        filters_applied = {}
        
        if is_active is not None:
            filters.append(JobPosition.is_active == is_active)
            filters_applied["is_active"] = is_active
        
        if search:
            search_filter = or_(
                JobPosition.title.ilike(f"%{search}%"),
                JobPosition.description.ilike(f"%{search}%")
            )
            filters.append(search_filter)
            filters_applied["search"] = search
        
        if company_ids:
            filters.append(JobPosition.company_id.in_(company_ids))
            filters_applied["company_ids"] = [str(cid) for cid in company_ids]
        
        if locations:
            filters.append(JobPosition.location.in_(locations))
            filters_applied["locations"] = locations
        
        if departments:
            filters.append(JobPosition.department.in_(departments))
            filters_applied["departments"] = departments
        
        if remote_type:
            filters.append(JobPosition.remote_type.in_(remote_type))
            filters_applied["remote_type"] = remote_type
        
        if employment_type:
            filters.append(JobPosition.employment_type.in_(employment_type))
            filters_applied["employment_type"] = employment_type
        
        if seniority_level:
            filters.append(JobPosition.seniority_level.in_(seniority_level))
            filters_applied["seniority_level"] = seniority_level
        
        if posted_after:
            filters.append(JobPosition.posted_date >= posted_after)
            filters_applied["posted_after"] = posted_after.isoformat()
        
        if filters:
            query = query.filter(and_(*filters))
        
        # Get total count
        total = query.count()
        
        # Apply sorting
        sort_field = getattr(JobPosition, sort_by, JobPosition.posted_date)
        if sort_order == "desc":
            query = query.order_by(sort_field.desc())
        else:
            query = query.order_by(sort_field.asc())
        
        # Apply pagination
        offset = (page - 1) * page_size
        jobs = query.offset(offset).limit(page_size).all()
        
        # Calculate total pages
        total_pages = math.ceil(total / page_size) if total > 0 else 0
        
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "jobs": jobs,
            "filters_applied": filters_applied,
        }
    
    def get_job(self, job_id: UUID) -> Optional[JobPosition]:
        """
        Get job by ID with company details.

        Args:
            job_id: Job UUID

        Returns:
            Job position or None if not found
        """
        return self.session.query(JobPosition).options(
            joinedload(JobPosition.company)
        ).filter(JobPosition.id == job_id).first()

    def get_personalized_jobs(
        self,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        Get personalized jobs for a user based on their active alerts.

        Returns jobs that match ANY of the user's active alerts, sorted by posted date.
        Each job includes information about which alerts it matched.

        Args:
            user_id: User UUID
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            Dictionary with jobs, pagination info, and match information
        """
        # Get user's active alerts
        user_alerts = self.alert_repo.get_by_user(user_id, is_active=True)

        if not user_alerts:
            # No active alerts, return empty result
            return {
                "total": 0,
                "page": page,
                "page_size": page_size,
                "total_pages": 0,
                "jobs": [],
                "alert_count": 0,
            }

        # Get all active jobs
        active_jobs = self.session.query(JobPosition).filter(
            JobPosition.is_active == True
        ).options(joinedload(JobPosition.company)).all()

        # Find jobs that match any alert
        matching_jobs_map: Dict[UUID, Set[str]] = {}  # job_id -> set of matching alert names

        for job in active_jobs:
            for alert in user_alerts:
                if alert.matches_position(job):
                    if job.id not in matching_jobs_map:
                        matching_jobs_map[job.id] = set()
                    matching_jobs_map[job.id].add(alert.name)

        # Get matching jobs and sort by posted date (newest first)
        # Use created_at as fallback for jobs without posted_date
        matching_jobs = [
            job for job in active_jobs
            if job.id in matching_jobs_map
        ]
        matching_jobs.sort(key=lambda j: j.posted_date or j.created_at, reverse=True)

        # Calculate pagination
        total = len(matching_jobs)
        total_pages = math.ceil(total / page_size) if total > 0 else 0
        offset = (page - 1) * page_size
        paginated_jobs = matching_jobs[offset:offset + page_size]

        # Add match information to jobs
        jobs_with_matches = []
        for job in paginated_jobs:
            job_dict = {
                "job": job,
                "matched_alerts": list(matching_jobs_map[job.id]),
                "match_count": len(matching_jobs_map[job.id])
            }
            jobs_with_matches.append(job_dict)

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "jobs": jobs_with_matches,
            "alert_count": len(user_alerts),
        }

