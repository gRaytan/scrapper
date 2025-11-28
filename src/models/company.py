"""Company data model."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import Boolean, String, Text, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin


class Company(Base, UUIDMixin, TimestampMixin):
    """Company model for storing company information and scraping configuration."""
    
    __tablename__ = "companies"
    
    # Basic information
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    website: Mapped[str] = mapped_column(String(500), nullable=False)
    careers_url: Mapped[str] = mapped_column(String(500), nullable=False)
    industry: Mapped[Optional[str]] = mapped_column(String(100))
    size: Mapped[Optional[str]] = mapped_column(String(50))
    location: Mapped[Optional[str]] = mapped_column(String(200))
    
    # Scraping configuration (stored as JSON)
    scraping_config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    
    # Scheduling
    scraping_frequency: Mapped[Optional[str]] = mapped_column(String(100))  # Cron expression
    last_scraped_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Relationships
    job_positions = relationship("JobPosition", back_populates="company", cascade="all, delete-orphan")
    scraping_sessions = relationship("ScrapingSession", back_populates="company", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Company(id={self.id}, name='{self.name}')>"
    
    @property
    def scraper_type(self) -> str:
        """Get the scraper type from config."""
        return self.scraping_config.get("scraper_type", "playwright")
    
    @property
    def pagination_type(self) -> str:
        """Get the pagination type from config."""
        return self.scraping_config.get("pagination_type", "button")
    
    @property
    def requires_js(self) -> bool:
        """Check if JavaScript is required."""
        return self.scraping_config.get("requires_js", True)
    
    @property
    def selectors(self) -> dict:
        """Get CSS selectors from config."""
        return self.scraping_config.get("selectors", {})

