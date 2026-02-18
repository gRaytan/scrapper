"""Pydantic schemas for SavedFilter API."""
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class SavedFilterFilters(BaseModel):
    """Filter configuration schema."""
    companies: Optional[List[str]] = Field(default_factory=list)
    locations: Optional[List[str]] = Field(default_factory=list)
    work_types: Optional[List[str]] = Field(default_factory=list)
    departments: Optional[List[str]] = Field(default_factory=list)
    seniority_levels: Optional[List[str]] = Field(default_factory=list)
    search_query: Optional[str] = None


class SavedFilterCreate(BaseModel):
    """Schema for creating a saved filter."""
    name: str = Field(..., min_length=1, max_length=100)
    filters: SavedFilterFilters


class SavedFilterUpdate(BaseModel):
    """Schema for updating a saved filter."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    filters: Optional[SavedFilterFilters] = None


class SavedFilterResponse(BaseModel):
    """Schema for saved filter response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    name: str
    filters: dict
    created_at: datetime
    updated_at: datetime


class SavedFilterListResponse(BaseModel):
    """Schema for list of saved filters."""
    filters: List[SavedFilterResponse]
    total: int

