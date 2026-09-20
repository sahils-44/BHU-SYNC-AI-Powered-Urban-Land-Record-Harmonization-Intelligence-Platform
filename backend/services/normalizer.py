"""
BHU-SYNC Phase C: Normalizer Service
Provides multi-lingual honorific removal, phonetic Soundex, area unit conversion, and coordinate parsing.
"""

import re
from typing import Optional, Tuple, Any

HONORIFICS = {
    "mr", "mrs", "ms", "shri", "shree", "smt", "shrimati", "dr", "late",
    "advocate", "adv", "m/s", "prop", "proprietor", "kumar", "kumari"
}

AREA_CONVERSION_FACTORS = {
    "sqm": 1.0,
    "sq_meters": 1.0,
    "sqm.": 1.0,
    "sqft": 0.092903,
    "sq_ft": 0.092903,
    "square_feet": 0.092903,
    "sq_yards": 0.836127,
    "gaj": 0.836127,
    "guntha": 101.171,
    "gunthe": 101.171,
    "bigha": 2529.28,
    "acre": 4046.86,
    "acres": 4046.86,
    "hectare": 10000.0,
    "hectares": 10000.0
}


def normalize_owner_name_advanced(name: Optional[str]) -> str:
    """
    Cleans owner name, removes honorifics, removes non-alphabetic noise, collapses spaces.
    """
    if not name:
        return ""

    # Convert to lowercase string
    cleaned = str(name).lower().strip()

    # Remove special characters except spaces
    cleaned = re.sub(r"[^\w\s]", " ", cleaned)

    # Tokenize and filter honorifics
    tokens = cleaned.split()
    filtered = [t for t in tokens if t not in HONORIFICS and len(t) > 0]

    return " ".join(filtered)


def calculate_soundex(text: str) -> str:
    """
    Calculates American Soundex code for phonetic matching of Indian and English names.
    """
    text = text.upper()
    text = re.sub(r"[^A-Z]", "", text)
    if not text:
        return "0000"

    first_letter = text[0]
    mappings = {
        "BFPV": "1",
        "CGJKQSXZ": "2",
        "DT": "3",
        "L": "4",
        "MN": "5",
        "R": "6"
    }

    code = first_letter
    prev_digit = ""
    for char in text[1:]:
        digit = ""
        for letters, num in mappings.items():
            if char in letters:
                digit = num
                break
        if digit and digit != prev_digit:
            code += digit
            prev_digit = digit
        elif not digit:
            prev_digit = ""

    code = (code + "0000")[:4]
    return code


def string_similarity(s1: str, s2: str) -> float:
    """
    Computes token-based Jaccard similarity and character bigram similarity between two names.
    """
    if not s1 or not s2:
        return 0.0
    if s1 == s2:
        return 1.0

    tokens1 = set(s1.split())
    tokens2 = set(s2.split())

    intersection = len(tokens1.intersection(tokens2))
    union = len(tokens1.union(tokens2))
    token_score = intersection / union if union > 0 else 0.0

    # Bigram character similarity
    def get_bigrams(s):
        return {s[i:i+2] for i in range(len(s) - 1)}

    bg1 = get_bigrams(s1)
    bg2 = get_bigrams(s2)
    if bg1 and bg2:
        char_score = 2.0 * len(bg1.intersection(bg2)) / (len(bg1) + len(bg2))
    else:
        char_score = 0.0

    return round(max(token_score, char_score), 4)


def convert_area_to_sqm(value: float, unit: str = "sqm") -> float:
    """
    Converts various land record measurement units into standardized square meters (sqm).
    """
    unit_clean = unit.lower().strip().replace(" ", "_")
    factor = AREA_CONVERSION_FACTORS.get(unit_clean, 1.0)
    return round(value * factor, 2)


def parse_coordinates(lat_str: Any, lng_str: Any) -> Tuple[Optional[float], Optional[float]]:
    """
    Safely parses and validates geographic latitude and longitude.
    """
    try:
        lat = float(lat_str) if lat_str is not None else None
        lng = float(lng_str) if lng_str is not None else None
        if lat is not None and lng is not None:
            if -90.0 <= lat <= 90.0 and -180.0 <= lng <= 180.0:
                return lat, lng
    except (ValueError, TypeError):
        pass
    return None, None
