"""Pydantic schemas for Alert API."""
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class AlertBase(BaseModel):
    """Base alert schema with common fields."""
    name: str = Field(..., min_length=1, max_length=255)
    is_active: bool = True
    company_ids: List[UUID] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    excluded_keywords: List[str] = Field(default_factory=list)
    locations: List[str] = Field(default_factory=list)
    departments: List[str] = Field(default_factory=list)
    employment_types: List[str] = Field(default_factory=list)
    remote_types: List[str] = Field(default_factory=list)
    seniority_levels: List[str] = Field(default_factory=list)


class AlertCreate(AlertBase):
    """Schema for creating a new alert."""
    notification_method: str = Field(default="email", pattern="^(email|webhook|push)$")
    notification_config: dict = Field(default_factory=lambda: {"frequency": "immediate"})


class AlertUpdate(BaseModel):
    """Schema for updating an alert."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    is_active: Optional[bool] = None
    company_ids: Optional[List[UUID]] = None
    keywords: Optional[List[str]] = None
    excluded_keywords: Optional[List[str]] = None
    locations: Optional[List[str]] = None
    departments: Optional[List[str]] = None
    employment_types: Optional[List[str]] = None
    remote_types: Optional[List[str]] = None
    seniority_levels: Optional[List[str]] = None
    notification_method: Optional[str] = Field(None, pattern="^(email|webhook|push)$")
    notification_config: Optional[dict] = None


class AlertStats(BaseModel):
    """Alert statistics."""
    matching_jobs_count: int = 0
    last_triggered_at: Optional[datetime] = None
    trigger_count: int = 0
    notifications_sent: int = 0


class CompanyBrief(BaseModel):
    """Brief company info for alert response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    name: str


class AlertResponse(AlertBase):
    """Schema for alert response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    user_id: UUID
    notification_method: str
    notification_config: dict
    last_triggered_at: Optional[datetime] = None
    trigger_count: int
    created_at: datetime
    updated_at: datetime


class AlertDetailResponse(AlertResponse):
    """Schema for detailed alert response with stats."""
    companies: List[CompanyBrief] = Field(default_factory=list)
    stats: Optional[AlertStats] = None


class AlertListResponse(BaseModel):
    """Schema for alert list response."""
    total: int
    alerts: List[AlertResponse]


class JobMatchPreview(BaseModel):
    """Schema for job match preview in alert test."""
    id: UUID
    title: str
    company: dict
    location: Optional[str] = None
    match_score: float
    matched_criteria: List[str]


class AlertTestResponse(BaseModel):
    """Schema for alert test response."""
    matching_jobs_count: int
    sample_jobs: List[JobMatchPreview]
    total_active_jobs: int

