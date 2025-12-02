"""Parser for Ashby ATS GraphQL API."""
from typing import Dict, Any, Optional
from .base_parser import BaseJobParser
from src.utils.logger import logger


class AshbyParser(BaseJobParser):
    """Parser for Ashby ATS GraphQL API."""
    
    def __init__(self, company_name: str):
        """
        Initialize Ashby parser.
        
        Args:
            company_name: Company identifier for Ashby (e.g., 'lemonade')
        """
        self.company_name = company_name
        self.url_template = f"https://jobs.ashbyhq.com/{company_name}/{{id}}"
    
    def parse(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse job from Ashby GraphQL format.
        
        Args:
            job_data: Raw job data from Ashby GraphQL API
            
        Returns:
            Standardized job dictionary
        """
        try:
            # Extract basic fields
            external_id = job_data.get("id", "")
            title = job_data.get("title", "").strip()
            location = job_data.get("locationName", "")
            employment_type = job_data.get("employmentType", "")
            
            # Map employment type
            employment_type_map = {
                "FullTime": "Full-time",
                "PartTime": "Part-time",
                "Contract": "Contract",
                "Intern": "Internship",
                "Temporary": "Temporary"
            }
            employment_type = employment_type_map.get(employment_type, employment_type)
            
            # Determine if remote
            is_remote = location and location.lower() in ["remote", "anywhere"]
            remote_type = "remote" if is_remote else "onsite"
            
            # Build job URL
            job_url = self.url_template.format(id=external_id) if external_id else ""
            
            return {
                "external_id": external_id,
                "title": title,
                "description": "",  # Ashby brief API doesn't include description
                "location": location,
                "department": None,  # Not available in brief API
                "employment_type": employment_type,
                "remote_type": remote_type,
                "job_url": job_url,
                "application_url": job_url,
                "posted_date": None,  # Not available in brief API
                "is_remote": is_remote
            }
            
        except Exception as e:
            logger.error(f"Error parsing Ashby job: {e}")
            logger.error(f"Job data: {job_data}")
            return {}

