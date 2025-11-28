"""RSS/XML feed job parser."""
import re
from typing import Dict, Any
from email.utils import parsedate_to_datetime
from loguru import logger

from .base_parser import BaseJobParser


class RSSParser(BaseJobParser):
    """Parser for RSS/XML job feeds (TalentBrew format used by Palo Alto Networks)."""
    
    def parse(self, item) -> Dict[str, Any]:
        """Parse job from RSS/XML item.
        
        Args:
            item: XML element from RSS feed
            
        Returns:
            Standardized job dictionary
        """
        try:
            # Extract fields from XML
            title_elem = item.find('title')
            link_elem = item.find('link')
            guid_elem = item.find('guid')
            pub_date_elem = item.find('pubDate')
            category_elem = item.find('category')
            description_elem = item.find('description')
            
            # Parse title to extract location (TalentBrew format: "Job Title - (Location)")
            title_text = title_elem.text if title_elem is not None else ""
            location = ""
            
            # TalentBrew format: "Title - (Location)"
            if " - (" in title_text and title_text.endswith(")"):
                parts = title_text.rsplit(" - (", 1)
                title = parts[0].strip()
                location = parts[1].rstrip(")").strip()
            else:
                title = title_text
            
            # Parse posted date
            posted_date = None
            if pub_date_elem is not None and pub_date_elem.text:
                try:
                    posted_date = parsedate_to_datetime(pub_date_elem.text)
                except:
                    pass
            
            # Extract description and remove HTML tags
            description = ""
            if description_elem is not None and description_elem.text:
                description = re.sub(r'<[^>]+>', '', description_elem.text)
                description = description.strip()[:5000]  # Limit length
            
            # Generate external_id from guid or link
            external_id = ""
            if guid_elem is not None and guid_elem.text:
                # GUID format: "86090263200-Dallas,Texas,United States-Sales"
                external_id = guid_elem.text.split("-")[0] if "-" in guid_elem.text else guid_elem.text
            elif link_elem is not None and link_elem.text:
                # Extract ID from URL
                external_id = link_elem.text.split("/")[-1]
            
            return {
                "external_id": external_id,
                "title": title,
                "description": description,
                "location": location,
                "job_url": link_elem.text if link_elem is not None else "",
                "department": category_elem.text if category_elem is not None else None,
                "posted_date": posted_date,
                "employment_type": None,
                "is_remote": "remote" in location.lower() if location else False,
            }
        except Exception as e:
            logger.error(f"Error parsing RSS job: {e}")
            return {}

