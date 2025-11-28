"""Apple jobs parser - extracts from embedded JSON in HTML."""
import json
import re
from typing import List, Dict, Any
from .base_parser import BaseJobParser


class AppleParser(BaseJobParser):
    """Parser for Apple jobs (embedded JSON in HTML)."""
    
    def parse(self, html_content: str) -> List[Dict[str, Any]]:
        """
        Extract jobs from Apple's embedded JSON data.
        
        Args:
            html_content: HTML content containing window.__staticRouterHydrationData
            
        Returns:
            List of job dictionaries
        """
        jobs = []
        
        try:
            # Extract JSON from window.__staticRouterHydrationData
            match = re.search(
                r'window\.__staticRouterHydrationData\s*=\s*JSON\.parse\("(.*)"\);',
                html_content,
                re.DOTALL
            )
            
            if not match:
                return jobs
            
            # Unescape the JSON string
            escaped_json = match.group(1)
            unescaped = escaped_json.encode().decode('unicode_escape')
            
            data = json.loads(unescaped)
            
            # Navigate to searchResults
            if 'loaderData' in data and 'search' in data['loaderData']:
                search_data = data['loaderData']['search']
                
                if 'searchResults' in search_data:
                    results = search_data['searchResults']
                    
                    for job_data in results:
                        # Extract location
                        locations = job_data.get('locations', [])
                        location = locations[0].get('name', '') if locations else ''
                        
                        # Build job URL
                        job_id = job_data.get('positionId', job_data.get('id', ''))
                        url = f"https://jobs.apple.com/en-il/details/{job_id}" if job_id else ''
                        
                        job = {
                            'title': job_data.get('postingTitle', ''),
                            'location': location,
                            'url': url,
                            'description': job_data.get('jobSummary', ''),
                            'team': job_data.get('team', {}).get('teamName', ''),
                            'job_id': job_id,
                        }
                        
                        jobs.append(job)
        
        except Exception as e:
            print(f"Error parsing Apple jobs: {e}")
        
        return jobs
