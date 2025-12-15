"""Generic parser for jobs embedded as JavaScript variables in HTML pages.

Many career sites embed job data directly in the HTML as JavaScript variables
(e.g., `var jobs = [...]` or `window.__JOBS__ = [...]`). This parser provides
a configurable way to extract and parse such data.

Supported sites:
- Taboola: `var jobs = [...]` with Greenhouse-backed data
- Can be extended for other sites with similar patterns
"""
import re
import json
from typing import Dict, Any, List, Optional
from loguru import logger

from .base_parser import BaseJobParser


# HTML entity replacements for cleaning JSON
HTML_ENTITIES = {
    '&#8211;': '-',      # en-dash
    '&#8212;': '—',      # em-dash
    '&#8217;': "'",      # right single quote
    '&#8216;': "'",      # left single quote
    '&#8220;': '"',      # left double quote
    '&#8221;': '"',      # right double quote
    '&amp;': '&',
    '&lt;': '<',
    '&gt;': '>',
    '&nbsp;': ' ',
    '&quot;': '"',
}


class EmbeddedJSParser(BaseJobParser):
    """Generic parser for jobs embedded as JavaScript in HTML pages.
    
    Configuration via scraping_config:
        embedded_js_config:
            variable_pattern: "var jobs = (\\[.*?\\]);"  # Regex to extract JSON
            field_mapping:
                external_id: id | greenhouse_job_id
                title: title
                location: office_textual | office_text | country
                job_url: link
                department: teams_text
    """

    # Pre-configured patterns for known sites
    KNOWN_PATTERNS = {
        'taboola': {
            'variable_pattern': r'var jobs = (\[.*?\]);',
            'field_mapping': {
                'external_id': ['greenhouse_job_id', 'id'],
                'title': 'title',
                'location': ['office_textual', 'office_text', 'country'],
                'job_url': 'link',
                'department': 'teams_text',
            }
        },
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None, site_name: Optional[str] = None):
        """Initialize the parser.
        
        Args:
            config: Custom configuration dict with variable_pattern and field_mapping
            site_name: Name of a known site (e.g., 'taboola') to use pre-configured settings
        """
        if site_name and site_name in self.KNOWN_PATTERNS:
            self.config = self.KNOWN_PATTERNS[site_name]
        elif config:
            self.config = config
        else:
            # Default to Taboola pattern
            self.config = self.KNOWN_PATTERNS['taboola']
        
        self.field_mapping = self.config.get('field_mapping', {})

    @staticmethod
    def clean_json_string(json_str: str) -> str:
        """Clean HTML entities from JSON string."""
        for entity, replacement in HTML_ENTITIES.items():
            json_str = json_str.replace(entity, replacement)
        return json_str

    def extract_jobs_from_html(self, html_content: str) -> List[Dict[str, Any]]:
        """Extract jobs array from HTML page containing embedded JavaScript.

        Args:
            html_content: Raw HTML content

        Returns:
            List of raw job dictionaries extracted from the page
        """
        try:
            pattern = self.config.get('variable_pattern', r'var jobs = (\[.*?\]);')
            match = re.search(pattern, html_content, re.DOTALL)
            
            if not match:
                logger.warning(f"Could not find pattern '{pattern}' in page")
                return []

            jobs_json = self.clean_json_string(match.group(1))
            jobs = json.loads(jobs_json)
            logger.info(f"Extracted {len(jobs)} jobs from embedded JS")
            return jobs

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse embedded JS JSON: {e}")
            return []
        except Exception as e:
            logger.error(f"Error extracting embedded JS jobs: {e}")
            return []

    def _get_field_value(self, job_data: Dict[str, Any], field_spec: Any) -> Any:
        """Get field value from job data using field specification.
        
        Args:
            job_data: Raw job data
            field_spec: Field name (str) or list of fallback field names
            
        Returns:
            Field value or empty string if not found
        """
        if isinstance(field_spec, list):
            for field in field_spec:
                value = job_data.get(field)
                if value:
                    return value
            return ""
        return job_data.get(field_spec, "")

    def parse(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse a single job using the configured field mapping.

        Args:
            job_data: Job data from the embedded JavaScript array

        Returns:
            Standardized job dictionary
        """
        try:
            location = self._get_field_value(job_data, self.field_mapping.get('location', 'location'))
            is_remote = 'remote' in location.lower() if location else False

            external_id = self._get_field_value(job_data, self.field_mapping.get('external_id', 'id'))
            
            return {
                "external_id": str(external_id) if external_id else "",
                "title": self._get_field_value(job_data, self.field_mapping.get('title', 'title')),
                "description": "",
                "location": location,
                "job_url": self._get_field_value(job_data, self.field_mapping.get('job_url', 'url')),
                "department": self._get_field_value(job_data, self.field_mapping.get('department')) or None,
                "employment_type": self._get_field_value(job_data, self.field_mapping.get('employment_type')) or None,
                "posted_date": None,
                "is_remote": is_remote,
            }
        except Exception as e:
            logger.error(f"Error parsing embedded JS job: {e}")
            return {}

