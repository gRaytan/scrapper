"""Base parser interface for job data parsing."""
from typing import Dict, Any
from abc import ABC, abstractmethod


class BaseJobParser(ABC):
    """Abstract base class for job parsers."""
    
    @abstractmethod
    def parse(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse job data into standardized format.
        
        Args:
            job_data: Raw job data from API/scraper
            
        Returns:
            Standardized job dictionary with keys:
                - external_id: str
                - title: str
                - description: str
                - location: str
                - job_url: str
                - department: str (optional)
                - employment_type: str (optional)
                - posted_date: datetime (optional)
                - is_remote: bool (optional)
        """
        pass

