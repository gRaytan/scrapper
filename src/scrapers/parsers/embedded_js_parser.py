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
        'apple': {
            'variable_pattern': r'window\.__staticRouterHydrationData\s*=\s*JSON\.parse\("(.*)"\);',
            'json_path': 'loaderData.search.searchResults',
            'needs_unescape': True,
            'field_mapping': {
                'external_id': 'positionId',
                'title': 'postingTitle',
                'location': 'locations[0].name',
                'job_url': None,  # Built dynamically
                'department': 'team.teamName',
                'description': 'jobSummary',
            },
            'url_template': 'https://jobs.apple.com/en-il/details/{positionId}',
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

    def _navigate_json_path(self, data: Any, path: str) -> Any:
        """Navigate a dot-separated path in JSON data, supporting array indexing.

        Args:
            data: JSON data (dict or list)
            path: Dot-separated path like 'loaderData.search.searchResults' or 'locations[0].name'

        Returns:
            Value at the path or None if not found
        """
        if not path or data is None:
            return data

        parts = path.split('.')
        current = data

        for part in parts:
            if current is None:
                return None

            # Handle array indexing like 'locations[0]'
            array_match = re.match(r'(\w+)\[(\d+)\]', part)
            if array_match:
                key, index = array_match.groups()
                if isinstance(current, dict) and key in current:
                    arr = current[key]
                    if isinstance(arr, list) and len(arr) > int(index):
                        current = arr[int(index)]
                    else:
                        return None
                else:
                    return None
            elif isinstance(current, dict):
                current = current.get(part)
            else:
                return None

        return current

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

            jobs_json = match.group(1)

            # Handle escaped JSON (e.g., Apple's JSON.parse("..."))
            if self.config.get('needs_unescape'):
                jobs_json = jobs_json.encode().decode('unicode_escape')

            jobs_json = self.clean_json_string(jobs_json)
            data = json.loads(jobs_json)

            # Navigate to jobs array if json_path is specified
            json_path = self.config.get('json_path')
            if json_path:
                jobs = self._navigate_json_path(data, json_path)
                if jobs is None:
                    logger.warning(f"Could not find jobs at path '{json_path}'")
                    return []
            else:
                jobs = data

            if not isinstance(jobs, list):
                logger.warning(f"Expected list of jobs, got {type(jobs)}")
                return []

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
            field_spec: Field name (str), dot-path (str), or list of fallback field names

        Returns:
            Field value or empty string if not found
        """
        if field_spec is None:
            return ""
        if isinstance(field_spec, list):
            for field in field_spec:
                value = self._get_field_value(job_data, field)
                if value:
                    return value
            return ""
        # Support dot-notation and array indexing
        if '.' in field_spec or '[' in field_spec:
            return self._navigate_json_path(job_data, field_spec) or ""
        return job_data.get(field_spec, "")

    def _build_url(self, job_data: Dict[str, Any]) -> str:
        """Build job URL from template or field mapping.

        Args:
            job_data: Raw job data

        Returns:
            Job URL string
        """
        url_template = self.config.get('url_template')
        if url_template:
            # Replace {field} placeholders with values from job_data
            url = url_template
            for match in re.finditer(r'\{(\w+)\}', url_template):
                field = match.group(1)
                value = job_data.get(field, '')
                url = url.replace(f'{{{field}}}', str(value))
            return url

        # Fall back to field mapping
        return self._get_field_value(job_data, self.field_mapping.get('job_url', 'url'))

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
            description = self._get_field_value(job_data, self.field_mapping.get('description', ''))

            return {
                "external_id": str(external_id) if external_id else "",
                "title": self._get_field_value(job_data, self.field_mapping.get('title', 'title')),
                "description": description or "",
                "location": location,
                "job_url": self._build_url(job_data),
                "department": self._get_field_value(job_data, self.field_mapping.get('department')) or None,
                "employment_type": self._get_field_value(job_data, self.field_mapping.get('employment_type')) or None,
                "posted_date": None,
                "is_remote": is_remote,
            }
        except Exception as e:
            logger.error(f"Error parsing embedded JS job: {e}")
            return {}

