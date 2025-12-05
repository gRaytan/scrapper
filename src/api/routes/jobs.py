"""Job API endpoints."""
import logging
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Query, status
from sqlalchemy.orm import Session

from src.storage.database import db
from src.services.job_service import JobService
from src.auth.dependencies import get_current_active_user
from src.models.user import User
from src.api.schemas.job import (
    JobListResponse,
    JobDetailResponse,
    PersonalizedJobsResponse,
    PersonalizedJobItem,
    JobListItem,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def get_db_session():
    """Dependency to get database session."""
    with db.get_session() as session:
        yield session


@router.get("/me/personalized", response_model=PersonalizedJobsResponse)
def get_personalized_jobs(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_db_session)
):
    """
    Get personalized jobs for current user based on their active alerts.

    Returns jobs that match ANY of the user's active alerts, sorted by posted date (newest first).
    Each job includes information about which alerts it matched.

    **Pagination:**
    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 20, max: 100)

    **Response includes:**
    - List of jobs with match information
    - Names of alerts that matched each job
    - Total count of matching jobs
    - Number of active alerts used for matching

    Requires JWT authentication.
    """
    try:
        service = JobService(session)
        result = service.get_personalized_jobs(
            user_id=current_user.id,
            page=page,
            page_size=page_size
        )

        # Transform jobs to match schema
        personalized_jobs = []
        for job_data in result["jobs"]:
            job_item = JobListItem.model_validate(job_data["job"])
            personalized_jobs.append(PersonalizedJobItem(
                job=job_item,
                matched_alerts=job_data["matched_alerts"],
                match_count=job_data["match_count"]
            ))

        return PersonalizedJobsResponse(
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"],
            total_pages=result["total_pages"],
            jobs=personalized_jobs,
            alert_count=result["alert_count"]
        )
    except Exception as e:
        logger.error(f"Error getting personalized jobs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get personalized jobs"
        )


@router.get("", response_model=JobListResponse)
def list_jobs(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search in title and description"),
    company_ids: Optional[List[UUID]] = Query(None, description="Filter by company IDs"),
    locations: Optional[List[str]] = Query(None, description="Filter by locations"),
    departments: Optional[List[str]] = Query(None, description="Filter by departments"),
    remote_type: Optional[List[str]] = Query(None, description="Filter by remote type (remote, hybrid, onsite)"),
    employment_type: Optional[List[str]] = Query(None, description="Filter by employment type"),
    seniority_level: Optional[List[str]] = Query(None, description="Filter by seniority level"),
    posted_after: Optional[datetime] = Query(None, description="Filter by posted date (ISO format)"),
    is_active: Optional[bool] = Query(True, description="Filter by active status"),
    sort_by: str = Query("posted_date", description="Field to sort by"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_db_session)
):
    """
    List jobs with filtering, pagination, and sorting.
    
    **Filters:**
    - **search**: Search in job title and description
    - **company_ids**: Filter by specific companies
    - **locations**: Filter by job locations
    - **departments**: Filter by departments
    - **remote_type**: Filter by remote/hybrid/onsite
    - **employment_type**: Filter by full-time/part-time/contract/internship
    - **seniority_level**: Filter by entry/mid/senior/lead/executive
    - **posted_after**: Only jobs posted after this date
    - **is_active**: Show only active jobs (default: true)
    
    **Sorting:**
    - **sort_by**: Field to sort by (default: posted_date)
    - **sort_order**: asc or desc (default: desc)
    
    **Pagination:**
    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 20, max: 100)
    """
    try:
        service = JobService(session)
        result = service.list_jobs(
            page=page,
            page_size=page_size,
            search=search,
            company_ids=company_ids,
            locations=locations,
            departments=departments,
            remote_type=remote_type,
            employment_type=employment_type,
            seniority_level=seniority_level,
            posted_after=posted_after,
            is_active=is_active,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        
        return JobListResponse(**result)
    except Exception as e:
        logger.error(f"Error listing jobs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list jobs"
        )


@router.get("/{job_id}", response_model=JobDetailResponse)
def get_job(
    job_id: UUID,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_db_session)
):
    """
    Get job details by ID.

    - **job_id**: Job UUID

    Returns detailed job information including company details.
    Requires JWT authentication.
    """
    try:
        service = JobService(session)
        job = service.get_job(job_id)
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )
        
        return job
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get job"
        )

