"""Pydantic schemas for Company API."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, HttpUrl, Field, ConfigDict


class CompanyBase(BaseModel):
    """Base company schema with common fields."""
    name: str = Field(..., min_length=1, max_length=255)
    website: Optional[str] = None
    careers_url: Optional[str] = None
    industry: Optional[str] = None
    size: Optional[str] = None
    location: Optional[str] = None


class CompanyCreate(CompanyBase):
    """Schema for creating a new company."""
    is_active: bool = True
    scraping_config: Optional[dict] = Field(default_factory=dict)


class CompanyUpdate(BaseModel):
    """Schema for updating a company."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    website: Optional[str] = None
    careers_url: Optional[str] = None
    industry: Optional[str] = None
    size: Optional[str] = None
    location: Optional[str] = None
    is_active: Optional[bool] = None
    scraping_config: Optional[dict] = None


class CompanyStats(BaseModel):
    """Company statistics."""
    active_jobs: int = 0
    total_jobs: int = 0
    last_scraped_at: Optional[datetime] = None
    scraping_frequency: Optional[str] = None


class CompanyListItem(CompanyBase):
    """Schema for company in list view."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    is_active: bool
    active_jobs_count: int = 0
    total_jobs_count: int = 0
    last_scraped_at: Optional[datetime] = None
    created_at: datetime


class CompanyResponse(CompanyBase):
    """Schema for company response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    is_active: bool
    scraping_config: dict
    created_at: datetime
    updated_at: datetime


class CompanyDetailResponse(CompanyResponse):
    """Schema for detailed company response with stats."""
    stats: Optional[CompanyStats] = None


class CompanyListResponse(BaseModel):
    """Schema for paginated company list response."""
    total: int
    page: int
    page_size: int
    companies: list[CompanyListItem]

