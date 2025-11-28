"""
Repository for Company model operations.
"""
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from src.models.company import Company
from src.utils.logger import logger


class CompanyRepository:
    """Repository for Company CRUD operations."""
    
    def __init__(self, session: Session):
        """Initialize repository with database session."""
        self.session = session
    
    def create(self, company_data: dict) -> Company:
        """
        Create a new company.
        
        Args:
            company_data: Dictionary with company fields
            
        Returns:
            Created Company instance
        """
        company = Company(**company_data)
        self.session.add(company)
        self.session.commit()
        self.session.refresh(company)
        logger.info(f"Created company: {company.name} ({company.id})")
        return company
    
    def get_by_id(self, company_id: UUID) -> Optional[Company]:
        """Get company by ID."""
        return self.session.query(Company).filter(Company.id == company_id).first()
    
    def get_by_name(self, name: str) -> Optional[Company]:
        """Get company by name."""
        return self.session.query(Company).filter(Company.name == name).first()
    
    def get_by_website(self, website: str) -> Optional[Company]:
        """Get company by website URL."""
        return self.session.query(Company).filter(Company.website == website).first()
    
    def get_all(self, is_active: Optional[bool] = None) -> List[Company]:
        """
        Get all companies.
        
        Args:
            is_active: Filter by active status (None = all)
            
        Returns:
            List of Company instances
        """
        query = self.session.query(Company)
        if is_active is not None:
            query = query.filter(Company.is_active == is_active)
        return query.all()
    
    def update(self, company_id: UUID, update_data: dict) -> Optional[Company]:
        """
        Update company.
        
        Args:
            company_id: Company UUID
            update_data: Dictionary with fields to update
            
        Returns:
            Updated Company instance or None if not found
        """
        company = self.get_by_id(company_id)
        if not company:
            logger.warning(f"Company not found: {company_id}")
            return None
        
        for key, value in update_data.items():
            if hasattr(company, key):
                setattr(company, key, value)
        
        self.session.commit()
        self.session.refresh(company)
        logger.info(f"Updated company: {company.name} ({company.id})")
        return company
    
    def delete(self, company_id: UUID) -> bool:
        """
        Delete company (soft delete by setting is_active=False).
        
        Args:
            company_id: Company UUID
            
        Returns:
            True if deleted, False if not found
        """
        company = self.get_by_id(company_id)
        if not company:
            logger.warning(f"Company not found: {company_id}")
            return False
        
        company.is_active = False
        self.session.commit()
        logger.info(f"Soft deleted company: {company.name} ({company.id})")
        return True
    
    def get_or_create(self, name: str, defaults: dict) -> tuple[Company, bool]:
        """
        Get existing company or create new one.
        
        Args:
            name: Company name
            defaults: Default values for creation
            
        Returns:
            Tuple of (Company instance, created boolean)
        """
        company = self.get_by_name(name)
        if company:
            return company, False
        
        company_data = {"name": name, **defaults}
        company = self.create(company_data)
        return company, True

