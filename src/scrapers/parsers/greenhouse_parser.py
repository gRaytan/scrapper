"""Greenhouse API job parser."""
from datetime import datetime
from typing import Dict, Any
from loguru import logger

from .base_parser import BaseJobParser


class GreenhouseParser(BaseJobParser):
    """Parser for Greenhouse API job format."""
    
    def parse(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse job from Greenhouse API format.
        
        Args:
            job_data: Job data from Greenhouse API
            
        Returns:
            Standardized job dictionary
        """
        try:
            # Extract location
            location = ""
            location_obj = job_data.get("location", {})
            if isinstance(location_obj, dict):
                location = location_obj.get("name", "")
            elif isinstance(location_obj, str):
                location = location_obj
            
            # Extract job URL
            job_url = job_data.get("absolute_url", "")
            
            # Parse posted/updated date
            posted_date = None
            updated_at = job_data.get("updated_at") or job_data.get("first_published")
            if updated_at:
                try:
                    # Greenhouse uses ISO format with timezone
                    posted_date = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                except:
                    pass
            
            # Extract departments from metadata if available
            department = None
            metadata = job_data.get("metadata")
            if metadata and isinstance(metadata, list):
                for item in metadata:
                    if item.get("name") == "Department":
                        department = item.get("value")
                        break
            
            return {
                "external_id": str(job_data.get("id")),
                "title": job_data.get("title"),
                "description": "",  # Greenhouse API doesn't include full description in list endpoint
                "location": location,
                "job_url": job_url,
                "department": department,
                "employment_type": None,  # Not in basic API response
                "posted_date": posted_date,
                "is_remote": "remote" in location.lower() if location else False,
            }
        except Exception as e:
            logger.error(f"Error parsing Greenhouse job: {e}")
            return {}

