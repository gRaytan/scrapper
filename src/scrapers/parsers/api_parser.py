"""Generic API parser for JSON-based job APIs with configurable field mapping."""
import re
from typing import Dict, Any, Optional, List
from dateutil import parser as date_parser
from datetime import datetime
from loguru import logger

from .base_parser import BaseJobParser


class APIParser(BaseJobParser):
    """Generic parser for JSON API responses with configurable field mapping.
    
    This parser supports various transformations to handle different API formats:
    - strip_html: Remove HTML tags from text
    - parse_date: Parse date strings into datetime objects
    - prepend_url: Build full URLs from relative paths
    - contains_keywords: Check if text contains any keywords (for is_remote, etc.)
    - extract_first: Get first element from array
    - join_list: Join array elements into string
    - direct: Return value as-is
    
    Example field_mapping:
    {
        "external_id": ["id_icims", "id"],  # Try multiple fields
        "title": "title",  # Simple field
        "description": {
            "field": "description",
            "transform": "strip_html",
            "max_length": 5000
        },
        "posted_date": {
            "field": "posted_date",
            "transform": "parse_date",
            "date_format": "natural"
        },
        "job_url": {
            "field": "job_path",
            "transform": "prepend_url",
            "base_url": "https://www.amazon.jobs"
        },
        "is_remote": {
            "field": "location",
            "transform": "contains_keywords",
            "keywords": ["remote", "virtual", "work from home"]
        }
    }
    """
    
    def __init__(self, field_mapping: Optional[Dict[str, Any]] = None, url_template: Optional[str] = None):
        """Initialize API parser with field mapping.
        
        Args:
            field_mapping: Dictionary mapping standard fields to API response fields
            url_template: Optional template for building job URLs (e.g., "https://company.com/jobs/{id}")
        """
        self.field_mapping = field_mapping or {}
        self.url_template = url_template
    
    def parse(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse job from API response using field mapping.
        
        Args:
            job_data: Job data from API response
            
        Returns:
            Standardized job dictionary
        """
        try:
            result = {}
            
            # Process each field in the mapping
            for standard_field, field_config in self.field_mapping.items():
                value = self._extract_field_value(job_data, field_config)
                result[standard_field] = value
            
            return result
        except Exception as e:
            logger.error(f"Error parsing API job: {e}")
            return {}
    
    def _extract_field_value(self, job_data: Dict[str, Any], field_config: Any) -> Any:
        """Extract and transform a field value based on configuration.
        
        Args:
            job_data: Raw job data from API
            field_config: Field configuration (string, list, or dict)
            
        Returns:
            Extracted and transformed value
        """
        # Simple string field name
        if isinstance(field_config, str):
            return job_data.get(field_config)
        
        # List of field names (try each until one has a value)
        if isinstance(field_config, list):
            for field_name in field_config:
                value = job_data.get(field_name)
                if value:
                    return value
            return None
        
        # Dictionary with field and transformation
        if isinstance(field_config, dict):
            field_name = field_config.get("field")
            transform = field_config.get("transform", "direct")
            
            # Get raw value
            if isinstance(field_name, list):
                # Try multiple fields
                raw_value = None
                for fname in field_name:
                    raw_value = job_data.get(fname)
                    if raw_value:
                        break
            else:
                raw_value = job_data.get(field_name)
            
            # Apply transformation
            return self._apply_transformation(raw_value, transform, field_config)
        
        return None
    
    def _apply_transformation(self, value: Any, transform: str, config: Dict[str, Any]) -> Any:
        """Apply a transformation to a field value.
        
        Args:
            value: Raw value to transform
            transform: Transformation type
            config: Full field configuration
            
        Returns:
            Transformed value
        """
        if value is None:
            return None
        
        if transform == "direct":
            return value
        
        elif transform == "strip_html":
            # Remove HTML tags
            if isinstance(value, str):
                clean_text = re.sub(r'<[^>]+>', '', value)
                max_length = config.get("max_length")
                if max_length:
                    clean_text = clean_text[:max_length]
                return clean_text
            return value
        
        elif transform == "parse_date":
            # Parse date string
            if isinstance(value, str):
                try:
                    return date_parser.parse(value)
                except Exception as e:
                    logger.debug(f"Failed to parse date '{value}': {e}")
                    return None
            return value
        
        elif transform == "prepend_url":
            # Build full URL from path
            if isinstance(value, str):
                base_url = config.get("base_url", "")
                if value.startswith("http"):
                    return value
                return f"{base_url}{value}"
            return value
        
        elif transform == "contains_keywords":
            # Check if text contains any keywords
            if isinstance(value, str):
                keywords = config.get("keywords", [])
                return any(keyword.lower() in value.lower() for keyword in keywords)
            return False
        
        elif transform == "extract_first":
            # Get first element from array
            if isinstance(value, list) and len(value) > 0:
                return value[0]
            return value
        
        elif transform == "join_list":
            # Join array into string
            if isinstance(value, list):
                separator = config.get("separator", ", ")
                return separator.join(str(item) for item in value if item)
            return value
        
        else:
            logger.warning(f"Unknown transformation: {transform}")
            return value


class AmazonParser(APIParser):
    """Backward-compatible parser for Amazon API format.
    
    This is a convenience class that uses the generic APIParser with
    Amazon-specific default field mapping.
    """
    
    def __init__(self):
        """Initialize Amazon parser with default field mapping."""
        super().__init__(
            field_mapping=self._get_default_amazon_mapping(),
            url_template="https://www.amazon.jobs{job_path}"
        )
    
    def _get_default_amazon_mapping(self) -> Dict[str, Any]:
        """Get default field mapping for Amazon API.
        
        Returns:
            Field mapping configuration for Amazon
        """
        return {
            "external_id": ["id_icims", "id"],
            "title": "title",
            "description": {
                "field": "description",
                "transform": "strip_html",
                "max_length": 5000
            },
            "location": ["location", "normalized_location"],
            "department": ["job_category", "business_category"],
            "employment_type": "job_schedule_type",
            "posted_date": {
                "field": "posted_date",
                "transform": "parse_date",
                "date_format": "natural"
            },
            "job_url": {
                "field": "job_path",
                "transform": "prepend_url",
                "base_url": "https://www.amazon.jobs"
            },
            "is_remote": {
                "field": "location",
                "transform": "contains_keywords",
                "keywords": ["remote", "virtual", "work from home"]
            }
        }

