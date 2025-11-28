"""Google jobs parser - extracts from AF_initDataCallback embedded data."""
import re
import json
from typing import List, Dict, Any
from .base_parser import BaseJobParser


class GoogleParser(BaseJobParser):
    """Parser for Google jobs (embedded in AF_initDataCallback)."""
    
    def parse(self, html_content: str) -> List[Dict[str, Any]]:
        """
        Extract jobs from Google's AF_initDataCallback embedded data.
        
        Args:
            html_content: HTML content containing AF_initDataCallback
            
        Returns:
            List of job dictionaries
        """
        jobs = []
        
        try:
            # Extract JSON from AF_initDataCallback with key 'ds:1'
            af_pattern = r'AF_initDataCallback\({key:\s*\'ds:1\',.*?data:(.*?), sideChannel:'
            match = re.search(af_pattern, html_content, re.DOTALL)
            
            if not match:
                return jobs
            
            # Clean up the data string
            data_str = match.group(1).rstrip().rstrip('}').rstrip()
            
            # Parse the JSON
            data = json.loads(data_str)
            
            if not isinstance(data, list) or len(data) == 0:
                return jobs
            
            jobs_array = data[0]
            
            for job_data in jobs_array:
                if not isinstance(job_data, list) or len(job_data) < 10:
                    continue
                
                # Extract fields based on observed structure
                job_id = job_data[0] if len(job_data) > 0 else ''
                title = job_data[1] if len(job_data) > 1 else ''
                url = job_data[2] if len(job_data) > 2 else ''
                
                # Field 3: [None, description]
                description = ''
                if len(job_data) > 3 and isinstance(job_data[3], list) and len(job_data[3]) > 1:
                    description = job_data[3][1] if job_data[3][1] else ''
                
                # Field 7: Company name (usually "Google")
                company = job_data[7] if len(job_data) > 7 else 'Google'
                
                # Field 9: Locations array
                locations = []
                if len(job_data) > 9 and isinstance(job_data[9], list):
                    for loc in job_data[9]:
                        if isinstance(loc, list) and len(loc) > 0:
                            # loc[0] is the location string like "Tel Aviv, Israel"
                            locations.append(loc[0])
                
                location = ', '.join(locations) if locations else ''
                
                # Field 4: [None, qualifications]
                qualifications = ''
                if len(job_data) > 4 and isinstance(job_data[4], list) and len(job_data[4]) > 1:
                    qualifications = job_data[4][1] if job_data[4][1] else ''
                
                job = {
                    'title': title,
                    'location': location,
                    'url': url,
                    'job_id': job_id,
                    'company': company,
                    'description': self._clean_html(description),
                    'qualifications': self._clean_html(qualifications),
                }
                
                jobs.append(job)
        
        except Exception as e:
            print(f"Error parsing Google jobs: {e}")
            import traceback
            traceback.print_exc()
        
        return jobs
    
    def _clean_html(self, html_text: str) -> str:
        """Remove HTML tags from text."""
        if not html_text:
            return ''
        
        # Simple HTML tag removal
        import re
        clean = re.sub(r'<[^>]+>', '', html_text)
        clean = re.sub(r'\s+', ' ', clean)
        return clean.strip()

