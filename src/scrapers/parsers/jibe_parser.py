"""Parser for Jibe API format (used by Booking.com and others)."""
from datetime import datetime
from typing import Dict, Any
from dateutil import parser as date_parser

from .base_parser import BaseJobParser
from src.utils.logger import logger


class JibeParser(BaseJobParser):
    """Parser for Jibe API job format."""
    
    def parse(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse job from Jibe API format.
        
        Args:
            job_data: Raw job data from Jibe API
            
        Returns:
            Normalized job dictionary
        """
        try:
            # Jibe wraps job data in a 'data' key
            data = job_data.get("data", {})
            
            # Extract location
            full_location = data.get("full_location", "")
            city = data.get("city", "")
            country = data.get("country", "")
            
            # Build location string
            location_parts = []
            if city:
                location_parts.append(city)
            if country:
                location_parts.append(country)
            location = ", ".join(location_parts) if location_parts else full_location
            
            # Extract job URL
            slug = data.get("slug") or data.get("req_id")
            apply_url = data.get("apply_url", "")
            
            # Parse posted date
            posted_date = None
            posted_date_str = data.get("posted_date")
            if posted_date_str:
                try:
                    posted_date = date_parser.parse(posted_date_str)
                except:
                    pass
            
            # Determine if remote
            location_type = data.get("location_type", "")
            is_remote = location_type.lower() == "remote" or "remote" in location.lower()
            
            # Extract department/category
            department = None
            categories = data.get("categories")
            if categories and isinstance(categories, list) and len(categories) > 0:
                department = categories[0].get("name") if isinstance(categories[0], dict) else str(categories[0])
            
            if not department:
                department = data.get("department")
            
            return {
                "external_id": data.get("req_id") or slug,
                "title": data.get("title"),
                "description": data.get("description", "")[:5000],  # Limit length
                "location": location,
                "job_url": apply_url,
                "department": department,
                "employment_type": data.get("employment_type"),
                "posted_date": posted_date,
                "is_remote": is_remote,
            }
        except Exception as e:
            logger.error(f"Error parsing Jibe job: {e}")
            return {}

