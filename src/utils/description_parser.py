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
    # Patterns can match at start of line OR inline (headers often run together in scraped text)
    SECTION_PATTERNS = {
        'responsibilities': [
            r'(?:^|\n)\s*(?:key\s+)?responsibilities[:\s]*',
            r'Key\s+Responsibilities(?=[A-Z])',  # Inline: "Key ResponsibilitiesLead..."
            r'(?:^|\n)\s*what\s+you\'?ll?\s+(?:do|be\s+doing)[:\s]*',
            r'(?:^|\n)\s*your\s+role[:\s]*',
            r'(?:^|\n)\s*the\s+role[:\s]*',
            r'(?:^|\n)\s*job\s+duties[:\s]*',
            r'(?:^|\n)\s*how\s+you\'?ll?\s+make\s+an?\s+impact[:\s]*',
            r'(?:^|\n)\s*what\s+you\'?ll?\s+own[:\s]*',
            r'(?:^|\n)\s*in\s+this\s+role[,\s]+you\s+will[:\s]*',
        ],
        'requirements': [
            r'(?:^|\n)\s*(?:minimum\s+)?requirements?[:\s]*',
            r'(?:^|\n)\s*(?:required\s+)?qualifications?[:\s]*',
            r'Qualifications\s+Required\s+Qualifications',  # Handle malformed "Qualifications Required Qualifications"
            r'Required\s+Qualifications(?=[A-Z0-9])',  # Inline: "Required Qualifications12+ years..."
            r'(?:^|\n)\s*what\s+(?:we\'?re?\s+looking\s+for|you\'?ll?\s+need)[:\s]*',
            r'to\s+thrive\s+in\s+this\s+role[,:\s]+you\'?ll?\s+need[:\s]*',  # Inline pattern
            r'(?:^|\n)\s*must\s+have[:\s]*',
            r'(?:^|\n)\s*skills\s+(?:and\s+)?(?:experience|qualifications)[:\s]*',
            r'(?:^|\n)\s*basic\s+qualifications?[:\s]*',
            r'(?:^|\n)\s*you\s+(?:should|must)\s+have[:\s]*',
        ],
        'nice_to_have': [
            r'(?:^|\n)\s*nice\s+to\s+have[:\s]*',
            r'(?:^|\n)\s*preferred\s+(?:qualifications?|skills?)[:\s]*',
            r'Preferred\s+Qualifications[:\s]*',  # Inline match
            r'(?:^|\n)\s*bonus\s+(?:points?|if\s+you)[:\s]*',
            r'(?:^|\n)\s*(?:it\'?s?\s+)?a\s+plus\s+if[:\s]*',
            r'(?:^|\n)\s*desired\s+(?:skills?|qualifications?)[:\s]*',
            r'(?:^|\n)\s*additional\s+(?:skills?|qualifications?)[:\s]*',
        ],
        'benefits': [
            r'(?:^|\n)\s*(?:what\s+we\s+offer|benefits?|perks?)[:\s]*',
            r'(?:^|\n)\s*why\s+(?:join\s+us|work\s+(?:here|with\s+us)|[a-z]+\?)[:\s]*',
            r'(?:^|\n)\s*well-?being[:\s]*',
            r'(?:^|\n)\s*compensation\s+(?:and|&)\s+benefits?[:\s]*',
            r'(?:^|\n)\s*our\s+commitment[:\s]*',
            r'Our\s+Commitment(?=[A-Z\s])',  # Inline match
        ],
        'about': [
            r'(?:^|\n)\s*about\s+(?:the\s+)?(?:role|position|this\s+role|this\s+position|us|company)[:\s]*',
            r'(?:^|\n)\s*(?:role|position|job)\s+(?:overview|summary|description)[:\s]*',
            r'(?:^|\n)\s*overview[:\s]*',
            r'(?:^|\n)\s*job\s+summary[:\s]*',
            r'Job\s+Summary(?=[A-Z])',  # Inline: "Job SummaryThe Team..."
            r'(?:^|\n)\s*who\s+we\s+are[:\s]*',
            r'Who\s+We\s+Are(?=[A-Z])',  # Inline match
            r'(?:^|\n)\s*our\s+mission[:\s]*',
            r'Our\s+Mission(?=[A-Z])',  # Inline match
            r'(?:^|\n)\s*the\s+team[:\s]*',
            r'(?:^|\n)\s*about\s+this\s+job[:\s]*',
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

        # Sort sections by header start position
        sorted_sections = sorted(sections.items(), key=lambda x: x[1][0])

        # Extract content for each section
        for i, (section_type, (header_start, header_end)) in enumerate(sorted_sections):
            # Find end position (start of next section header or end of text)
            if i + 1 < len(sorted_sections):
                end_pos = sorted_sections[i + 1][1][0]  # Start of next header
            else:
                end_pos = len(description)

            # Extract section content (starting after the header)
            content = description[header_end:end_pos].strip()

            # Parse into list items or keep as text
            if section_type == 'about':
                result.about = content
            else:
                items = cls._extract_list_items(content)
                setattr(result, section_type, items)

        # If no "about" section found, use text before first section
        if not result.about and sorted_sections:
            first_section_start = sorted_sections[0][1][0]
            if first_section_start > 0:
                result.about = description[:first_section_start].strip()

        return result
    
    @classmethod
    def _find_sections(cls, text: str) -> Dict[str, int]:
        """Find all section headers and their positions (end of header)."""
        sections = {}

        for section_type, patterns in cls.SECTION_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    # Only keep the first match for each section type
                    # Store the END position of the header so content starts after it
                    if section_type not in sections:
                        sections[section_type] = (match.start(), match.end())
                    break

        return sections

    @classmethod
    def _extract_list_items(cls, content: str) -> List[str]:
        """Extract list items from content."""
        items = []

        # First try splitting by newlines
        lines = content.strip().split('\n')

        # If we only have one line, try splitting by various patterns
        if len(lines) == 1 and len(content) > 100:
            text = content.strip()

            # Protect common abbreviations with periods from being split
            # Replace with placeholder tokens
            text = re.sub(r'B\.Sc\.?', '[[BSC]]', text)
            text = re.sub(r'M\.Sc\.?', '[[MSC]]', text)
            text = re.sub(r'Ph\.D\.?', '[[PHD]]', text)
            text = re.sub(r'B\.A\.?', '[[BA]]', text)
            text = re.sub(r'M\.A\.?', '[[MA]]', text)
            text = re.sub(r'B\.S\.(?!\s*c)', '[[BS]]', text)  # B.S. but not B.Sc.
            text = re.sub(r'M\.S\.(?!\s*c)', '[[MS]]', text)  # M.S. but not M.Sc.

            # Pattern 1: Split on patterns like "experience8+" -> "experience" | "8+"
            # (lowercase letter followed immediately by digit with +)
            text = re.sub(r'([a-z])(\d+\+)', r'\1. \2', text)

            # Pattern 2: Split on patterns like "innovationOversee" or "environmentBSC"
            # Require at least 3 lowercase letters before uppercase to avoid breaking
            # acronyms like "SaaS", "IoT", "AI", etc.
            text = re.sub(r'([a-z]{3,})([A-Z\[])', r'\1. \2', text)

            # Now split by sentence-ending patterns (period followed by capital letter or number)
            sentences = re.split(r'\.(?:\s+)?(?=[A-Z0-9\[])', text)
            if len(sentences) > 1:
                lines = []
                for s in sentences:
                    s = s.strip()
                    if s:
                        # Restore abbreviations
                        s = s.replace('[[BSC]]', 'B.Sc.').replace('[[MSC]]', 'M.Sc.')
                        s = s.replace('[[PHD]]', 'Ph.D.').replace('[[BA]]', 'B.A.')
                        s = s.replace('[[MA]]', 'M.A.').replace('[[BS]]', 'B.S.')
                        s = s.replace('[[MS]]', 'M.S.')
                        lines.append(s + ('.' if not s.endswith('.') else ''))

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Remove common bullet point prefixes
            line = re.sub(r'^[\-\*\•\◦\▪\→\►\✓\✔\☑\·]\s*', '', line)
            line = re.sub(r'^\d+[\.\)]\s*', '', line)  # Numbered lists

            if line and len(line) > 10:  # Skip very short items
                items.append(line)

        return items

