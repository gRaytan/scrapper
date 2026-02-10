"""Application schemas for API."""
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class ApplicationCreate(BaseModel):
    """Schema for creating a new application (tracking a job)."""
    job_position_id: UUID = Field(..., description="Job position UUID to track")
    status: str = Field(default='interested', description="Initial status")
    notes: Optional[str] = Field(None, description="Optional notes")


class ApplicationUpdate(BaseModel):
    """Schema for updating an application."""
    status: Optional[str] = Field(None, description="New status")
    notes: Optional[str] = Field(None, description="Updated notes")


class CompanyBrief(BaseModel):
    """Brief company info for application response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    name: str
    website: Optional[str] = None
    industry: Optional[str] = None


class JobBrief(BaseModel):
    """Brief job info for application response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    title: str
    location: Optional[str] = None
    remote_type: Optional[str] = None
    employment_type: Optional[str] = None
    salary_range: Optional[dict] = None
    job_url: Optional[str] = None
    application_url: Optional[str] = None
    posted_date: Optional[datetime] = None
    company: Optional[CompanyBrief] = None


class ApplicationResponse(BaseModel):
    """Schema for application response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    user_id: UUID
    job_position_id: UUID
    status: str
    applied_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    job: Optional[JobBrief] = Field(None, alias='job_position')


class ApplicationListResponse(BaseModel):
    """Schema for paginated application list."""
    total: int
    page: int
    page_size: int
    total_pages: int
    applications: List[ApplicationResponse]


class ApplicationStats(BaseModel):
    """Schema for application statistics."""
    total: int = 0
    interested: int = 0
    applied: int = 0
    interviewing: int = 0
    offered: int = 0
    accepted: int = 0
    rejected: int = 0
    withdrawn: int = 0


class TrackJobResponse(BaseModel):
    """Response for tracking a job."""
    message: str
    application: ApplicationResponse


class ManualJobCreate(BaseModel):
    """Schema for creating a manual job to track."""
    title: str = Field(..., description="Job title", min_length=1, max_length=255)
    company_name: str = Field(..., description="Company name", min_length=1, max_length=255)
    location: Optional[str] = Field(None, description="Job location")
    job_url: Optional[str] = Field(None, description="URL to job posting")
    application_url: Optional[str] = Field(None, description="URL to apply")
    salary_min: Optional[int] = Field(None, description="Minimum salary")
    salary_max: Optional[int] = Field(None, description="Maximum salary")
    salary_currency: Optional[str] = Field(default="USD", description="Salary currency")
    remote_type: Optional[str] = Field(None, description="Remote type: remote, hybrid, onsite")
    employment_type: Optional[str] = Field(None, description="Employment type: fulltime, parttime, contract")
    status: str = Field(default='interested', description="Initial tracking status")
    notes: Optional[str] = Field(None, description="Optional notes")
