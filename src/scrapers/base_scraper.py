"""Base scraper abstract class."""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from datetime import datetime

from loguru import logger


class BaseScraper(ABC):
    """Abstract base class for all scrapers."""
    
    def __init__(
        self,
        company_config: Dict[str, Any],
        scraping_config: Dict[str, Any],
        **kwargs
    ):
        """
        Initialize the scraper.
        
        Args:
            company_config: Company information
            scraping_config: Scraping configuration
            **kwargs: Additional arguments
        """
        self.company_config = company_config
        self.scraping_config = scraping_config
        self.company_name = company_config.get("name", "Unknown")
        self.careers_url = company_config.get("careers_url")
        self.selectors = scraping_config.get("selectors", {})
        self.pagination_type = scraping_config.get("pagination_type", "none")
        self.wait_time = scraping_config.get("wait_time", 2)
        
        # Location filtering configuration
        self.location_filter = company_config.get("location_filter", {})
        self.location_filter_enabled = self.location_filter.get("enabled", False)
        self.filter_countries = self.location_filter.get("countries", [])
        self.filter_keywords = self.location_filter.get("match_keywords", [])
        
        # Statistics
        self.stats = {
            "pages_scraped": 0,
            "jobs_found": 0,
            "jobs_filtered": 0,
            "requests_made": 0,
            "errors": 0,
            "start_time": None,
            "end_time": None
        }
        
        logger.info(f"Initialized {self.__class__.__name__} for {self.company_name}")
        if self.location_filter_enabled:
            logger.info(f"Location filter enabled for countries: {self.filter_countries}")
    
    @abstractmethod
    async def scrape(self) -> List[Dict[str, Any]]:
        """
        Main scraping method to be implemented by subclasses.
        
        Returns:
            List of job dictionaries
        """
        pass
    
    @abstractmethod
    async def setup(self):
        """Set up the scraper (e.g., initialize browser)."""
        pass
    
    @abstractmethod
    async def teardown(self):
        """Clean up resources (e.g., close browser)."""
        pass
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.setup()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.teardown()
    
    def start_timer(self):
        """Start the scraping timer."""
        self.stats["start_time"] = datetime.utcnow()
    
    def stop_timer(self):
        """Stop the scraping timer."""
        self.stats["end_time"] = datetime.utcnow()
    
    def get_duration(self) -> Optional[float]:
        """Get scraping duration in seconds."""
        if self.stats["start_time"] and self.stats["end_time"]:
            return (self.stats["end_time"] - self.stats["start_time"]).total_seconds()
        return None
    
    def increment_stat(self, stat_name: str, value: int = 1):
        """Increment a statistic."""
        if stat_name in self.stats:
            self.stats[stat_name] += value
    
    def get_stats(self) -> Dict[str, Any]:
        """Get scraping statistics."""
        stats = self.stats.copy()
        stats["duration_seconds"] = self.get_duration()
        return stats
    
    def log_progress(self, message: str, **kwargs):
        """Log progress with context."""
        logger.info(
            f"[{self.company_name}] {message}",
            extra={"company": self.company_name, **kwargs}
        )
    
    def log_error(self, message: str, error: Optional[Exception] = None, **kwargs):
        """Log error with context."""
        self.increment_stat("errors")
        logger.error(
            f"[{self.company_name}] {message}",
            extra={"company": self.company_name, "error": str(error) if error else None, **kwargs}
        )
    
    def validate_job_data(self, job: Dict[str, Any]) -> bool:
        """
        Validate job data.
        
        Args:
            job: Job dictionary
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = ["title", "job_url"]
        
        for field in required_fields:
            if not job.get(field):
                self.log_error(f"Missing required field: {field}", job_data=job)
                return False
        
        # Validate title length
        title = job.get("title", "")
        if len(title) < 3 or len(title) > 200:
            self.log_error(f"Invalid title length: {len(title)}", title=title)
            return False
        
        return True
    
    def normalize_job_data(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize job data.
        
        Args:
            job: Raw job dictionary
            
        Returns:
            Normalized job dictionary
        """
        normalized = {
            "external_id": job.get("external_id"),
            "title": job.get("title", "").strip(),
            "description": job.get("description", "").strip() if job.get("description") else None,
            "location": job.get("location", "").strip() if job.get("location") else None,
            "job_url": job.get("job_url", "").strip(),
            "department": job.get("department", "").strip() if job.get("department") else None,
            "employment_type": job.get("employment_type"),
            "posted_date": job.get("posted_date"),
            "is_remote": job.get("is_remote", False)
        }
        
        return normalized


    def matches_location_filter(self, job: Dict[str, Any]) -> bool:
        """
        Check if job matches location filter criteria.
        
        Args:
            job: Job dictionary with location field
            
        Returns:
            True if job matches filter (or filter disabled), False otherwise
        """
        # If filter is disabled, all jobs pass
        if not self.location_filter_enabled:
            return True
        
        location = job.get("location", "")
        if not location:
            # If no location specified, filter it out when filter is enabled
            return False
        
        location_lower = location.lower()
        
        # Check if any of the filter keywords match the location
        for keyword in self.filter_keywords:
            if keyword.lower() in location_lower:
                return True
        
        return False
