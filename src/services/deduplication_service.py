"""Service for detecting duplicate job postings."""
from typing import Optional, Tuple, List
from difflib import SequenceMatcher
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from src.models.job_position import JobPosition
from src.storage.repositories.job_repo import JobPositionRepository
from src.utils.logger import logger


class JobDeduplicationService:
    """Service to detect duplicate job postings based on company, title, and location."""
    
    # Thresholds for duplicate detection
    HIGH_CONFIDENCE_THRESHOLD = 0.95  # Very likely duplicate
    MEDIUM_CONFIDENCE_THRESHOLD = 0.85  # Possibly duplicate, needs review
    LOW_CONFIDENCE_THRESHOLD = 0.75  # Unlikely duplicate
    
    def __init__(self, session: Session):
        """Initialize service with database session."""
        self.session = session
        self.job_repo = JobPositionRepository(session)
    
    def normalize_text(self, text: str) -> str:
        """
        Normalize text for comparison.
        
        Args:
            text: Raw text
            
        Returns:
            Normalized text
        """
        if not text:
            return ""
        
        # Convert to lowercase
        normalized = text.lower().strip()
        
        # Remove extra whitespace
        normalized = ' '.join(normalized.split())
        
        # Remove common punctuation
        for char in [',', '.', '-', '/', '|', '(', ')', '[', ']']:
            normalized = normalized.replace(char, ' ')
        
        # Remove extra whitespace again
        normalized = ' '.join(normalized.split())
        
        return normalized
    
    def calculate_text_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two text strings.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        norm1 = self.normalize_text(text1)
        norm2 = self.normalize_text(text2)
        
        if not norm1 or not norm2:
            return 0.0
        
        # Exact match
        if norm1 == norm2:
            return 1.0
        
        # Use SequenceMatcher for fuzzy matching
        return SequenceMatcher(None, norm1, norm2).ratio()
    
    # Israeli city name variations for normalization
    CITY_ALIASES = {
        'tel aviv': ['tel aviv yafo', 'tel aviv-yafo', 'tel-aviv', 'tlv'],
        'herzliya': ['herzliya pituach', 'herzliya pituah'],
        'ramat gan': ['ramat-gan'],
        'petah tikva': ['petach tikva', 'petah-tikva', 'petach-tikva'],
        'beer sheva': ["be'er sheva", 'beersheva', 'beer-sheva'],
        'raanana': ["ra'anana", 'ra anana'],
        'kfar saba': ['kfar-saba'],
        'rishon lezion': ['rishon le zion', 'rishon-lezion'],
        'netanya': ['netania'],
        'haifa': [],
        'jerusalem': ['yerushalayim'],
        'yokneam': ["yoqne'am", 'yokneam illit'],
    }

    def normalize_city_name(self, location: str) -> str:
        """
        Normalize city name to a canonical form.
        Returns the city that appears FIRST in the location string.

        Args:
            location: Raw location string

        Returns:
            Normalized city name
        """
        if not location:
            return ""

        loc_lower = location.lower()

        # Find all matching cities and their positions in the string
        matches = []
        for canonical, aliases in self.CITY_ALIASES.items():
            # Check canonical name
            pos = loc_lower.find(canonical)
            if pos != -1:
                matches.append((pos, canonical))
            # Check aliases
            for alias in aliases:
                pos = loc_lower.find(alias)
                if pos != -1:
                    matches.append((pos, canonical))

        # Return the city that appears first in the string
        if matches:
            matches.sort(key=lambda x: x[0])
            return matches[0][1]

        return loc_lower

    def calculate_location_similarity(self, loc1: str, loc2: str) -> float:
        """
        Calculate similarity between two locations.
        Handles variations like "Tel Aviv" vs "Tel Aviv-Yafo, Tel Aviv District, Israel".

        Args:
            loc1: First location
            loc2: Second location

        Returns:
            Similarity score between 0.0 and 1.0
        """
        norm1 = self.normalize_text(loc1)
        norm2 = self.normalize_text(loc2)

        if not norm1 or not norm2:
            return 0.0

        # Exact match
        if norm1 == norm2:
            return 1.0

        # Normalize city names and compare
        city1 = self.normalize_city_name(loc1)
        city2 = self.normalize_city_name(loc2)

        # If both locations resolve to the same city, they're the same
        if city1 and city2 and city1 == city2:
            return 1.0

        # Check if one location contains the other (e.g., "Tel Aviv" in "Tel Aviv, Israel")
        if norm1 in norm2 or norm2 in norm1:
            return 0.95  # High confidence if one contains the other

        # Fuzzy match
        return SequenceMatcher(None, norm1, norm2).ratio()
    
    def calculate_duplicate_score(
        self,
        job1_title: str,
        job1_location: str,
        job2_title: str,
        job2_location: str
    ) -> float:
        """
        Calculate overall duplicate score for two jobs from the same company.
        
        Args:
            job1_title: Title of first job
            job1_location: Location of first job
            job2_title: Title of second job
            job2_location: Location of second job
            
        Returns:
            Duplicate confidence score between 0.0 and 1.0
        """
        # Calculate individual similarities
        title_similarity = self.calculate_text_similarity(job1_title, job2_title)
        location_similarity = self.calculate_location_similarity(job1_location, job2_location)
        
        # Weighted average (title is more important than location)
        # Title: 70%, Location: 30%
        overall_score = (title_similarity * 0.7) + (location_similarity * 0.3)
        
        logger.debug(
            f"Duplicate score calculation:\n"
            f"  Title similarity: {title_similarity:.2f}\n"
            f"  Location similarity: {location_similarity:.2f}\n"
            f"  Overall score: {overall_score:.2f}"
        )
        
        return overall_score
    
    def find_potential_duplicates(
        self,
        company_id: str,
        title: str,
        location: str,
        exclude_job_id: Optional[str] = None
    ) -> List[Tuple[JobPosition, float]]:
        """
        Find potential duplicate jobs for the given job details.
        
        Args:
            company_id: Company UUID
            title: Job title
            location: Job location
            exclude_job_id: Job ID to exclude from search (e.g., the job being checked)
            
        Returns:
            List of tuples (JobPosition, confidence_score) sorted by confidence descending
        """
        # Get all active jobs for this company
        query = self.session.query(JobPosition).filter(
            and_(
                JobPosition.company_id == company_id,
                JobPosition.is_active == True
            )
        )
        
        if exclude_job_id:
            query = query.filter(JobPosition.id != exclude_job_id)
        
        existing_jobs = query.all()
        
        # Calculate duplicate scores for each existing job
        potential_duplicates = []
        for existing_job in existing_jobs:
            score = self.calculate_duplicate_score(
                title, location or "",
                existing_job.title, existing_job.location or ""
            )
            
            # Only include if above low threshold
            if score >= self.LOW_CONFIDENCE_THRESHOLD:
                potential_duplicates.append((existing_job, score))
        
        # Sort by confidence score descending
        potential_duplicates.sort(key=lambda x: x[1], reverse=True)
        
        return potential_duplicates
    
    def check_for_duplicate(
        self,
        company_id: str,
        title: str,
        location: str,
        exclude_job_id: Optional[str] = None
    ) -> Tuple[Optional[JobPosition], float, bool]:
        """
        Check if a job is a duplicate of an existing job.
        
        Args:
            company_id: Company UUID
            title: Job title
            location: Job location
            exclude_job_id: Job ID to exclude from search
            
        Returns:
            Tuple of (potential_duplicate_job, confidence_score, needs_manual_review)
            - If confidence >= HIGH_CONFIDENCE_THRESHOLD: likely duplicate, don't create
            - If MEDIUM <= confidence < HIGH: possible duplicate, create but flag for review
            - If confidence < MEDIUM: not a duplicate, create normally
        """
        potential_duplicates = self.find_potential_duplicates(
            company_id, title, location, exclude_job_id
        )
        
        if not potential_duplicates:
            return None, 0.0, False
        
        # Get the best match
        best_match, best_score = potential_duplicates[0]
        
        if best_score >= self.HIGH_CONFIDENCE_THRESHOLD:
            logger.info(
                f"High confidence duplicate detected (score: {best_score:.2f}):\n"
                f"  New: '{title}' at '{location}'\n"
                f"  Existing: '{best_match.title}' at '{best_match.location}'"
            )
            return best_match, best_score, False
        
        elif best_score >= self.MEDIUM_CONFIDENCE_THRESHOLD:
            logger.warning(
                f"Possible duplicate detected (score: {best_score:.2f}) - needs manual review:\n"
                f"  New: '{title}' at '{location}'\n"
                f"  Existing: '{best_match.title}' at '{best_match.location}'"
            )
            return best_match, best_score, True
        
        else:
            logger.debug(f"No duplicate found (best score: {best_score:.2f})")
            return None, best_score, False

