"""Phenom People job parser."""
from datetime import datetime
from typing import Dict, Any
from loguru import logger
import re

from .base_parser import BaseJobParser


class PhenomParser(BaseJobParser):
    """Parser for Phenom People platform job format."""
    
    def parse(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse job from Phenom People format.
        
        Args:
            job_data: Job data from Phenom People (scraped from page)
            
        Returns:
            Standardized job dictionary
        """
        try:
            # Extract job ID from URL
            external_id = None
            url = job_data.get("url", "")
            if url:
                # Extract ID from URL pattern: /job/{location}/{title}/{company-id}/{job-id}
                id_match = re.search(r'/(\d+)(?:\?|$)', url)
                if id_match:
                    external_id = id_match.group(1)
            
            # Clean up title (remove extra whitespace and location text)
            title = job_data.get("title", "").strip()
            # Remove location text that might be appended to title
            title = re.sub(r'\s+Petach? Tikva,?\s*Israel\s*$', '', title, flags=re.I)
            title = re.sub(r'\s+Tel Aviv,?\s*Israel\s*$', '', title, flags=re.I)
            title = re.sub(r'\s+\n.*$', '', title)  # Remove anything after newline
            title = ' '.join(title.split())  # Normalize whitespace
            
            # Extract location
            location = job_data.get("location", "").strip()
            if not location or location == "Unknown":
                # Try to extract from URL
                url_location = re.search(r'/job/([^/]+)/', url)
                if url_location:
                    location = url_location.group(1).replace('-', ' ').title()
            
            return {
                "external_id": external_id or url,
                "title": title,
                "description": "",  # Not available in list view
                "location": location,
                "job_url": url,
                "department": None,
                "employment_type": None,
                "posted_date": None,  # Not available in list view
                "is_remote": "remote" in location.lower() if location else False,
            }
        except Exception as e:
            logger.error(f"Error parsing Phenom job: {e}")
            return {}

