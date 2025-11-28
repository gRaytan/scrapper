"""Workday API job parser."""
from typing import Dict, Any, Optional
from loguru import logger

from .base_parser import BaseJobParser


class WorkdayParser(BaseJobParser):
    """Parser for Workday API job format (used by Salesforce and others)."""
    
    def __init__(self, base_url: str = ""):
        """
        Initialize Workday parser.
        
        Args:
            base_url: Base URL for constructing job URLs (e.g., "https://salesforce.wd12.myworkdayjobs.com")
        """
        self.base_url = base_url
    
    def parse(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse job from Workday API format.
        
        Workday API returns jobs in this format:
        {
            "title": "Job Title",
            "externalPath": "/job/Location/Job-Title_JR123456",
            "locationsText": "Location Name",
            "postedOn": "Posted Today" or "Posted 2 Days Ago",
            "bulletFields": ["JR123456"]
        }
        
        Args:
            job_data: Job data from Workday API
            
        Returns:
            Standardized job dictionary
        """
        try:
            # Extract external ID from bulletFields or externalPath
            external_id = ""
            bullet_fields = job_data.get("bulletFields", [])
            if bullet_fields and len(bullet_fields) > 0:
                external_id = bullet_fields[0]
            else:
                # Extract from externalPath (e.g., "/job/Location/Job-Title_JR123456")
                external_path = job_data.get("externalPath", "")
                if "_" in external_path:
                    external_id = external_path.split("_")[-1]
            
            # Build job URL
            external_path = job_data.get("externalPath", "")
            job_url = f"{self.base_url}{external_path}" if self.base_url and external_path else ""
            
            # Extract location
            location = job_data.get("locationsText", "")
            
            # Parse posted date (Workday uses relative dates like "Posted Today", "Posted 2 Days Ago")
            posted_date = None
            posted_on = job_data.get("postedOn", "")
            # We'll keep it as None since Workday doesn't provide exact dates in the list API
            # Could be enhanced to parse relative dates if needed
            
            # Determine if remote
            is_remote = "remote" in location.lower() if location else False
            
            return {
                "external_id": external_id,
                "title": job_data.get("title"),
                "description": "",  # Not in list API response
                "location": location,
                "job_url": job_url,
                "department": None,  # Not in basic list response
                "employment_type": None,  # Not in basic list response
                "posted_date": posted_date,
                "is_remote": is_remote,
            }
        except Exception as e:
            logger.error(f"Error parsing Workday job: {e}")
            logger.error(f"Job data: {job_data}")
            return {}


class SalesforceParser(WorkdayParser):
    """Backward-compatible alias for Salesforce Workday parser."""
    
    def __init__(self):
        super().__init__(base_url="https://salesforce.wd12.myworkdayjobs.com")

