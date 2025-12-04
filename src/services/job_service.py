"""Job service for business logic."""
import logging
import math
from typing import Optional, List, Dict, Any
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

