"""Comeet API job parser (used by Monday.com)."""
from typing import Dict, Any
from datetime import datetime
import re
from loguru import logger

from .base_parser import BaseJobParser


class ComeetParser(BaseJobParser):
    """Parser for Comeet API job format."""
    
    def parse(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse job from Comeet API format."""
        try:
            location_data = job_data.get("location", {})
            location_parts = []
            if location_data.get("city"):
                location_parts.append(location_data["city"])
            if location_data.get("country"):
                location_parts.append(location_data["country"])
            
            location = ", ".join(location_parts) if location_parts else location_data.get("name", "")
            
            # Extract description from details
            description = ""
            details = job_data.get("details", [])
            for detail in details:
                if detail.get("name") == "Description":
                    description = detail.get("value", "")
                    # Remove HTML tags
                    description = re.sub(r'<[^>]+>', '', description)
                    break
            
            # Parse posted date
            posted_date = None
            time_updated = job_data.get("time_updated")
            if time_updated:
                try:
                    posted_date = datetime.fromisoformat(time_updated.replace('Z', '+00:00'))
                except:
                    pass
            
            return {
                "external_id": job_data.get("uid"),
                "title": job_data.get("name"),
                "description": description[:5000] if description else "",  # Limit length
                "location": location,
                "job_url": job_data.get("url_active_page"),
                "department": job_data.get("department"),
                "employment_type": job_data.get("employment_type"),
                "posted_date": posted_date,
                "is_remote": location_data.get("is_remote", False),
            }
        except Exception as e:
            logger.error(f"Error parsing Comeet job: {e}")
            return {}

