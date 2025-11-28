"""Microsoft jobs parser - uses Microsoft's API."""
import json
from typing import List, Dict, Any
from .base_parser import BaseJobParser


class MicrosoftParser(BaseJobParser):
    """Parser for Microsoft jobs API."""
    
    def parse(self, response_text: str) -> List[Dict[str, Any]]:
        """
        Extract jobs from Microsoft's API response.
        
        Args:
            response_text: JSON response from Microsoft API
            
        Returns:
            List of job dictionaries
        """
        jobs = []
        
        try:
            data = json.loads(response_text)
            
            # Navigate to positions array
            if 'data' in data and 'positions' in data['data']:
                positions = data['data']['positions']
                
                for position in positions:
                    # Extract locations (join multiple locations)
                    locations = position.get('locations', [])
                    location = ', '.join(locations) if locations else ''
                    
                    # Build job URL
                    position_url = position.get('positionUrl', '')
                    url = f"https://apply.careers.microsoft.com{position_url}" if position_url else ''
                    
                    job = {
                        'title': position.get('name', ''),
                        'location': location,
                        'url': url,
                        'job_id': str(position.get('id', '')),
                        'display_job_id': position.get('displayJobId', ''),
                        'department': position.get('department', ''),
                        'work_location_option': position.get('workLocationOption', ''),
                        'posted_timestamp': position.get('postedTs', 0),
                    }
                    
                    jobs.append(job)
        
        except Exception as e:
            print(f"Error parsing Microsoft jobs: {e}")
        
        return jobs

