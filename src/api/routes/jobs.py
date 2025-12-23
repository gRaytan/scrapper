"""Job API endpoints."""
import logging
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Query, status
from sqlalchemy.orm import Session

from src.storage.database import db
from src.services.job_service import JobService
from src.services.personalized_job_service import PersonalizedJobService
from src.auth.dependencies import get_current_active_user
from src.models.user import User
from src.api.schemas.job import (
    JobListResponse,
    JobDetailResponse,
    PersonalizedJobsResponse,
    PersonalizedJobItem,
    JobListItem,
    FeedJobItem,
    FeedResponse,
    StarredJobsResponse,
    ArchivedJobsResponse,
    JobInteractionResponse,
    JobPreferencesUpdate,
    JobPreferencesResponse,
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


# ============ Personalized Feed Endpoints ============

def _job_to_feed_item(job, similarity_score: float, is_starred: bool, is_archived: bool) -> FeedJobItem:
    """Convert a JobPosition to FeedJobItem."""
    return FeedJobItem(
        id=job.id,
        title=job.title,
        location=job.location,
        remote_type=job.remote_type,
        employment_type=job.employment_type,
        department=job.department,
        seniority_level=job.seniority_level,
        company=job.company,
        description=job.description,
        salary_range=job.salary_range,
        requirements=job.requirements,
        benefits=job.benefits,
        job_url=job.job_url,
        application_url=job.application_url,
        posted_date=job.posted_date,
        status=job.status,
        is_active=job.is_active,
        source_type=job.source_type,
        created_at=job.created_at,
        similarity_score=similarity_score,
        is_starred=is_starred,
        is_archived=is_archived,
    )


@router.get("/feed", response_model=FeedResponse)
def get_job_feed(
    location: Optional[str] = Query(None, description="Filter by location"),
    days_back: int = Query(30, ge=1, le=365, description="How many days back to look"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_db_session)
):
    """
    Get personalized job feed based on user's job preferences.

    Uses semantic matching to find jobs that match the user's job_title and job_keywords.
    Jobs are sorted by similarity score (highest first), then by posted date.

    **Filters:**
    - **location**: Filter by job location (partial match)
    - **days_back**: How many days back to look for jobs (default: 30)

    **Pagination:**
    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 20, max: 100)

    **Note:** Archived jobs are excluded from the feed.
    Set job preferences using PATCH /jobs/preferences first.

    Requires JWT authentication.
    """
    try:
        service = PersonalizedJobService(session)
        result = service.get_personalized_feed(
            user=current_user,
            location=location,
            days_back=days_back,
            page=page,
            page_size=page_size
        )

        # Transform jobs to schema
        feed_jobs = [
            _job_to_feed_item(
                job_data["job"],
                job_data["similarity_score"],
                job_data["is_starred"],
                job_data["is_archived"]
            )
            for job_data in result["jobs"]
        ]

        return FeedResponse(
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"],
            total_pages=result["total_pages"],
            jobs=feed_jobs,
            user_preferences=result["user_preferences"]
        )
    except Exception as e:
        logger.error(f"Error getting job feed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get job feed"
        )


@router.get("/starred", response_model=StarredJobsResponse)
def get_starred_jobs(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_db_session)
):
    """
    Get user's starred jobs.

    Returns jobs that the user has starred, sorted by starred date (newest first).

    Requires JWT authentication.
    """
    try:
        service = PersonalizedJobService(session)
        jobs, total = service.get_starred_jobs(
            user_id=current_user.id,
            page=page,
            page_size=page_size
        )

        # Get interaction status
        job_ids = [j.id for j in jobs]
        interactions = service.get_user_interactions_map(current_user.id, job_ids)

        feed_jobs = [
            _job_to_feed_item(
                job,
                similarity_score=0.0,  # Not applicable for starred list
                is_starred=interactions.get(job.id, {}).get("is_starred", True),
                is_archived=interactions.get(job.id, {}).get("is_archived", False)
            )
            for job in jobs
        ]

        total_pages = (total + page_size - 1) // page_size

        return StarredJobsResponse(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            jobs=feed_jobs
        )
    except Exception as e:
        logger.error(f"Error getting starred jobs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get starred jobs"
        )


@router.get("/archived", response_model=ArchivedJobsResponse)
def get_archived_jobs(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_db_session)
):
    """
    Get user's archived jobs.

    Returns jobs that the user has archived, sorted by archived date (newest first).

    Requires JWT authentication.
    """
    try:
        service = PersonalizedJobService(session)
        jobs, total = service.get_archived_jobs(
            user_id=current_user.id,
            page=page,
            page_size=page_size
        )

        # Get interaction status
        job_ids = [j.id for j in jobs]
        interactions = service.get_user_interactions_map(current_user.id, job_ids)

        feed_jobs = [
            _job_to_feed_item(
                job,
                similarity_score=0.0,
                is_starred=interactions.get(job.id, {}).get("is_starred", False),
                is_archived=interactions.get(job.id, {}).get("is_archived", True)
            )
            for job in jobs
        ]

        total_pages = (total + page_size - 1) // page_size

        return ArchivedJobsResponse(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            jobs=feed_jobs
        )
    except Exception as e:
        logger.error(f"Error getting archived jobs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get archived jobs"
        )




@router.post("/{job_id}/star", response_model=JobInteractionResponse)
def star_job(
    job_id: UUID,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_db_session)
):
    """
    Star a job.

    Adds the job to the user's starred list.

    Requires JWT authentication.
    """
    try:
        # Verify job exists
        job_service = JobService(session)
        job = job_service.get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )

        service = PersonalizedJobService(session)
        interaction = service.star_job(current_user.id, job_id)

        return JobInteractionResponse(
            job_id=job_id,
            is_starred=interaction.is_starred,
            is_archived=interaction.is_archived,
            message="Job starred successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starring job {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to star job"
        )


@router.delete("/{job_id}/star", response_model=JobInteractionResponse)
def unstar_job(
    job_id: UUID,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_db_session)
):
    """
    Unstar a job.

    Removes the job from the user's starred list.

    Requires JWT authentication.
    """
    try:
        service = PersonalizedJobService(session)
        interaction = service.unstar_job(current_user.id, job_id)

        return JobInteractionResponse(
            job_id=job_id,
            is_starred=interaction.is_starred,
            is_archived=interaction.is_archived,
            message="Job unstarred successfully"
        )
    except Exception as e:
        logger.error(f"Error unstarring job {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unstar job"
        )


@router.post("/{job_id}/archive", response_model=JobInteractionResponse)
def archive_job(
    job_id: UUID,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_db_session)
):
    """
    Archive a job.

    Archived jobs are hidden from the personalized feed.

    Requires JWT authentication.
    """
    try:
        # Verify job exists
        job_service = JobService(session)
        job = job_service.get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )

        service = PersonalizedJobService(session)
        interaction = service.archive_job(current_user.id, job_id)

        return JobInteractionResponse(
            job_id=job_id,
            is_starred=interaction.is_starred,
            is_archived=interaction.is_archived,
            message="Job archived successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error archiving job {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to archive job"
        )


@router.delete("/{job_id}/archive", response_model=JobInteractionResponse)
def unarchive_job(
    job_id: UUID,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_db_session)
):
    """
    Unarchive a job.

    Restores the job to the personalized feed.

    Requires JWT authentication.
    """
    try:
        service = PersonalizedJobService(session)
        interaction = service.unarchive_job(current_user.id, job_id)

        return JobInteractionResponse(
            job_id=job_id,
            is_starred=interaction.is_starred,
            is_archived=interaction.is_archived,
            message="Job unarchived successfully"
        )
    except Exception as e:
        logger.error(f"Error unarchiving job {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unarchive job"
        )


@router.get("/preferences", response_model=JobPreferencesResponse)
def get_job_preferences(
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_db_session)
):
    """
    Get user's job preferences.

    Returns the user's job_title and job_keywords used for personalized feed matching.

    Requires JWT authentication.
    """
    return JobPreferencesResponse(
        job_title=current_user.preferences.get("job_title"),
        job_keywords=current_user.preferences.get("job_keywords", []),
        updated_at=current_user.updated_at
    )


@router.patch("/preferences", response_model=JobPreferencesResponse)
def update_job_preferences(
    preferences: JobPreferencesUpdate,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_db_session)
):
    """
    Update user's job preferences.

    Updates the user's job_title and/or job_keywords used for personalized feed matching.
    This also recomputes the query embedding for semantic matching.

    **Fields:**
    - **job_title**: Target job title (e.g., "Software Engineer")
    - **job_keywords**: List of keywords to match (e.g., ["Python", "Backend", "FastAPI"])

    Requires JWT authentication.
    """
    try:
        service = PersonalizedJobService(session)
        updated_user = service.update_user_job_preferences(
            user=current_user,
            job_title=preferences.job_title,
            job_keywords=preferences.job_keywords
        )

        return JobPreferencesResponse(
            job_title=updated_user.preferences.get("job_title"),
            job_keywords=updated_user.preferences.get("job_keywords", []),
            updated_at=updated_user.updated_at
        )
    except Exception as e:
        logger.error(f"Error updating job preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update job preferences"
        )