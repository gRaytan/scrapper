"""Company service for business logic."""
import logging
import math
from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import func

from src.storage.repositories.company_repo import CompanyRepository
from src.models.job_position import JobPosition
from src.api.schemas.company import CompanyCreate, CompanyUpdate, CompanyStats

logger = logging.getLogger(__name__)


class CompanyService:
    """Service for company-related business logic."""
    
    def __init__(self, session: Session):
        """Initialize service with database session."""
        self.session = session
        self.company_repo = CompanyRepository(session)
    
    def create_company(self, company_data: CompanyCreate) -> dict:
        """
        Create a new company.
        
        Args:
            company_data: Company creation data
            
        Returns:
            Created company
            
        Raises:
            ValueError: If company name already exists
        """
        # Check if company already exists
        existing_company = self.company_repo.get_by_name(company_data.name)
        if existing_company:
            raise ValueError(f"Company with name {company_data.name} already exists")
        
        # Prepare company data
        company_dict = {
            "name": company_data.name,
            "website": str(company_data.website) if company_data.website else None,
            "careers_url": str(company_data.careers_url) if company_data.careers_url else None,
            "industry": company_data.industry,
            "size": company_data.size,
            "location": company_data.location,
            "is_active": company_data.is_active,
            "scraping_config": company_data.scraping_config or {},
        }
        
        # Create company
        company = self.company_repo.create(company_dict)
        return company
    
    def get_company(self, company_id: UUID, include_stats: bool = False) -> Optional[dict]:
        """
        Get company by ID.
        
        Args:
            company_id: Company UUID
            include_stats: Whether to include company statistics
            
        Returns:
            Company data with optional stats, or None if not found
        """
        company = self.company_repo.get_by_id(company_id)
        if not company:
            return None
        
        if include_stats:
            stats = self._get_company_stats(company_id)
            return {"company": company, "stats": stats}
        
        return company
    
    def list_companies(
        self,
        page: int = 1,
        page_size: int = 20,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        List companies with pagination and filtering.
        
        Args:
            page: Page number (1-indexed)
            page_size: Number of items per page
            is_active: Filter by active status
            search: Search query for company name
            
        Returns:
            Dictionary with companies and pagination info
        """
        from src.models.company import Company
        
        # Build query
        query = self.session.query(Company)
        
        # Apply filters
        if is_active is not None:
            query = query.filter(Company.is_active == is_active)
        
        if search:
            query = query.filter(Company.name.ilike(f"%{search}%"))
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * page_size
        companies = query.order_by(Company.name).offset(offset).limit(page_size).all()
        
        # Add job counts to each company
        companies_with_counts = []
        for company in companies:
            active_jobs = self.session.query(JobPosition).filter(
                JobPosition.company_id == company.id,
                JobPosition.is_active == True
            ).count()
            
            total_jobs = self.session.query(JobPosition).filter(
                JobPosition.company_id == company.id
            ).count()
            
            company_dict = {
                "company": company,
                "active_jobs_count": active_jobs,
                "total_jobs_count": total_jobs,
            }
            companies_with_counts.append(company_dict)
        
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "companies": companies_with_counts,
        }
    
    def update_company(self, company_id: UUID, update_data: CompanyUpdate) -> Optional[dict]:
        """
        Update company.
        
        Args:
            company_id: Company UUID
            update_data: Update data
            
        Returns:
            Updated company or None if not found
        """
        # Prepare update dict (only include non-None values)
        update_dict = {}
        if update_data.name is not None:
            update_dict["name"] = update_data.name
        if update_data.website is not None:
            update_dict["website"] = str(update_data.website)
        if update_data.careers_url is not None:
            update_dict["careers_url"] = str(update_data.careers_url)
        if update_data.industry is not None:
            update_dict["industry"] = update_data.industry
        if update_data.size is not None:
            update_dict["size"] = update_data.size
        if update_data.location is not None:
            update_dict["location"] = update_data.location
        if update_data.is_active is not None:
            update_dict["is_active"] = update_data.is_active
        if update_data.scraping_config is not None:
            update_dict["scraping_config"] = update_data.scraping_config

        if not update_dict:
            # No updates provided
            return self.company_repo.get_by_id(company_id)

        return self.company_repo.update(company_id, update_dict)

    def delete_company(self, company_id: UUID) -> bool:
        """
        Delete company (soft delete - mark as inactive).

        Args:
            company_id: Company UUID

        Returns:
            True if deleted, False if not found
        """
        company = self.company_repo.get_by_id(company_id)
        if not company:
            return False

        # Soft delete by marking as inactive
        self.company_repo.update(company_id, {"is_active": False})
        return True

    def _get_company_stats(self, company_id: UUID) -> CompanyStats:
        """
        Get company statistics.

        Args:
            company_id: Company UUID

        Returns:
            Company statistics
        """
        from src.models.company import Company

        company = self.company_repo.get_by_id(company_id)

        # Count active jobs
        active_jobs = self.session.query(JobPosition).filter(
            JobPosition.company_id == company_id,
            JobPosition.is_active == True
        ).count()

        # Count total jobs
        total_jobs = self.session.query(JobPosition).filter(
            JobPosition.company_id == company_id
        ).count()

        return CompanyStats(
            active_jobs=active_jobs,
            total_jobs=total_jobs,
            last_scraped_at=company.last_scraped_at if company else None,
            scraping_frequency=company.scraping_frequency if company else None,
        )

