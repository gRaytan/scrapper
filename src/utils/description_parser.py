"""Parser for extracting structured sections from job descriptions."""
import re
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class ParsedDescription:
    """Structured job description sections."""
    about: str = ""
    responsibilities: List[str] = None
    requirements: List[str] = None
    nice_to_have: List[str] = None
    benefits: List[str] = None
    
    def __post_init__(self):
        if self.responsibilities is None:
            self.responsibilities = []
        if self.requirements is None:
            self.requirements = []
        if self.nice_to_have is None:
            self.nice_to_have = []
        if self.benefits is None:
            self.benefits = []
    
    def has_structured_content(self) -> bool:
        """Check if any structured sections were extracted."""
        return bool(
            self.responsibilities or 
            self.requirements or 
            self.nice_to_have or 
            self.benefits
        )


class DescriptionParser:
    """Parse raw job description text into structured sections."""
    
    # Section header patterns (case-insensitive)
    SECTION_PATTERNS = {
        'responsibilities': [
            r'(?:^|\n)\s*(?:key\s+)?responsibilities[:\s]*(?:\n|$)',
            r'(?:^|\n)\s*what\s+you\'?ll?\s+(?:do|be\s+doing)[:\s]*(?:\n|$)',
            r'(?:^|\n)\s*your\s+role[:\s]*(?:\n|$)',
            r'(?:^|\n)\s*the\s+role[:\s]*(?:\n|$)',
            r'(?:^|\n)\s*job\s+duties[:\s]*(?:\n|$)',
            r'(?:^|\n)\s*how\s+you\'?ll?\s+make\s+an?\s+impact[:\s]*(?:\n|$)',
        ],
        'requirements': [
            r'(?:^|\n)\s*(?:minimum\s+)?requirements?[:\s]*(?:\n|$)',
            r'(?:^|\n)\s*(?:required\s+)?qualifications?[:\s]*(?:\n|$)',
            r'(?:^|\n)\s*what\s+(?:we\'?re?\s+looking\s+for|you\'?ll?\s+need)[:\s]*(?:\n|$)',
            r'(?:^|\n)\s*to\s+thrive\s+in\s+this\s+role[,:\s]+you\'?ll?\s+need[:\s]*(?:\n|$)',
            r'(?:^|\n)\s*must\s+have[:\s]*(?:\n|$)',
            r'(?:^|\n)\s*skills\s+(?:and\s+)?(?:experience|qualifications)[:\s]*(?:\n|$)',
        ],
        'nice_to_have': [
            r'(?:^|\n)\s*nice\s+to\s+have[:\s]*(?:\n|$)',
            r'(?:^|\n)\s*preferred\s+(?:qualifications?|skills?)[:\s]*(?:\n|$)',
            r'(?:^|\n)\s*bonus\s+(?:points?|if\s+you)[:\s]*(?:\n|$)',
            r'(?:^|\n)\s*(?:it\'?s?\s+)?a\s+plus\s+if[:\s]*(?:\n|$)',
            r'(?:^|\n)\s*desired\s+(?:skills?|qualifications?)[:\s]*(?:\n|$)',
        ],
        'benefits': [
            r'(?:^|\n)\s*(?:what\s+we\s+offer|benefits?|perks?)[:\s]*(?:\n|$)',
            r'(?:^|\n)\s*why\s+(?:join\s+us|work\s+(?:here|with\s+us)|[a-z]+\?)[:\s]*(?:\n|$)',
            r'(?:^|\n)\s*well-?being[:\s]*(?:\n|$)',
            r'(?:^|\n)\s*compensation\s+(?:and|&)\s+benefits?[:\s]*(?:\n|$)',
        ],
        'about': [
            r'(?:^|\n)\s*about\s+(?:the\s+)?(?:role|position|this\s+role|this\s+position)[:\s]*(?:\n|$)',
            r'(?:^|\n)\s*(?:role|position)\s+(?:overview|summary|description)[:\s]*(?:\n|$)',
            r'(?:^|\n)\s*overview[:\s]*(?:\n|$)',
        ],
    }
    
    @classmethod
    def parse(cls, description: Optional[str]) -> ParsedDescription:
        """
        Parse a raw job description into structured sections.
        
        Args:
            description: Raw job description text
            
        Returns:
            ParsedDescription with extracted sections
        """
        if not description:
            return ParsedDescription()
        
        result = ParsedDescription()
        
        # Find all section boundaries
        sections = cls._find_sections(description)
        
        if not sections:
            # No sections found - use entire description as "about"
            result.about = description.strip()
            return result
        
        # Sort sections by position
        sorted_sections = sorted(sections.items(), key=lambda x: x[1])
        
        # Extract content for each section
        for i, (section_type, start_pos) in enumerate(sorted_sections):
            # Find end position (start of next section or end of text)
            if i + 1 < len(sorted_sections):
                end_pos = sorted_sections[i + 1][1]
            else:
                end_pos = len(description)
            
            # Extract section content
            content = description[start_pos:end_pos]
            
            # Remove the header line
            content = cls._remove_header(content)
            
            # Parse into list items or keep as text
            if section_type == 'about':
                result.about = content.strip()
            else:
                items = cls._extract_list_items(content)
                setattr(result, section_type, items)
        
        # If no "about" section found, use text before first section
        if not result.about and sorted_sections:
            first_section_pos = sorted_sections[0][1]
            if first_section_pos > 0:
                result.about = description[:first_section_pos].strip()
        
        return result
    
    @classmethod
    def _find_sections(cls, text: str) -> Dict[str, int]:
        """Find all section headers and their positions."""
        sections = {}
        
        for section_type, patterns in cls.SECTION_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    # Only keep the first match for each section type
                    if section_type not in sections:
                        sections[section_type] = match.start()
                    break
        
        return sections
    
    @classmethod
    def _remove_header(cls, content: str) -> str:
        """Remove the section header line from content."""
        lines = content.split('\n')
        if lines:
            # Skip the first line (header) and any empty lines after it
            start_idx = 1
            while start_idx < len(lines) and not lines[start_idx].strip():
                start_idx += 1
            return '\n'.join(lines[start_idx:])
        return content
    
    @classmethod
    def _extract_list_items(cls, content: str) -> List[str]:
        """Extract list items from content."""
        items = []
        lines = content.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Remove common bullet point prefixes
            line = re.sub(r'^[\-\*\•\◦\▪\→\►\✓\✔\☑\·]\s*', '', line)
            line = re.sub(r'^\d+[\.\)]\s*', '', line)  # Numbered lists
            
            if line and len(line) > 5:  # Skip very short items
                items.append(line)
        
        return items

