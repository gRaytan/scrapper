"""LinkedIn job parser for hidden API endpoint."""
from typing import Dict, Any
from datetime import datetime
from loguru import logger
from bs4 import BeautifulSoup

from .base_parser import BaseJobParser


class LinkedInParser(BaseJobParser):
    """Parser for LinkedIn jobs from hidden API endpoint.
    
    LinkedIn's hidden API endpoint returns HTML with job listings.
    Each job is in an <li> element with structured data.
    """
    
    def parse(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse job from LinkedIn HTML format.
        
        The LinkedIn API returns HTML, so job_data is expected to be
        a BeautifulSoup element or a dict with 'html' key containing the HTML string.
        
        Args:
            job_data: Either a BeautifulSoup element or dict with HTML
            
        Returns:
            Standardized job dictionary
        """
        try:
            # Handle both BeautifulSoup element and dict input
            if isinstance(job_data, dict) and 'html' in job_data:
                soup = BeautifulSoup(job_data['html'], 'html.parser')
                job_element = soup
            elif hasattr(job_data, 'select_one'):
                # Already a BeautifulSoup element
                job_element = job_data
            else:
                logger.error(f"Unexpected job_data type: {type(job_data)}")
                return {}
            
            # Extract job URL
            link_element = job_element.select_one(
                'a[data-tracking-control-name="public_jobs_jserp-result_search-card"]'
            )
            job_url = link_element.get('href', '') if link_element else ''
            
            # Extract external ID from data attribute or URL
            # The data-entity-urn is on the child div, not the li
            external_id = ''
            div_element = job_element.find('div', {'data-entity-urn': True})
            if div_element:
                urn = div_element.get('data-entity-urn', '')
                if urn:
                    # Extract ID from URN format: "urn:li:jobPosting:3625991287"
                    external_id = urn.split(':')[-1]
            
            # Fallback: try to extract from URL
            if not external_id and job_url:
                import re
                match = re.search(r'-(\d+)(?:\?|$)', job_url)
                if match:
                    external_id = match.group(1)
            
            # Extract job title
            title_element = job_element.select_one('h3.base-search-card__title')
            title = title_element.text.strip() if title_element else ''
            
            # Extract company name
            company_element = job_element.select_one('h4.base-search-card__subtitle')
            company = company_element.text.strip() if company_element else ''
            
            # Extract location
            location_element = job_element.select_one('span.job-search-card__location')
            location = location_element.text.strip() if location_element else ''
            
            # Extract posted date
            posted_date = None
            date_element = job_element.select_one('time.job-search-card__listdate')
            if date_element:
                datetime_str = date_element.get('datetime', '')
                if datetime_str:
                    try:
                        posted_date = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
                    except Exception as e:
                        logger.debug(f"Failed to parse date '{datetime_str}': {e}")
            
            # Extract description snippet if available
            description_element = job_element.select_one('.base-search-card__snippet')
            description = description_element.text.strip() if description_element else ''
            
            # Determine if remote
            is_remote = False
            if location:
                location_lower = location.lower()
                is_remote = any(keyword in location_lower for keyword in ['remote', 'hybrid'])
            
            # Build standardized job dict
            job = {
                "external_id": external_id or job_url,  # Fallback to URL if no ID
                "title": title,
                "description": description,
                "location": location,
                "job_url": job_url,
                "department": None,  # LinkedIn API doesn't provide department in list view
                "employment_type": None,  # Not available in list view
                "posted_date": posted_date,
                "is_remote": is_remote,
                "company": company,  # Extra field for reference
            }
            
            return job
            
        except Exception as e:
            logger.error(f"Error parsing LinkedIn job: {e}")
            logger.exception(e)
            return {}

