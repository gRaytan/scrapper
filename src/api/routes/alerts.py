"""Alert API endpoints."""
import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Query, status
from sqlalchemy.orm import Session

from src.storage.database import db
from src.services.alert_service import AlertService
from src.auth.dependencies import get_current_active_user
from src.models.user import User
from src.api.schemas.alert import (
    AlertCreate,
    AlertUpdate,
    AlertResponse,
    AlertDetailResponse,
    AlertListResponse,
    AlertTestResponse,
    JobMatchPreview,
    AlertMatchingJobsResponse,
    JobMatchFull,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def get_db_session():
    """Dependency to get database session."""
    with db.get_session() as session:
        yield session


@router.get("/users/me/alerts", response_model=AlertListResponse)
def list_current_user_alerts(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_db_session)
):
    """
    Get all alerts for current user.

    Requires JWT authentication.
    """
    try:
        service = AlertService(session)
        alerts = service.list_user_alerts(current_user.id, is_active=is_active)
        return {
            "total": len(alerts),
            "alerts": alerts
        }
    except Exception as e:
        logger.error(f"Error listing alerts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list alerts"
        )


@router.get("/users/{user_id}/alerts", response_model=AlertListResponse)
def list_user_alerts(
    user_id: UUID,
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_db_session)
):
    """
    Get all alerts for a user.

    Users can only access their own alerts.
    Requires JWT authentication.
    """
    # Users can only access their own alerts
    if user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own alerts"
        )

    try:
        service = AlertService(session)
        alerts = service.list_user_alerts(user_id, is_active=is_active)
        
        return AlertListResponse(
            total=len(alerts),
            alerts=alerts,
        )
    except Exception as e:
        logger.error(f"Error listing alerts for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list alerts"
        )


@router.get("/alerts/{alert_id}", response_model=AlertDetailResponse)
def get_alert(
    alert_id: UUID,
    include_stats: bool = Query(False, description="Include alert statistics"),
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_db_session)
):
    """
    Get alert details by ID.

    - **alert_id**: Alert UUID
    - **include_stats**: Include statistics (matching jobs count, trigger count)

    Users can only access their own alerts.
    Requires JWT authentication.
    """
    try:
        service = AlertService(session)
        result = service.get_alert(alert_id, include_stats=include_stats)

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alert {alert_id} not found"
            )

        # Check ownership
        alert = result if not isinstance(result, dict) else result["alert"]
        if alert.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access your own alerts"
            )

        if include_stats and isinstance(result, dict):
            return AlertDetailResponse(
                **result["alert"].__dict__,
                stats=result["stats"]
            )

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting alert {alert_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get alert"
        )


@router.post("/users/me/alerts", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
def create_alert_for_current_user(
    alert_data: AlertCreate,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_db_session)
):
    """
    Create a new alert for current user.

    - **name**: Alert name
    - **company_ids**: List of company IDs to monitor (optional)
    - **keywords**: Keywords to match in job title/description (optional)
    - **excluded_keywords**: Keywords to exclude (optional)
    - **locations**: Locations to filter (optional)
    - **departments**: Departments to filter (optional)
    - **employment_types**: Employment types to filter (optional)
    - **remote_types**: Remote types to filter (optional)
    - **seniority_levels**: Seniority levels to filter (optional)
    - **notification_method**: Notification method (email/webhook/push)
    - **notification_config**: Notification configuration

    Requires JWT authentication.

    Note: When an alert is created, it automatically matches against existing
    jobs from the last 30 days and creates notifications for matching jobs.
    """
    try:
        service = AlertService(session)
        result = service.create_alert(current_user.id, alert_data)
        # Log matching stats if available
        if result.get("existing_jobs_matched"):
            matches = result["existing_jobs_matched"]
            logger.info(
                f"Alert created with {matches.get('matches_found', 0)} existing job matches"
            )
        return result["alert"]
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating alert: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create alert"
        )


@router.post("/users/{user_id}/alerts", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
def create_alert(
    user_id: UUID,
    alert_data: AlertCreate,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_db_session)
):
    """
    Create a new alert for a user.

    Users can only create alerts for themselves.
    Requires JWT authentication.

    Note: When an alert is created, it automatically matches against existing
    jobs from the last 30 days and creates notifications for matching jobs.
    """
    # Users can only create alerts for themselves
    if user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only create alerts for yourself"
        )

    try:
        service = AlertService(session)
        result = service.create_alert(user_id, alert_data)
        # Log matching stats if available
        if result.get("existing_jobs_matched"):
            matches = result["existing_jobs_matched"]
            logger.info(
                f"Alert created with {matches.get('matches_found', 0)} existing job matches"
            )
        return result["alert"]
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating alert for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create alert"
        )


@router.patch("/alerts/{alert_id}", response_model=AlertResponse)
def update_alert(
    alert_id: UUID,
    update_data: AlertUpdate,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_db_session)
):
    """
    Update alert.

    - **alert_id**: Alert UUID
    - All fields are optional and will only update if provided

    Users can only update their own alerts.
    Requires JWT authentication.
    """
    try:
        service = AlertService(session)

        # First get the alert to check ownership
        alert = service.get_alert(alert_id, include_stats=False)
        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alert {alert_id} not found"
            )

        # Check ownership
        if alert.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own alerts"
            )

        # Update the alert
        updated_alert = service.update_alert(alert_id, update_data)
        return updated_alert
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating alert {alert_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update alert"
        )


@router.delete("/alerts/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_alert(
    alert_id: UUID,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_db_session)
):
    """
    Delete alert.

    - **alert_id**: Alert UUID

    Users can only delete their own alerts.
    Requires JWT authentication.
    """
    try:
        service = AlertService(session)

        # First get the alert to check ownership
        alert = service.get_alert(alert_id, include_stats=False)
        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alert {alert_id} not found"
            )

        # Check ownership
        if alert.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own alerts"
            )

        # Delete the alert
        deleted = service.delete_alert(alert_id)
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting alert {alert_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete alert"
        )


@router.post("/alerts/{alert_id}/test", response_model=AlertTestResponse)
def test_alert(
    alert_id: UUID,
    limit: int = Query(10, ge=1, le=50, description="Max sample jobs to return"),
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_db_session)
):
    """
    Test alert by finding matching jobs.

    - **alert_id**: Alert UUID
    - **limit**: Maximum number of sample jobs to return (default: 10, max: 50)

    Returns a preview of jobs that match the alert criteria.
    Users can only test their own alerts.
    Requires JWT authentication.
    """
    try:
        service = AlertService(session)

        # First get the alert to check ownership
        alert = service.get_alert(alert_id, include_stats=False)
        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alert {alert_id} not found"
            )

        # Check ownership
        if alert.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only test your own alerts"
            )

        result = service.test_alert(alert_id, limit=limit)

        # Transform sample jobs to match schema
        sample_jobs = []
        for job in result["sample_jobs"]:
            sample_jobs.append(JobMatchPreview(
                id=job.id,
                title=job.title,
                company={
                    "id": str(job.company.id),
                    "name": job.company.name,
                },
                location=job.location,
                match_score=1.0,  # TODO: Implement actual match scoring
                matched_criteria=["keywords"],  # TODO: Implement criteria tracking
            ))

        return AlertTestResponse(
            matching_jobs_count=result["matching_jobs_count"],
            sample_jobs=sample_jobs,
            total_active_jobs=result["total_active_jobs"],
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error testing alert {alert_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to test alert"
        )

@router.get("/alerts/{alert_id}/matches", response_model=AlertMatchingJobsResponse)
def get_alert_matching_jobs(
    alert_id: UUID,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_db_session)
):
    """
    Get ALL jobs matching an alert.

    - **alert_id**: Alert UUID

    Returns all jobs that match the alert criteria (not just a sample).
    Users can only access their own alerts.
    Requires JWT authentication.
    """
    try:
        from datetime import datetime

        service = AlertService(session)

        # First get the alert to check ownership
        alert = service.get_alert(alert_id, include_stats=False)
        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alert {alert_id} not found"
            )

        # Check ownership
        if alert.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access your own alerts"
            )

        result = service.get_all_matching_jobs(alert_id)

        # Transform jobs to match schema
        jobs = []
        for job in result["jobs"]:
            jobs.append(JobMatchFull(
                id=job.id,
                title=job.title,
                company={
                    "id": str(job.company.id),
                    "name": job.company.name,
                },
                location=job.location,
                department=job.department,
                description=job.description,
                posted_date=job.posted_date,
                job_url=job.job_url,
                external_id=job.external_id,
                remote_type=job.remote_type,
                employment_type=job.employment_type,
                match_score=1.0,  # TODO: Implement actual match scoring
                matched_criteria=["keywords"],  # TODO: Implement criteria tracking
            ))

        return AlertMatchingJobsResponse(
            matching_jobs_count=result["matching_jobs_count"],
            jobs=jobs,
            total_active_jobs=result["total_active_jobs"],
            retrieved_at=datetime.utcnow(),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting matching jobs for alert {alert_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get matching jobs"
        )


