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
