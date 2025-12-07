"""Service for matching company names from external sources to database companies."""
from typing import Optional, Tuple
from difflib import SequenceMatcher
from sqlalchemy.orm import Session

from src.models.company import Company
from src.storage.repositories.company_repo import CompanyRepository
from src.utils.logger import logger


class CompanyMatchingService:
    """Service to match external company names with database companies."""
    
    # Common company name variations and aliases
    COMPANY_ALIASES = {
        "Meta": ["Facebook", "Meta Platforms", "Meta Platforms Inc"],
        "Google": ["Google LLC", "Alphabet", "Alphabet Inc"],
        "Microsoft": ["Microsoft Corporation", "MSFT"],
        "Amazon": ["Amazon.com", "Amazon Web Services", "AWS"],
        "Apple": ["Apple Inc", "Apple Computer"],
        "NVIDIA": ["Nvidia Corporation", "nVidia"],
        "Intel": ["Intel Corporation"],
        "Wiz": ["Wiz.io", "Wiz Inc"],
        "Monday.com": ["monday.com", "Monday", "monday"],
        "Check Point": ["Check Point Software", "Check Point Software Technologies"],
        "CyberArk": ["CyberArk Software"],
        "Mobileye": ["Mobileye Global", "Mobileye Inc"],
        "SentinelOne": ["Sentinel One", "SentinelOne Inc"],
        "Palo Alto Networks": ["Palo Alto", "PANW"],
        "Trigo Vision": ["Trigo", "Trigo Retail"],
    }
    
    # Minimum similarity threshold for fuzzy matching
    SIMILARITY_THRESHOLD = 0.85
    
    def __init__(self, session: Session):
        """Initialize service with database session."""
        self.session = session
        self.company_repo = CompanyRepository(session)
    
    def normalize_company_name(self, name: str) -> str:
        """
        Normalize company name for matching.
        
        Args:
            name: Raw company name
            
        Returns:
            Normalized company name
        """
        if not name:
            return ""
        
        # Convert to lowercase
        normalized = name.lower().strip()
        
        # Remove common suffixes
        suffixes = [
            " inc", " inc.", " incorporated",
            " ltd", " ltd.", " limited",
            " llc", " llc.",
            " corp", " corp.", " corporation",
            " plc", " plc.",
            " sa", " s.a.",
            " gmbh",
        ]
        
        for suffix in suffixes:
            if normalized.endswith(suffix):
                normalized = normalized[:-len(suffix)].strip()
        
        # Remove special characters except spaces
        normalized = ''.join(c if c.isalnum() or c.isspace() else '' for c in normalized)
        
        # Remove extra whitespace
        normalized = ' '.join(normalized.split())
        
        return normalized
    
    def calculate_similarity(self, name1: str, name2: str) -> float:
        """
        Calculate similarity score between two company names.
        
        Args:
            name1: First company name
            name2: Second company name
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        norm1 = self.normalize_company_name(name1)
        norm2 = self.normalize_company_name(name2)
        
        if not norm1 or not norm2:
            return 0.0
        
        # Exact match after normalization
        if norm1 == norm2:
            return 1.0
        
        # Use SequenceMatcher for fuzzy matching
        return SequenceMatcher(None, norm1, norm2).ratio()
    
    def check_alias_match(self, external_name: str, db_company: Company) -> bool:
        """
        Check if external name matches any known alias of the database company.
        
        Args:
            external_name: Company name from external source
            db_company: Company from database
            
        Returns:
            True if alias match found
        """
        normalized_external = self.normalize_company_name(external_name)
        normalized_db = self.normalize_company_name(db_company.name)
        
        # Check if db company has aliases
        for canonical_name, aliases in self.COMPANY_ALIASES.items():
            canonical_normalized = self.normalize_company_name(canonical_name)
            
            # Check if db company matches canonical or any alias
            db_matches = (normalized_db == canonical_normalized or 
                         any(self.normalize_company_name(alias) == normalized_db 
                             for alias in aliases))
            
            if db_matches:
                # Check if external name matches canonical or any alias
                external_matches = (normalized_external == canonical_normalized or
                                  any(self.normalize_company_name(alias) == normalized_external
                                      for alias in aliases))
                if external_matches:
                    return True
        
        return False
    
    def find_matching_company(self, external_company_name: str) -> Tuple[Optional[Company], float]:
        """
        Find matching company in database.
        
        Args:
            external_company_name: Company name from external source (e.g., LinkedIn)
            
        Returns:
            Tuple of (Company instance or None, confidence score 0.0-1.0)
        """
        if not external_company_name:
            return None, 0.0
        
        # Get all active companies from database
        all_companies = self.company_repo.get_all(is_active=True)
        
        best_match = None
        best_score = 0.0
        
        for company in all_companies:
            # Check for alias match first (highest confidence)
            if self.check_alias_match(external_company_name, company):
                logger.info(f"Alias match: '{external_company_name}' -> '{company.name}' (confidence: 1.0)")
                return company, 1.0
            
            # Calculate similarity score
            score = self.calculate_similarity(external_company_name, company.name)
            
            if score > best_score:
                best_score = score
                best_match = company
        
        # Only return match if above threshold
        if best_score >= self.SIMILARITY_THRESHOLD:
            logger.info(f"Fuzzy match: '{external_company_name}' -> '{best_match.name}' (confidence: {best_score:.2f})")
            return best_match, best_score
        
        logger.info(f"No match found for '{external_company_name}' (best score: {best_score:.2f})")
        return None, best_score

