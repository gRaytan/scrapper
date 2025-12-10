"""
Location Filter Service - Filters jobs based on allowed locations/countries.
"""
import re
from typing import List, Optional, Set
from src.utils.logger import logger
from config.settings import settings


class LocationFilterService:
    """
    Service to filter jobs based on location.
    
    Validates if a job's location matches allowed countries/regions.
    """
    
    # Default Israel location patterns (case-insensitive)
    ISRAEL_PATTERNS = [
        r'\bisrael\b',
        r'\btel[- ]?aviv\b',
        r'\bherzliya\b',
        r'\bramat[- ]?gan\b',
        r'\bhaifa\b',
        r'\bjerusalem\b',
        r'\bnetanya\b',
        r'\braanana\b',
        r'\bra\'?anana\b',
        r'\bpetah[- ]?tikva\b',
        r'\bpetach[- ]?tikva\b',
        r'\brehovot\b',
        r'\byokneam\b',
        r'\bkfar[- ]?saba\b',
        r'\brishon[- ]?le[- ]?zion\b',
        r'\bholon\b',
        r'\bgivatayim\b',
        r'\bbnei[- ]?brak\b',
        r'\brosh[- ]?ha[- ]?ayin\b',
        r'\bor[- ]?yehuda\b',
        r'\bcaesarea\b',
        r'\bashdod\b',
        r'\bbeersheba\b',
        r'\bbeer[- ]?sheva\b',
        r'\bmodiin\b',
        r'\bmod\'?iin\b',
        r'\bnazareth\b',
        r'\bakko\b',
        r'\bacre\b',
        r'\beilat\b',
        r'\bashkelon\b',
        r'\bbat[- ]?yam\b',
        r'\blod\b',
        r'\bramla\b',
        r'\bnahariya\b',
        r'\bkiryat\b',
        r'\btiberias\b',
        r'\bafula\b',
        r'\bdimona\b',
        r'\barad\b',
        r'\bsderot\b',
        r'\bnetivot\b',
        r'\bofakim\b',
        r'\byavne\b',
        r'\bness[- ]?ziona\b',
        r'\beven[- ]?yehuda\b',
        r'\bhod[- ]?hasharon\b',
        r'\bkadima\b',
        r'\bzoran\b',
        r'\bpardes[- ]?hanna\b',
        r'\bkarkur\b',
        r'\bzichron[- ]?yaakov\b',
        r'\btirat[- ]?carmel\b',
        r'\bnesher\b',
        r'\bdaliyat[- ]?el[- ]?carmel\b',
        r'\bisfiya\b',
        r'\bshfaram\b',
        r'\bsachnin\b',
        r'\btamra\b',
        r'\bumm[- ]?el[- ]?fahm\b',
        r'\bbaqa[- ]?al[- ]?gharbiyye\b',
        r'\btayibe\b',
        r'\btira\b',
        r'\bqalansawe\b',
        r'\bkafr[- ]?qasim\b',
        r'\bjaffa\b',
        r'\byafo\b',
        r',\s*il\b',  # ", IL" suffix
        r'\bil,',  # "IL," prefix
        r'\btlv\b',  # TLV abbreviation
        r'\bisr[-]',  # ISR- prefix (like ISR-Tel Aviv)
    ]
    
    def __init__(self, allowed_countries: Optional[List[str]] = None):
        """
        Initialize the location filter service.
        
        Args:
            allowed_countries: List of allowed country names. 
                              Defaults to ["Israel"] if not provided.
        """
        self.allowed_countries = allowed_countries or ["Israel"]
        self._compiled_patterns: dict[str, List[re.Pattern]] = {}
        self._build_patterns()
    
    def _build_patterns(self):
        """Build compiled regex patterns for each allowed country."""
        for country in self.allowed_countries:
            if country.lower() == "israel":
                self._compiled_patterns["israel"] = [
                    re.compile(pattern, re.IGNORECASE) 
                    for pattern in self.ISRAEL_PATTERNS
                ]
            else:
                # For other countries, just match the country name
                self._compiled_patterns[country.lower()] = [
                    re.compile(rf'\b{re.escape(country)}\b', re.IGNORECASE)
                ]
    
    def is_location_allowed(self, location: Optional[str]) -> bool:
        """
        Check if a location matches any of the allowed countries.
        
        Args:
            location: The job location string to check.
            
        Returns:
            True if location matches an allowed country, False otherwise.
        """
        if not location:
            # If no location, we can't filter - let it through or reject
            # Being conservative: reject jobs without location
            return False
        
        location = location.strip()
        
        # Check against all patterns for all allowed countries
        for country, patterns in self._compiled_patterns.items():
            for pattern in patterns:
                if pattern.search(location):
                    return True
        
        return False
    
    def filter_jobs(self, jobs: List[dict], location_field: str = "location") -> tuple[List[dict], List[dict]]:
        """
        Filter a list of jobs, returning allowed and filtered-out jobs.
        
        Args:
            jobs: List of job dictionaries.
            location_field: The key in job dict containing location.
            
        Returns:
            Tuple of (allowed_jobs, filtered_out_jobs)
        """
        allowed = []
        filtered_out = []
        
        for job in jobs:
            location = job.get(location_field)
            if self.is_location_allowed(location):
                allowed.append(job)
            else:
                filtered_out.append(job)
                logger.debug(f"Filtered out job due to location: {job.get('title', 'Unknown')} - {location}")
        
        if filtered_out:
            logger.info(f"Location filter: {len(allowed)} allowed, {len(filtered_out)} filtered out")
        
        return allowed, filtered_out


# Singleton instance using settings
location_filter = LocationFilterService(allowed_countries=settings.allowed_countries_list)

