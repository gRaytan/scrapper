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

    Rules:
    1. If a known city is found -> "City, Israel"
    2. If no city but has district -> "District, Israel" (keep district)
    3. If just "Israel" with no city/district -> "Israel"
    4. Always add ", Israel" suffix for Israeli locations

    Examples:
        "Tel Aviv-Yafo, Tel Aviv District, Israel" -> "Tel Aviv, Israel"
        "TLV" -> "Tel Aviv, Israel"
        "Herzliya, Tel Aviv District, Israel" -> "Herzliya, Israel"
        "Center District, Israel" -> "Center District, Israel" (no city, keep district)
        "Beit Shean, North District, Israel" -> "Beit Shean, Israel" (unknown city, keep name)

    Args:
        location: Raw location string

    Returns:
        Normalized location string
    """
    if not location:
        return ""

    original = location
    location = location.strip()

    # Check if this is an Israeli location
    # Note: \bIL\b alone is ambiguous (could be Illinois), so only match if:
    # - "Israel" is explicitly mentioned, OR
    # - "IL" appears with comma before it (e.g., "Tel Aviv, IL") but NOT "Chicago, IL, USA"
    is_israel = bool(re.search(r'\bisrael\b', location, re.IGNORECASE))
    if not is_israel:
        # Check for ", IL" pattern but exclude if USA/US is also present
        if re.search(r',\s*IL\b', location) and not re.search(r'\bUSA?\b', location, re.IGNORECASE):
            is_israel = True

    # Handle "Remote" locations
    if re.search(r'\bremote\b', location, re.IGNORECASE):
        if is_israel:
            return "Remote, Israel"
        if re.search(r'\bunited states\b', location, re.IGNORECASE):
            return "Remote, United States"
        return "Remote"

    # Check for known Israeli cities first
    cities_found = extract_cities(location)
    if cities_found:
        # Found a known Israeli city - always add ", Israel"
        return f"{cities_found[0]}, Israel"

    # No known city found - check if it's an Israeli location
    if is_israel:
        location_lower = location.lower()

        # Check if there's a city name we don't recognize (before the district/country)
        # Pattern: "CityName, District, Israel" or "CityName, Israel"
        city_match = re.match(r'^([A-Za-z\s\-\']+?)(?:,\s*(?:Center|North|South|Haifa|Jerusalem|Tel Aviv)?\s*District|,\s*Israel)', location, re.IGNORECASE)
        if city_match:
            city_name = city_match.group(1).strip()
            # Clean up the city name
            city_name = re.sub(r'\s+', ' ', city_name)
            # Exclude district names and country names
            excluded = ['israel', 'il', 'center', 'north', 'south', 'haifa', 'jerusalem', 'tel aviv']
            if city_name.lower() not in excluded and len(city_name) > 1:
                return f"{city_name}, Israel"

        # No city found - check for district and keep it
        for district in ISRAEL_DISTRICTS:
            if district in location_lower:
                # Format nicely: "Center District, Israel"
                district_name = district.title()
                return f"{district_name}, Israel"

        # Just "Israel" with no specific location
        return "Israel"

    # Not Israeli - return cleaned version
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

