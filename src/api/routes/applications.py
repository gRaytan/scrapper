"""Application API endpoints for job tracking."""
import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Query, status
from sqlalchemy.orm import Session

from src.storage.database import db
from src.services.application_service import ApplicationService
from src.auth.dependencies import get_current_active_user
from src.models.user import User
from src.api.schemas.application import (
    ApplicationCreate,
    ApplicationUpdate,
    ApplicationResponse,
    ApplicationListResponse,
    ApplicationStats,
    TrackJobResponse,
    JobBrief,
    CompanyBrief,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def get_db_session():
    """Dependency to get database session."""
    with db.get_session() as session:
        yield session


def _build_application_response(app) -> ApplicationResponse:
    """Build application response with job details."""
    job_brief = None
    if app.job_position:
        company_brief = None
        if app.job_position.company:
            company_brief = CompanyBrief(
                id=app.job_position.company.id,
                name=app.job_position.company.name,
                website=app.job_position.company.website,
                industry=app.job_position.company.industry,
            )
        job_brief = JobBrief(
            id=app.job_position.id,
            title=app.job_position.title,
            location=app.job_position.location,
            remote_type=app.job_position.remote_type,
            employment_type=app.job_position.employment_type,
            salary_range=app.job_position.salary_range,
            job_url=app.job_position.job_url,
            application_url=app.job_position.application_url,
            posted_date=app.job_position.posted_date,
            company=company_brief,
        )
    
    return ApplicationResponse(
        id=app.id,
        user_id=app.user_id,
        job_position_id=app.job_position_id,
        status=app.status,
        applied_at=app.applied_at,
        notes=app.notes,
        created_at=app.created_at,
        updated_at=app.updated_at,
        job_position=job_brief,
    )


@router.get("", response_model=ApplicationListResponse)
def list_applications(
    status: Optional[str] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_db_session)
):
    """
    List user's tracked jobs/applications.
    
    **Status values:**
    - interested: Saved/bookmarked
    - applied: Application submitted
    - interviewing: In interview process
    - offered: Received offer
    - accepted: Accepted offer
    - rejected: Application rejected
    - withdrawn: User withdrew application
    """
    try:
        service = ApplicationService(session)
        result = service.list_applications(
            user_id=current_user.id,
            status=status,
            page=page,
            page_size=page_size
        )
        
        applications = [_build_application_response(app) for app in result['applications']]
        
        return ApplicationListResponse(
            total=result['total'],
            page=result['page'],
            page_size=result['page_size'],
            total_pages=result['total_pages'],
            applications=applications,
        )
    except Exception as e:
        logger.error(f"Error listing applications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list applications"
        )


@router.post("", response_model=TrackJobResponse, status_code=status.HTTP_201_CREATED)
def track_job(
    data: ApplicationCreate,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_db_session)
):
    """
    Track a job (add to user's tracked jobs).
    """
    try:
        service = ApplicationService(session)
        application = service.track_job(
            user_id=current_user.id,
            job_position_id=data.job_position_id,
            status=data.status,
            notes=data.notes
        )
        
        return TrackJobResponse(
            message="Job tracked successfully",
            application=_build_application_response(application)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error tracking job: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to track job"
        )


@router.get("/stats", response_model=ApplicationStats)
def get_application_stats(
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_db_session)
):
    """Get application statistics for current user."""
    try:
        service = ApplicationService(session)
        stats = service.get_stats(current_user.id)
        return ApplicationStats(**stats)
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get statistics"
        )


@router.get("/check/{job_position_id}")
def check_job_tracked(
    job_position_id: UUID,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_db_session)
):
    """Check if a job is tracked by the current user."""
    try:
        service = ApplicationService(session)
        application = service.is_job_tracked(current_user.id, job_position_id)
        
        if application:
            return {
                "tracked": True,
                "application_id": str(application.id),
                "status": application.status
            }
        return {"tracked": False}
    except Exception as e:
        logger.error(f"Error checking job: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check job"
        )


@router.get("/{application_id}", response_model=ApplicationResponse)
def get_application(
    application_id: UUID,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_db_session)
):
    """Get a specific application by ID."""
    try:
        service = ApplicationService(session)
        application = service.get_application(application_id, current_user.id)
        
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found"
            )
        
        return _build_application_response(application)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting application: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get application"
        )


@router.patch("/{application_id}", response_model=ApplicationResponse)
def update_application(
    application_id: UUID,
    data: ApplicationUpdate,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_db_session)
):
    """Update an application's status or notes."""
    try:
        service = ApplicationService(session)
        application = service.update_application(
            application_id=application_id,
            user_id=current_user.id,
            status=data.status,
            notes=data.notes
        )
        
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found"
            )
        
        return _build_application_response(application)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating application: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update application"
        )


@router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
def untrack_job(
    application_id: UUID,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_db_session)
):
    """Remove a job from tracking (untrack)."""
    try:
        service = ApplicationService(session)
        deleted = service.untrack_job(application_id, current_user.id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found"
            )
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error untracking job: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to untrack job"
        )
