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
        company_names: Optional[List[str]] = None,
        locations: Optional[List[str]] = None,
        departments: Optional[List[str]] = None,
        remote_type: Optional[List[str]] = None,
        employment_type: Optional[List[str]] = None,
        seniority_level: Optional[List[str]] = None,
        job_type: Optional[str] = None,
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
            company_names: Filter by company names
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

        # Always exclude manual jobs from the main job listings
        # Manual jobs are user-created and should only appear in their tracker
        filters.append(JobPosition.source_type != 'manual')

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

        if company_names:
            # Look up company IDs by name (case-insensitive)
            from sqlalchemy import func
            company_id_results = self.session.query(Company.id).filter(
                func.lower(Company.name).in_([name.lower() for name in company_names])
            ).all()
            resolved_company_ids = [r[0] for r in company_id_results]
            if resolved_company_ids:
                filters.append(JobPosition.company_id.in_(resolved_company_ids))
            else:
                # No matching companies found, return empty results
                filters.append(JobPosition.company_id == None)
            filters_applied["companies"] = company_names

        if locations:
            # Use ILIKE for partial matching (e.g., "Tel Aviv" matches "Tel Aviv, Israel")
            location_filters = [JobPosition.location.ilike(f"%{loc}%") for loc in locations]
            filters.append(or_(*location_filters))
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

        if job_type:
            filters.append(JobPosition.job_type == job_type)
            filters_applied["job_type"] = job_type

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

    def get_filter_options(self) -> Dict[str, Any]:
        """
        Get available filter options (facets) for job listings.

        Returns distinct values and counts for each filter category.
        Only includes active jobs.
        """
        # Base query for active jobs
        base_query = self.session.query(JobPosition).filter(JobPosition.is_active == True)

        # Get location counts
        location_counts = (
            self.session.query(
                JobPosition.location,
                func.count(JobPosition.id).label('count')
            )
            .filter(JobPosition.is_active == True)
            .filter(JobPosition.location.isnot(None))
            .filter(JobPosition.location != '')
            .group_by(JobPosition.location)
            .order_by(func.count(JobPosition.id).desc())
            .limit(50)
            .all()
        )

        # Get company counts
        company_counts = (
            self.session.query(
                Company.name,
                func.count(JobPosition.id).label('count')
            )
            .join(JobPosition, JobPosition.company_id == Company.id)
            .filter(JobPosition.is_active == True)
            .group_by(Company.name)
            .order_by(func.count(JobPosition.id).desc())
            .limit(50)
            .all()
        )

        # Get department counts
        department_counts = (
            self.session.query(
                JobPosition.department,
                func.count(JobPosition.id).label('count')
            )
            .filter(JobPosition.is_active == True)
            .filter(JobPosition.department.isnot(None))
            .filter(JobPosition.department != '')
            .group_by(JobPosition.department)
            .order_by(func.count(JobPosition.id).desc())
            .limit(50)
            .all()
        )

        # Get remote type counts
        remote_type_counts = (
            self.session.query(
                JobPosition.remote_type,
                func.count(JobPosition.id).label('count')
            )
            .filter(JobPosition.is_active == True)
            .filter(JobPosition.remote_type.isnot(None))
            .filter(JobPosition.remote_type != '')
            .group_by(JobPosition.remote_type)
            .order_by(func.count(JobPosition.id).desc())
            .all()
        )

        # Get seniority level counts
        seniority_counts = (
            self.session.query(
                JobPosition.seniority_level,
                func.count(JobPosition.id).label('count')
            )
            .filter(JobPosition.is_active == True)
            .filter(JobPosition.seniority_level.isnot(None))
            .filter(JobPosition.seniority_level != '')
            .group_by(JobPosition.seniority_level)
            .order_by(func.count(JobPosition.id).desc())
            .all()
        )

        # Get job title counts (distinct titles from job_positions)
        job_title_counts = (
            self.session.query(
                JobPosition.title,
                func.count(JobPosition.id).label('count')
            )
            .filter(JobPosition.is_active == True)
            .filter(JobPosition.title.isnot(None))
            .filter(JobPosition.title != '')
            .group_by(JobPosition.title)
            .order_by(func.count(JobPosition.id).desc())
            .limit(100)
            .all()
        )

        # Get industry counts (from companies table)
        industry_counts = (
            self.session.query(
                Company.industry,
                func.count(JobPosition.id).label('count')
            )
            .join(JobPosition, JobPosition.company_id == Company.id)
            .filter(JobPosition.is_active == True)
            .filter(Company.industry.isnot(None))
            .filter(Company.industry != '')
            .group_by(Company.industry)
            .order_by(func.count(JobPosition.id).desc())
            .all()
        )

        # Get company size counts (from companies table)
        company_size_counts = (
            self.session.query(
                Company.size,
                func.count(JobPosition.id).label('count')
            )
            .join(JobPosition, JobPosition.company_id == Company.id)
            .filter(JobPosition.is_active == True)
            .filter(Company.size.isnot(None))
            .filter(Company.size != '')
            .group_by(Company.size)
            .order_by(func.count(JobPosition.id).desc())
            .all()
        )

        return {
            "locations": [
                {"value": loc, "label": loc, "count": count}
                for loc, count in location_counts if loc
            ],
            "companies": [
                {"value": name, "label": name, "count": count}
                for name, count in company_counts if name
            ],
            "departments": [
                {"value": dept, "label": dept, "count": count}
                for dept, count in department_counts if dept
            ],
            "remote_types": [
                {"value": rt, "label": rt, "count": count}
                for rt, count in remote_type_counts if rt
            ],
            "seniority_levels": [
                {"value": sl, "label": sl, "count": count}
                for sl, count in seniority_counts if sl
            ],
            "job_titles": [
                {"value": title, "label": title, "count": count}
                for title, count in job_title_counts if title
            ],
            "industries": [
                {"value": industry, "label": industry, "count": count}
                for industry, count in industry_counts if industry
            ],
            "company_sizes": [
                {"value": size, "label": size, "count": count}
                for size, count in company_size_counts if size
            ],
        }

    def get_jobs_over_time(self, months: int = 12) -> List[Dict[str, Any]]:
        """
        Get job posting counts grouped by month.

        Args:
            months: Number of months to look back (default: 12)

        Returns:
            List of dicts with month and count
        """
        from datetime import timedelta
        from sqlalchemy import extract

        # Calculate the start date (beginning of month, N months ago)
        today = datetime.utcnow()
        start_date = datetime(today.year, today.month, 1) - timedelta(days=months * 31)
        start_date = datetime(start_date.year, start_date.month, 1)

        # Query jobs grouped by year and month
        results = (
            self.session.query(
                extract('year', JobPosition.posted_date).label('year'),
                extract('month', JobPosition.posted_date).label('month'),
                func.count(JobPosition.id).label('count')
            )
            .filter(JobPosition.posted_date >= start_date)
            .filter(JobPosition.posted_date.isnot(None))
            .group_by(
                extract('year', JobPosition.posted_date),
                extract('month', JobPosition.posted_date)
            )
            .order_by(
                extract('year', JobPosition.posted_date),
                extract('month', JobPosition.posted_date)
            )
            .all()
        )

        # Convert to list of dicts with formatted month
        data = []
        for year, month, count in results:
            if year and month:
                month_str = datetime(int(year), int(month), 1).strftime('%Y-%m')
                data.append({
                    "month": month_str,
                    "year": int(year),
                    "month_num": int(month),
                    "count": count
                })

        return data
