"""Job position data model."""
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from sqlalchemy import Boolean, String, Text, JSON, DateTime, Float, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID as PGUUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin


class JobPosition(Base, UUIDMixin, TimestampMixin):
    """Job position model for storing job posting information."""
    
    __tablename__ = "job_positions"
    
    # Foreign key
    company_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # External ID from source (for deduplication)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # Basic information
    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    location: Mapped[Optional[str]] = mapped_column(String(200), index=True)
    
    # Job details
    remote_type: Mapped[Optional[str]] = mapped_column(String(50))  # remote, hybrid, onsite
    employment_type: Mapped[Optional[str]] = mapped_column(String(50))  # full-time, part-time, contract
    department: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    seniority_level: Mapped[Optional[str]] = mapped_column(String(50))  # entry, mid, senior, lead, executive
    
    # Salary information (stored as JSON for flexibility)
    salary_range: Mapped[Optional[dict]] = mapped_column(JSON)
    
    # Additional details
    requirements: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text))
    benefits: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text))
    
    # URLs
    application_url: Mapped[Optional[str]] = mapped_column(String(1000))
    job_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    
    # Dates
    posted_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    scraped_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )

    # Lifecycle tracking
    status: Mapped[str] = mapped_column(String(50), default='active', nullable=False, index=True)  # active, expired, filled
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expired_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Status (deprecated - use status field instead)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    
    # Raw data (for re-parsing if needed)
    raw_html: Mapped[Optional[str]] = mapped_column(Text)
    
    # Additional metadata
    extra_metadata: Mapped[Optional[dict]] = mapped_column(JSON, default=dict, name="metadata")
    
    # Relationships
    company = relationship("Company", back_populates="job_positions")
    
    # Indexes for common queries
    __table_args__ = (
        Index("ix_job_positions_company_active", "company_id", "is_active"),
        Index("ix_job_positions_location_active", "location", "is_active"),
        Index("ix_job_positions_department_active", "department", "is_active"),
        Index("ix_job_positions_external_id_company", "external_id", "company_id", unique=True),
    )
    
    def __repr__(self) -> str:
        return f"<JobPosition(id={self.id}, title='{self.title}', company_id={self.company_id})>"
    
    @property
    def salary_min(self) -> Optional[float]:
        """Get minimum salary."""
        if self.salary_range:
            return self.salary_range.get("min")
        return None
    
    @property
    def salary_max(self) -> Optional[float]:
        """Get maximum salary."""
        if self.salary_range:
            return self.salary_range.get("max")
        return None
    
    @property
    def salary_currency(self) -> Optional[str]:
        """Get salary currency."""
        if self.salary_range:
            return self.salary_range.get("currency", "USD")
        return None

