"""Pydantic schemas for Job API."""
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class SalaryRange(BaseModel):
    """Salary range schema."""
    min: Optional[float] = None
    max: Optional[float] = None
    currency: str = "USD"


class CompanyBrief(BaseModel):
    """Brief company information for job listings."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    name: str
    website: Optional[str] = None
    industry: Optional[str] = None
    logo_url: Optional[str] = None


class JobBase(BaseModel):
    """Base job schema with common fields."""
    title: str
    location: Optional[str] = None
    remote_type: Optional[str] = None
    employment_type: Optional[str] = None
    department: Optional[str] = None
    seniority_level: Optional[str] = None


class JobListItem(JobBase):
    """Schema for job in list view (brief)."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company: CompanyBrief
    description: Optional[str] = None  # Full description, can be truncated by frontend
    salary_range: Optional[SalaryRange] = None
    requirements: Optional[List[str]] = None
    benefits: Optional[List[str]] = None
    job_url: Optional[str] = None
    application_url: Optional[str] = None
    posted_date: Optional[datetime] = None
    status: str
    is_active: bool
    source_type: str
    created_at: datetime


class JobDetailResponse(JobBase):
    """Schema for detailed job response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company: CompanyBrief
    description: Optional[str] = None
    salary_range: Optional[SalaryRange] = None
    requirements: Optional[List[str]] = None
    benefits: Optional[List[str]] = None
    job_url: Optional[str] = None
    application_url: Optional[str] = None
    posted_date: Optional[datetime] = None
    scraped_at: Optional[datetime] = None
    first_seen_at: Optional[datetime] = None
    last_seen_at: Optional[datetime] = None
    status: str
    is_active: bool
    source_type: str
    duplicate_metadata: Optional[dict] = None
    created_at: datetime
    updated_at: datetime


class JobListResponse(BaseModel):
    """Schema for paginated job list response."""
    total: int
    page: int
    page_size: int
    total_pages: int
    jobs: List[JobListItem]
    filters_applied: dict = Field(default_factory=dict)


class PersonalizedJobItem(BaseModel):
    """Schema for a personalized job with match information."""
    job: JobListItem
    matched_alerts: List[str] = Field(description="Names of alerts that matched this job")
    match_count: int = Field(description="Number of alerts that matched this job")


class PersonalizedJobsResponse(BaseModel):
    """Schema for personalized jobs response."""
    total: int = Field(description="Total number of matching jobs")
    page: int = Field(description="Current page number")
    page_size: int = Field(description="Number of items per page")
    total_pages: int = Field(description="Total number of pages")
    jobs: List[PersonalizedJobItem] = Field(description="List of personalized jobs with match info")
    alert_count: int = Field(description="Number of active alerts used for matching")


# ============ Personalized Feed Schemas ============

class FeedJobItem(JobBase):
    """Schema for a job in the personalized feed."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company: CompanyBrief
    description: Optional[str] = None
    salary_range: Optional[SalaryRange] = None
    requirements: Optional[List[str]] = None
    benefits: Optional[List[str]] = None
    job_url: Optional[str] = None
    application_url: Optional[str] = None
    posted_date: Optional[datetime] = None
    status: str
    is_active: bool
    source_type: str
    created_at: datetime
    # Personalization fields
    similarity_score: float = Field(description="Semantic similarity score (0.0 - 1.0)")
    is_starred: bool = Field(default=False, description="Whether user has starred this job")
    is_archived: bool = Field(default=False, description="Whether user has archived this job")


class FeedResponse(BaseModel):
    """Schema for personalized feed response."""
    total: int = Field(description="Total number of matching jobs")
    page: int = Field(description="Current page number")
    page_size: int = Field(description="Number of items per page")
    total_pages: int = Field(description="Total number of pages")
    jobs: List[FeedJobItem] = Field(description="List of personalized jobs")
    user_preferences: dict = Field(description="User's job preferences used for matching")


class StarredJobsResponse(BaseModel):
    """Schema for starred jobs list response."""
    total: int
    page: int
    page_size: int
    total_pages: int
    jobs: List[FeedJobItem]


class ArchivedJobsResponse(BaseModel):
    """Schema for archived jobs list response."""
    total: int
    page: int
    page_size: int
    total_pages: int
    jobs: List[FeedJobItem]


class JobInteractionResponse(BaseModel):
    """Schema for star/archive action response."""
    job_id: UUID
    is_starred: bool
    is_archived: bool
    message: str


class JobPreferencesUpdate(BaseModel):
    """Schema for updating user's job preferences."""
    job_title: Optional[str] = Field(None, description="User's target job title", max_length=200)
    job_keywords: Optional[List[str]] = Field(None, description="Keywords to match against job titles", max_items=20)


class JobPreferencesResponse(BaseModel):
    """Schema for job preferences response."""
    job_title: Optional[str] = None
    job_keywords: List[str] = Field(default_factory=list)
    updated_at: datetime

