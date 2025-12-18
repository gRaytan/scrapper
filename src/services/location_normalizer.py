"""Location normalization service for standardizing job location strings."""
import re
from typing import Optional, List, Tuple

# Canonical location names for Israel
# Format: (canonical_name, [aliases and patterns])
ISRAEL_LOCATIONS = [
    ("Tel Aviv", [
        "tel aviv", "tel-aviv", "tlv", "tel aviv-yafo", "tel aviv yafo",
        "telaviv", "t.a.", "ta ", "tel-aviv-yafo"
    ]),
    ("Ramat Gan", ["ramat gan", "ramat-gan"]),
    ("Herzliya", ["herzliya", "herzlia", "herzeliya"]),
    ("Petah Tikva", ["petah tikva", "petach tikva", "petah-tikva", "petach-tikva"]),
    ("Netanya", ["netanya", "netania"]),
    ("Ra'anana", ["raanana", "ra'anana", "ra'anana", "rannana"]),
    ("Haifa", ["haifa", "hefa"]),
    ("Jerusalem", ["jerusalem", "yerushalayim", "west jerusalem"]),
    ("Be'er Sheva", ["beer sheva", "be'er sheva", "beersheva", "beer-sheva"]),
    ("Rehovot", ["rehovot", "rechovot"]),
    ("Rishon LeZion", ["rishon lezion", "rishon le-zion", "rishon le zion"]),
    ("Kfar Saba", ["kfar saba", "kfar-saba"]),
    ("Holon", ["holon"]),
    ("Bnei Brak", ["bnei brak", "bnei-brak", "bney brak"]),
    ("Givatayim", ["givatayim", "givataim", "giv'atayim"]),
    ("Yokneam", ["yokneam", "yoqneam", "yokneam ilit", "yoqneam illit"]),
    ("Rosh HaAyin", ["rosh haayin", "rosh ha'ayin", "rosh-haayin"]),
    ("Hod HaSharon", ["hod hasharon", "hod ha-sharon", "hod-hasharon"]),
    ("Modiin", ["modiin", "modi'in", "modiin-maccabim-reut"]),
    ("Caesarea", ["caesarea", "cesarea", "qesarya"]),
    ("Migdal HaEmek", ["migdal haemek", "migdal ha'emek"]),
    ("Or Yehuda", ["or yehuda", "or-yehuda"]),
    ("Azor", ["azor"]),
    ("Kiryat Ono", ["kiryat ono", "qiryat ono"]),
    ("Ramat HaSharon", ["ramat hasharon", "ramat ha-sharon"]),
    ("Noam", ["noam"]),
    ("Tel Hai", ["tel hai", "tel-hai"]),
]

# Districts in Israel - maps to their main city
ISRAEL_DISTRICT_TO_CITY = {
    "tel aviv district": "Tel Aviv",
    "center district": None,  # No single city
    "central district": None,
    "haifa district": "Haifa",
    "north district": None,
    "northern district": None,
    "south district": None,
    "southern district": None,
    "jerusalem district": "Jerusalem",
    "gush dan": "Tel Aviv",
}

# Districts list for removal
ISRAEL_DISTRICTS = list(ISRAEL_DISTRICT_TO_CITY.keys())

# Country patterns
COUNTRY_PATTERNS = [
    (r"\bisrael\b", "Israel"),
    (r"\bil\b", "Israel"),
    (r"\bisr\b", "Israel"),
]


def normalize_location(location: str) -> str:
    """
    Normalize a location string to a canonical format.
    
    Examples:
        "Tel Aviv-Yafo, Tel Aviv District, Israel" -> "Tel Aviv, Israel"
        "TLV" -> "Tel Aviv, Israel"
        "Herzliya, Tel Aviv District, Israel" -> "Herzliya, Israel"
        "Israel, Tel Aviv, Israel, Yokneam" -> "Tel Aviv, Israel"  (takes first city)
    
    Args:
        location: Raw location string
        
    Returns:
        Normalized location string
    """
    if not location:
        return ""
    
    original = location
    location = location.strip()
    
    # Handle "Remote" locations
    if re.search(r'\bremote\b', location, re.IGNORECASE):
        # Check if it's remote with a country
        if re.search(r'\bisrael\b', location, re.IGNORECASE):
            return "Remote, Israel"
        if re.search(r'\bunited states\b', location, re.IGNORECASE):
            return "Remote, United States"
        return "Remote"
    
    # Handle multi-location strings (e.g., "Israel, Tel Aviv, Israel, Yokneam")
    # Take the first recognizable city
    cities_found = extract_cities(location)
    if cities_found:
        primary_city = cities_found[0]
        # Check if Israel is mentioned
        if re.search(r'\bisrael\b|\bil\b', location, re.IGNORECASE):
            return f"{primary_city}, Israel"
        return primary_city

    # If no city found, check for district names that map to a city
    location_lower = location.lower()
    for district, city in ISRAEL_DISTRICT_TO_CITY.items():
        if district in location_lower and city:
            if re.search(r'\bisrael\b', location, re.IGNORECASE):
                return f"{city}, Israel"
            return city

    # If no city found, check for just country
    if re.search(r'\bisrael\b', location, re.IGNORECASE):
        return "Israel"
    
    # Return cleaned version of original if no normalization possible
    return clean_location_string(location)


def extract_cities(location: str) -> List[str]:
    """Extract all recognized cities from a location string."""
    # First, remove district names to avoid false matches
    location_cleaned = location.lower()
    for district in ISRAEL_DISTRICTS:
        location_cleaned = location_cleaned.replace(district, " ")

    cities = []

    # Sort by alias length (longest first) to match more specific names first
    sorted_locations = sorted(
        ISRAEL_LOCATIONS,
        key=lambda x: max(len(a) for a in x[1]),
        reverse=True
    )

    for canonical, aliases in sorted_locations:
        for alias in sorted(aliases, key=len, reverse=True):
            # Use word boundary matching for short aliases
            if len(alias) <= 3:
                pattern = rf'\b{re.escape(alias)}\b'
                if re.search(pattern, location_cleaned):
                    if canonical not in cities:
                        cities.append(canonical)
                    break
            elif alias in location_cleaned:
                if canonical not in cities:
                    cities.append(canonical)
                break

    return cities


def clean_location_string(location: str) -> str:
    """Clean up a location string by removing districts and extra formatting."""
    result = location
    
    # Remove district names
    for district in ISRAEL_DISTRICTS:
        result = re.sub(rf',?\s*{re.escape(district)}', '', result, flags=re.IGNORECASE)
    
    # Clean up multiple commas and spaces
    result = re.sub(r',\s*,', ',', result)
    result = re.sub(r'\s+', ' ', result)
    result = re.sub(r',\s*$', '', result)
    result = re.sub(r'^\s*,', '', result)
    
    return result.strip()


def normalize_location_for_matching(location: str) -> str:
    """
    Get a simplified location for matching purposes.
    Returns just the city name without country.
    """
    normalized = normalize_location(location)
    # Remove ", Israel" suffix for matching
    return re.sub(r',\s*Israel$', '', normalized, flags=re.IGNORECASE).strip()

