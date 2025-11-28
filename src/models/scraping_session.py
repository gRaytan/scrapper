"""Scraping session data model."""
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from sqlalchemy import String, DateTime, Integer, JSON, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin


class ScrapingSession(Base, UUIDMixin, TimestampMixin):
    """Scraping session model for tracking scraping runs."""
    
    __tablename__ = "scraping_sessions"
    
    # Foreign key
    company_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Status
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
        index=True
    )  # pending, running, completed, failed
    
    # Timing
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Statistics
    jobs_found: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    jobs_new: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    jobs_updated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    jobs_removed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Errors
    errors: Mapped[Optional[List[dict]]] = mapped_column(JSON, default=list)
    
    # Performance metrics
    performance_metrics: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    
    # Configuration snapshot (for debugging)
    scraper_config_snapshot: Mapped[Optional[dict]] = mapped_column(JSON)
    
    # Relationships
    company = relationship("Company", back_populates="scraping_sessions")
    
    # Indexes
    __table_args__ = (
        Index("ix_scraping_sessions_company_status", "company_id", "status"),
        Index("ix_scraping_sessions_started_at", "started_at"),
    )
    
    def __repr__(self) -> str:
        return f"<ScrapingSession(id={self.id}, company_id={self.company_id}, status='{self.status}')>"
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate session duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    @property
    def is_running(self) -> bool:
        """Check if session is currently running."""
        return self.status == "running"
    
    @property
    def is_completed(self) -> bool:
        """Check if session completed successfully."""
        return self.status == "completed"
    
    @property
    def is_failed(self) -> bool:
        """Check if session failed."""
        return self.status == "failed"
    
    def add_error(self, error_type: str, error_message: str, **kwargs):
        """Add an error to the session."""
        if self.errors is None:
            self.errors = []
        
        error_entry = {
            "type": error_type,
            "message": error_message,
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs
        }
        self.errors.append(error_entry)
    
    def update_metrics(self, **metrics):
        """Update performance metrics."""
        if self.performance_metrics is None:
            self.performance_metrics = {}
        
        self.performance_metrics.update(metrics)

