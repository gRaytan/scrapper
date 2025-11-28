"""Generic parser for GraphQL job APIs with configurable field mapping."""
from typing import Dict, Any, List, Optional
from .base_parser import BaseJobParser
from src.utils.logger import logger


class GraphQLParser(BaseJobParser):
    """Generic parser for GraphQL job APIs with configurable field mapping."""
    
    def __init__(self, field_mapping: Optional[Dict[str, Any]] = None, url_template: Optional[str] = None):
        """
        Initialize GraphQL parser with field mapping.
        
        Args:
            field_mapping: Dictionary mapping standard fields to GraphQL response fields
            url_template: Template for building job URLs (e.g., "https://company.com/jobs/{id}")
        """
        self.field_mapping = field_mapping or self._get_default_meta_mapping()
        self.url_template = url_template or "https://www.metacareers.com/jobs/{id}"
    
    def _get_default_meta_mapping(self) -> Dict[str, Any]:
        """Get default field mapping for Meta (backward compatibility)."""
        return {
            "external_id": "id",
            "title": "title",
            "description": None,
            "location": {
                "field": "locations",
                "transform": "join_list",
                "separator": ", "
            },
            "department": {
                "field": "teams",
                "transform": "join_list",
                "separator": ", "
            },
            "employment_type": None,
            "posted_date": None,
            "is_remote": {
                "field": "locations",
                "transform": "contains_keywords",
                "keywords": ["remote", "virtual", "work from home"]
            }
        }
    
    def _extract_field_value(self, job_data: Dict[str, Any], field_config: Any) -> Any:
        """
        Extract field value from job data based on field configuration.
        
        Args:
            job_data: Raw job data from GraphQL
            field_config: Field configuration (string or dict with transform)
            
        Returns:
            Extracted and transformed value
        """
        # If field_config is None, return None
        if field_config is None:
            return None
        
        # If field_config is a string, just get the value
        if isinstance(field_config, str):
            return job_data.get(field_config)
        
        # If field_config is a dict, apply transformations
        if isinstance(field_config, dict):
            field_name = field_config.get("field")
            transform = field_config.get("transform")
            
            if not field_name:
                return None
            
            value = job_data.get(field_name)
            
            # Apply transformation
            if transform == "join_list" and isinstance(value, list):
                separator = field_config.get("separator", ", ")
                return separator.join(str(v) for v in value) if value else ""
            
            elif transform == "contains_keywords":
                keywords = field_config.get("keywords", [])
                if isinstance(value, list):
                    # Join list first, then check keywords
                    text = ", ".join(str(v) for v in value).lower()
                elif isinstance(value, str):
                    text = value.lower()
                else:
                    return False
                return any(keyword.lower() in text for keyword in keywords)
            
            elif transform == "extract_first" and isinstance(value, list):
                return value[0] if value else None
            
            elif transform == "direct":
                return value
            
            else:
                # No transform or unknown transform, return raw value
                return value
        
        return None
    
    def parse(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse job from GraphQL format using field mapping.
        
        Args:
            job_data: Raw job data from GraphQL API
            
        Returns:
            Standardized job dictionary
        """
        try:
            # Extract all fields using field mapping
            result = {}
            
            for standard_field, field_config in self.field_mapping.items():
                result[standard_field] = self._extract_field_value(job_data, field_config)
            
            # Build job URL using template if external_id is available
            if self.url_template and result.get("external_id"):
                result["job_url"] = self.url_template.format(id=result["external_id"])
            
            # Ensure description is empty string if None
            if result.get("description") is None:
                result["description"] = ""
            
            return result
            
        except Exception as e:
            logger.error(f"Error parsing GraphQL job: {e}")
            return {}


# Backward compatibility: MetaParser is an alias for GraphQLParser with Meta defaults
class MetaParser(GraphQLParser):
    """Meta-specific GraphQL parser (backward compatibility)."""
    
    def __init__(self):
        """Initialize with Meta-specific defaults."""
        super().__init__(
            field_mapping=self._get_default_meta_mapping(),
            url_template="https://www.metacareers.com/jobs/{id}"
        )

