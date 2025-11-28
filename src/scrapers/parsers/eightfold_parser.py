"""Eightfold AI API job parser."""
from datetime import datetime
from typing import Dict, Any
from loguru import logger

from .base_parser import BaseJobParser


class EightfoldParser(BaseJobParser):
    """Parser for Eightfold AI API job format (used by Nvidia)."""
    
    def parse(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse job from Eightfold AI API format.
        
        Args:
            job_data: Job data from Eightfold AI API
            
        Returns:
            Standardized job dictionary
        """
        try:
            # Extract location (Eightfold returns list of locations)
            locations = job_data.get("locations", [])
            location = ", ".join(locations) if locations else ""
            
            # Extract job URL
            position_url = job_data.get("positionUrl", "")
            job_url = f"https://nvidia.eightfold.ai{position_url}" if position_url else ""
            
            # Parse posted date (Unix timestamp in milliseconds)
            posted_date = None
            posted_ts = job_data.get("postedTs")
            if posted_ts:
                try:
                    # Convert from milliseconds to seconds
                    posted_date = datetime.fromtimestamp(posted_ts / 1000)
                except:
                    pass
            
            # Determine if remote
            work_location_option = job_data.get("workLocationOption", "")
            is_remote = work_location_option.lower() == "remote"
            
            return {
                "external_id": job_data.get("displayJobId") or str(job_data.get("id", "")),
                "title": job_data.get("name"),
                "description": "",  # Not in search API response
                "location": location,
                "job_url": job_url,
                "department": job_data.get("department"),
                "employment_type": None,  # Not in Eightfold API
                "posted_date": posted_date,
                "is_remote": is_remote,
            }
        except Exception as e:
            logger.error(f"Error parsing Eightfold job: {e}")
            return {}

