"""SmartRecruiters API job parser."""
from typing import Dict, Any
from dateutil import parser as date_parser
from loguru import logger

from .base_parser import BaseJobParser


class SmartRecruitersParser(BaseJobParser):
    """Parser for SmartRecruiters API job format (used by Wix)."""
    
    def parse(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse job from SmartRecruiters API format.
        
        Args:
            job_data: Job data from SmartRecruiters API
            
        Returns:
            Standardized job dictionary
        """
        try:
            # Extract location
            location_data = job_data.get("location", {})
            location = location_data.get("fullLocation", "")
            
            # Extract job URL
            job_id = job_data.get("id", "")
            job_url = f"https://jobs.smartrecruiters.com/Wix2/{job_id}" if job_id else ""
            
            # Extract department
            department_data = job_data.get("department", {})
            department = department_data.get("label") if department_data else None
            
            # Extract employment type
            employment_data = job_data.get("typeOfEmployment", {})
            employment_type = employment_data.get("label") if employment_data else None
            
            # Parse posted date (ISO format)
            posted_date = None
            released_date = job_data.get("releasedDate")
            if released_date:
                try:
                    posted_date = date_parser.parse(released_date)
                except:
                    pass
            
            # Determine if remote
            is_remote = location_data.get("remote", False)
            
            return {
                "external_id": job_id,
                "title": job_data.get("name"),
                "description": "",  # Not in list API response
                "location": location,
                "job_url": job_url,
                "department": department,
                "employment_type": employment_type,
                "posted_date": posted_date,
                "is_remote": is_remote,
            }
        except Exception as e:
            logger.error(f"Error parsing SmartRecruiters job: {e}")
            return {}

