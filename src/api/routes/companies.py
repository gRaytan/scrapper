"""Company API endpoints."""
import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Query, status
from sqlalchemy.orm import Session

from src.storage.database import db
from src.services.company_service import CompanyService
from src.services.job_service import JobService
from src.auth.dependencies import get_current_active_user
from src.models.user import User
from src.api.schemas.company import (
    CompanyCreate,
    CompanyUpdate,
    CompanyResponse,
    CompanyDetailResponse,
    CompanyListResponse,
)
from src.api.schemas.job import JobListResponse

logger = logging.getLogger(__name__)

router = APIRouter()


def get_db_session():
    """Dependency to get database session."""
    with db.get_session() as session:
        yield session


@router.get("", response_model=CompanyListResponse)
def list_companies(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search company name"),
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_db_session)
):
    """
    List companies with pagination and filtering.

    **Filters:**
    - **is_active**: Filter by active status
    - **search**: Search in company name

    **Pagination:**
    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 20, max: 100)

    Requires JWT authentication.
    """
    try:
        service = CompanyService(session)
        result = service.list_companies(
            page=page,
            page_size=page_size,
            is_active=is_active,
            search=search,
        )
        
        # Transform result to match schema
        companies_list = []
        for item in result["companies"]:
            company = item["company"]
            companies_list.append({
                **company.__dict__,
                "active_jobs_count": item["active_jobs_count"],
                "total_jobs_count": item["total_jobs_count"],
            })
        
        return CompanyListResponse(
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"],
            companies=companies_list,
        )
    except Exception as e:
        logger.error(f"Error listing companies: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list companies"
        )


@router.get("/{company_id}", response_model=CompanyDetailResponse)
def get_company(
    company_id: UUID,
    include_stats: bool = Query(False, description="Include company statistics"),
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_db_session)
):
    """
    Get company details by ID.
    
    - **company_id**: Company UUID
    - **include_stats**: Include statistics (job counts, scraping info)
    """
    try:
        service = CompanyService(session)
        result = service.get_company(company_id, include_stats=include_stats)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Company {company_id} not found"
            )
        
        if include_stats and isinstance(result, dict):
            return CompanyDetailResponse(
                **result["company"].__dict__,
                stats=result["stats"]
            )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting company {company_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get company"
        )


@router.post("", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
def create_company(
    company_data: CompanyCreate,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_db_session)
):
    """
    Create a new company.
    
    - **name**: Company name (must be unique)
    - **website**: Company website URL (optional)
    - **careers_url**: Careers page URL (optional)
    - **industry**: Industry (optional)
    - **size**: Company size (optional)
    - **location**: Company location (optional)
    - **scraping_config**: Scraping configuration (optional)
    """
    try:
        service = CompanyService(session)
        company = service.create_company(company_data)
        return company
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating company: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create company"
        )


@router.patch("/{company_id}", response_model=CompanyResponse)
def update_company(
    company_id: UUID,
    update_data: CompanyUpdate,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_db_session)
):
    """
    Update company.

    - **company_id**: Company UUID
    - **name**: Updated company name (optional)
    - **website**: Updated website URL (optional)
    - **careers_url**: Updated careers URL (optional)
    - **industry**: Updated industry (optional)
    - **size**: Updated company size (optional)
    - **location**: Updated location (optional)
    - **is_active**: Updated active status (optional)
    - **scraping_config**: Updated scraping config (optional)
    """
    try:
        service = CompanyService(session)
        company = service.update_company(company_id, update_data)

        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Company {company_id} not found"
            )

        return company
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating company {company_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update company"
        )


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_company(
    company_id: UUID,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_db_session)
):
    """
    Delete company (soft delete - marks as inactive).

    - **company_id**: Company UUID

    Note: This is a soft delete. The company will be marked as inactive.
    """
    try:
        service = CompanyService(session)
        deleted = service.delete_company(company_id)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Company {company_id} not found"
            )

        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting company {company_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete company"
        )


@router.get("/{company_id}/jobs", response_model=JobListResponse)
def get_company_jobs(
    company_id: UUID,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    is_active: Optional[bool] = Query(True, description="Filter by active status"),
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_db_session)
):
    """
    Get all jobs for a specific company.

    - **company_id**: Company UUID
    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 20, max: 100)
    - **is_active**: Filter by active status (default: true)
    """
    try:
        # First verify company exists
        company_service = CompanyService(session)
        company = company_service.get_company(company_id)

        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Company {company_id} not found"
            )

        # Get jobs for this company
        job_service = JobService(session)
        result = job_service.list_jobs(
            page=page,
            page_size=page_size,
            company_ids=[company_id],
            is_active=is_active,
        )

        return JobListResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting jobs for company {company_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get company jobs"
        )

