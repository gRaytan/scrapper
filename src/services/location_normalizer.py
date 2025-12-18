"""Location normalization service for standardizing job location strings."""
import re
from typing import Optional, List, Tuple

# Canonical location names for Israel
# Format: (canonical_name, [aliases and patterns])
ISRAEL_LOCATIONS = [
    # Major cities
    ("Tel Aviv", [
        "tel aviv", "tel-aviv", "tlv", "tel aviv-yafo", "tel aviv yafo",
        "telaviv", "t.a.", "tel-aviv-yafo"
    ]),
    ("Haifa", ["haifa", "hefa"]),
    ("Jerusalem", ["jerusalem", "yerushalayim", "west jerusalem"]),
    ("Be'er Sheva", ["beer sheva", "be'er sheva", "beersheva", "beer-sheva"]),

    # Tel Aviv area
    ("Ramat Gan", ["ramat gan", "ramat-gan"]),
    ("Herzliya", ["herzliya", "herzlia", "herzeliya"]),
    ("Petah Tikva", ["petah tikva", "petach tikva", "petah-tikva", "petach-tikva"]),
    ("Ra'anana", ["raanana", "ra'anana", "ra'anana", "rannana"]),
    ("Holon", ["holon"]),
    ("Bnei Brak", ["bnei brak", "bnei-brak", "bney brak"]),
    ("Givatayim", ["givatayim", "givataim", "giv'atayim"]),
    ("Or Yehuda", ["or yehuda", "or-yehuda"]),
    ("Azor", ["azor"]),
    ("Kiryat Ono", ["kiryat ono", "qiryat ono"]),
    ("Ramat HaSharon", ["ramat hasharon", "ramat ha-sharon"]),
    ("Bat Yam", ["bat yam", "bat-yam"]),

    # Center
    ("Netanya", ["netanya", "netania"]),
    ("Rehovot", ["rehovot", "rechovot"]),
    ("Rishon LeZion", ["rishon lezion", "rishon le-zion", "rishon le zion"]),
    ("Kfar Saba", ["kfar saba", "kfar-saba"]),
    ("Rosh HaAyin", ["rosh haayin", "rosh ha'ayin", "rosh-haayin"]),
    ("Hod HaSharon", ["hod hasharon", "hod ha-sharon", "hod-hasharon"]),
    ("Modiin", ["modiin", "modi'in", "modiin-maccabim-reut"]),
    ("Lod", ["lod"]),
    ("Ramla", ["ramla", "ramle"]),
    ("Yavne", ["yavne"]),
    ("Beer Yaakov", ["beer yaakov", "be'er ya'akov"]),

    # North
    ("Yokneam", ["yokneam", "yoqneam", "yokneam ilit", "yoqneam illit"]),
    ("Migdal HaEmek", ["migdal haemek", "migdal ha'emek"]),
    ("Caesarea", ["caesarea", "cesarea", "qesarya"]),
    ("Tel Hai", ["tel hai", "tel-hai"]),
    ("Hadera", ["hadera"]),
    ("Afula", ["afula"]),
    ("Nazareth", ["nazareth", "natzeret", "nazerat"]),
    ("Karmiel", ["karmiel", "karmi'el"]),
    ("Nahariya", ["nahariya", "nahariyya"]),
    ("Akko", ["akko", "acre", "acco"]),
    ("Tiberias", ["tiberias", "tverya"]),
    ("Kiryat Shmona", ["kiryat shmona", "qiryat shemona"]),
    ("Gan HaShomron", ["gan hashomron"]),

    # South
    ("Ashdod", ["ashdod"]),
    ("Ashkelon", ["ashkelon"]),
    ("Eilat", ["eilat"]),
    ("Dimona", ["dimona"]),
    ("Arad", ["arad"]),
    ("Noam", ["noam"]),
    ("Sderot", ["sderot"]),

    # Jerusalem area
    ("Beit Shemesh", ["beit shemesh", "bet shemesh"]),
    ("Mevaseret Zion", ["mevaseret zion"]),
    ("Maaleh Adumim", ["maaleh adumim", "ma'ale adumim"]),
]

# Districts in Israel - maps to their main city (only when no specific city is found)
ISRAEL_DISTRICT_TO_CITY = {
    "tel aviv district": "Tel Aviv",
    "center district": None,  # No single city - too many options
    "central district": None,
    "haifa district": None,  # Don't default - could be Hadera, Caesarea, etc.
    "north district": None,
    "northern district": None,
    "south district": None,
    "southern district": None,
    "jerusalem district": None,  # Don't default - could be Beit Shemesh, etc.
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

