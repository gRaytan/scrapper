"""Job service for business logic."""
import logging
import math
from typing import Optional, List, Dict, Any, Set
from uuid import UUID
from datetime import datetime
from collections import defaultdict

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func

from src.storage.repositories.job_repo import JobPositionRepository
from src.storage.repositories.alert_repo import AlertRepository
from src.models.job_position import JobPosition
from src.models.company import Company

logger = logging.getLogger(__name__)

# Job family classification mapping
JOB_FAMILIES = {
    "Software Engineer": ["software engineer", "software developer", "backend engineer", "frontend engineer", "full stack", "fullstack", "full-stack", "web developer", "application developer", "application engineer", "developer", "programmer", "swe", "integration engineer", "robotics engineer"],
    "Data Scientist": ["data scientist", "machine learning", "ml engineer", "ai engineer", "deep learning", "nlp engineer", "computer vision", "research scientist", "artificial intelligence engineer"],
    "Data Engineer": ["data engineer", "etl", "data pipeline", "big data", "data architect", "analytics engineer", "bi engineer", "data center engineer"],
    "Data Analyst": ["data analyst", "business analyst", "analytics", "bi analyst", "reporting analyst", "insights analyst", "product analyst", "system analyst"],
    "Product Manager": ["product manager", "product owner", "product lead", "product director", "group product manager", "director of product", "program manager", "project manager", "technical program manager", "technical project manager", "pmo", "planner"],
    "DevOps Engineer": ["devops", "sre", "site reliability", "platform engineer", "infrastructure", "release engineer", "devsecops"],
    "QA Engineer": ["qa engineer", "quality assurance", "test engineer", "sdet", "automation engineer", "quality engineer", "verification engineer"],
    "Designer": ["designer", "ux", "ui", "product designer", "graphic designer", "visual designer", "interaction designer"],
    "Engineering Manager": ["engineering manager", "tech lead", "team lead", "vp engineering", "director of engineering", "head of engineering", "principal engineer", "staff engineer", "architect", "chief technology officer", "cto", "vp r&d", "chief information officer", "cio"],
    "Security Engineer": ["security engineer", "cybersecurity", "infosec", "security analyst", "penetration tester", "security architect", "security researcher"],
    "Mobile Developer": ["mobile developer", "ios developer", "android developer", "react native", "flutter", "mobile engineer"],
    "Cloud Engineer": ["cloud engineer", "aws", "azure", "gcp", "cloud architect", "solutions architect", "system administrator", "network engineer", "system engineer", "it specialist", "information technology specialist", "help desk", "technical support", "it technician"],
    "Solutions Engineer": ["solutions engineer", "sales engineer", "pre-sales", "technical account", "customer engineer"],
    "Hardware Engineer": ["hardware engineer", "hardware systems engineer", "chip design", "physical design", "mechanical engineer", "electrical engineer", "embedded engineer", "firmware engineer", "algorithm engineer"],
    "Technical Writer": ["technical writer", "documentation", "content writer"],
    "Marketing": ["marketing", "growth", "seo", "content marketing", "digital marketing", "brand", "demand generation", "product marketing", "pmm", "cmo"],
    "Sales": ["sales", "account executive", "business development", "bdr", "sdr", "account manager", "sales manager", "vp sales", "cro", "revenue operations"],
    "Customer Success": ["customer success", "csm", "customer success manager", "renewals", "expansion"],
    "GTM & Partnerships": ["gtm", "go-to-market", "partnerships", "partner manager", "channel", "alliances", "strategic partnerships"],
    "HR & Recruiting": ["recruiter", "talent acquisition", "hr", "human resources", "people operations", "hrbp"],
    "Finance": ["finance", "accountant", "controller", "financial analyst", "cfo", "fp&a", "bookkeeper"],
    "Operations": ["operations", "ops manager", "chief of staff", "office manager", "business operations", "business applications"],
    "Legal": ["legal counsel", "lawyer", "attorney", "legal"],
}

DEFAULT_JOB_FAMILY = "Other"


def get_job_family(title: str) -> str:
    """Classify a job title into a job family."""
    if not title:
        return DEFAULT_JOB_FAMILY
    lower_title = title.lower()
    for family, keywords in JOB_FAMILIES.items():
        if any(keyword in lower_title for keyword in keywords):
            return family
    return DEFAULT_JOB_FAMILY


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
        titles: Optional[List[str]] = None,
        job_families: Optional[List[str]] = None,
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
            # Search primarily in job title for more relevant results
            # Also search in company name via join
            search_terms = search.strip().split()
            if len(search_terms) == 1:
                # Single word search - look in title only for better relevance
                search_filter = JobPosition.title.ilike(f"%{search}%")
            else:
                # Multi-word search - match all words in title
                title_filters = [JobPosition.title.ilike(f"%{term}%") for term in search_terms]
                search_filter = and_(*title_filters)
            filters.append(search_filter)
            filters_applied["search"] = search

        if company_ids:
            filters.append(JobPosition.company_id.in_(company_ids))
            filters_applied["company_ids"] = [str(cid) for cid in company_ids]

        if company_names:
            # Look up company IDs by name (case-insensitive)
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

        if titles:
            # Use partial match (contains) so "DevOps Engineer" matches "Senior DevOps Engineer"
            title_filters = [func.lower(JobPosition.title).contains(t.lower()) for t in titles]
            filters.append(or_(*title_filters))
            filters_applied["titles"] = titles

        if job_families:
            # Filter by job family - match titles that belong to selected job families
            family_filters = []
            for family in job_families:
                if family in JOB_FAMILIES:
                    # Match any keyword from this job family
                    for keyword in JOB_FAMILIES[family]:
                        family_filters.append(func.lower(JobPosition.title).contains(keyword))
                elif family == DEFAULT_JOB_FAMILY:
                    # For "Other" category, we need to exclude all known families
                    # This is complex, so we'll use a different approach
                    pass
            if family_filters:
                filters.append(or_(*family_filters))
            filters_applied["job_families"] = job_families

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
        # For posted_date, use COALESCE to fall back to first_seen_at for jobs without posted_date
        if sort_by == "posted_date":
            sort_expr = func.coalesce(JobPosition.posted_date, JobPosition.first_seen_at)
            if sort_order == "desc":
                query = query.order_by(sort_expr.desc().nullslast())
            else:
                query = query.order_by(sort_expr.asc().nullsfirst())
        else:
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

        # Get company counts - return all companies with active jobs for frontend filtering
        company_counts = (
            self.session.query(
                Company.name,
                func.count(JobPosition.id).label('count')
            )
            .join(JobPosition, JobPosition.company_id == Company.id)
            .filter(JobPosition.is_active == True)
            .group_by(Company.name)
            .order_by(func.count(JobPosition.id).desc())
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

        # Get job title counts (distinct titles from job_positions) - no limit, return all
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
            .all()
        )

        # Get industry category counts (from companies table - clustered industries)
        industry_counts = (
            self.session.query(
                Company.industry_category,
                func.count(JobPosition.id).label('count')
            )
            .join(JobPosition, JobPosition.company_id == Company.id)
            .filter(JobPosition.is_active == True)
            .filter(Company.industry_category.isnot(None))
            .filter(Company.industry_category != '')
            .filter(Company.industry_category != 'Other')  # Exclude 'Other' from filters
            .group_by(Company.industry_category)
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

        # Calculate job family counts by classifying each job title
        job_family_counts = defaultdict(int)
        for title, count in job_title_counts:
            if title:
                family = get_job_family(title)
                job_family_counts[family] += count

        # Sort job families by count descending
        sorted_job_families = sorted(
            job_family_counts.items(),
            key=lambda x: x[1],
            reverse=True
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
            "job_families": [
                {"value": family, "label": family, "count": count}
                for family, count in sorted_job_families
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

    def get_jobs_over_time(self, months: int = 12, active_only: bool = False) -> List[Dict[str, Any]]:
        """
        Get job posting counts grouped by month.

        Args:
            months: Number of months to look back (default: 12)
            active_only: If True, only count jobs that are still active/open (default: False)

        Returns:
            List of dicts with month and count
        """
        from datetime import timedelta
        from sqlalchemy import extract

        # Calculate the start date (beginning of month, N months ago)
        today = datetime.utcnow()
        start_date = datetime(today.year, today.month, 1) - timedelta(days=months * 31)
        start_date = datetime(start_date.year, start_date.month, 1)

        # Build query
        query = (
            self.session.query(
                extract('year', JobPosition.posted_date).label('year'),
                extract('month', JobPosition.posted_date).label('month'),
                func.count(JobPosition.id).label('count')
            )
            .filter(JobPosition.posted_date >= start_date)
            .filter(JobPosition.posted_date.isnot(None))
        )

        # Filter by active status if requested
        if active_only:
            query = query.filter(JobPosition.is_active == True)

        # Group and order
        results = (
            query
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
