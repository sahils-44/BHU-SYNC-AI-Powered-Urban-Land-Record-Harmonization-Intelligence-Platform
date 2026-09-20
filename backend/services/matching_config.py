"""
BHU-SYNC Phase C: Centralized Matching Configuration & Weight Matrix
Defines source authorities, 7-level matching hierarchy, and score thresholds across 10 government sources.
"""

from typing import Dict, List, Any

# 10 Supported Government & Spatial Data Sources
SUPPORTED_SOURCES = [
    "CADASTRAL",           # Revenue / Land Records (7/12 extract)
    "MUNICIPAL",           # Municipal Corporation / Property Tax
    "REGISTRY",            # Sub-Registrar Office / Conveyance Deeds
    "SURVEY_OF_INDIA",     # National Cadastral Survey / Geodetic Control
    "UTILITY_WATER",       # Municipal Water Connection
    "UTILITY_ELECTRICITY", # State Power Distribution
    "BUILDING_PERMIT",     # Urban Development / Planning Authority
    "BANK_MORTGAGE",       # CERSAI / Banking Hypothecation
    "TAX_ASSESSMENT",      # Commercial / Stamp Duty Assessment
    "SATELLITE_IMAGERY"    # Drone / High-Res Optical Imagery Extraction
]

# Source Priority and Authority Weights (Sums to 1.0 per domain)
SOURCE_AUTHORITY = {
    "boundary": {
        "CADASTRAL": 0.45,
        "SURVEY_OF_INDIA": 0.35,
        "SATELLITE_IMAGERY": 0.20
    },
    "ownership": {
        "REGISTRY": 0.50,
        "CADASTRAL": 0.35,
        "MUNICIPAL": 0.15
    },
    "built_structure": {
        "MUNICIPAL": 0.45,
        "BUILDING_PERMIT": 0.35,
        "SATELLITE_IMAGERY": 0.20
    },
    "encumbrance": {
        "BANK_MORTGAGE": 0.60,
        "REGISTRY": 0.40
    },
    "utility_service": {
        "UTILITY_WATER": 0.50,
        "UTILITY_ELECTRICITY": 0.50
    }
}

# 7-Level Identity Resolution Hierarchy
MATCHING_HIERARCHY = [
    {"level": 1, "name": "ULPIN_EXACT", "weight": 1.00, "description": "Exact 14-digit ULPIN or Parcel ID match"},
    {"level": 2, "name": "OWNER_EXACT_VILLAGE", "weight": 0.95, "description": "Normalized owner name exact match with village/sub-district"},
    {"level": 3, "name": "OWNER_PHONETIC_FUZZY", "weight": 0.85, "description": "Phonetic Soundex/Metaphone with >0.85 Levenshtein similarity"},
    {"level": 4, "name": "SPATIAL_CENTROID_PROXIMITY", "weight": 0.85, "description": "Geographic centroid proximity within 10m-50m tolerance"},
    {"level": 5, "name": "POLYGON_IOU_OVERLAP", "weight": 0.90, "description": "Polygon intersection-over-union exceeding 50%-80%"},
    {"level": 6, "name": "SURVEY_KHASRA_HIERARCHY", "weight": 0.80, "description": "Survey number, Khasra, and Hissa sub-plot alignment"},
    {"level": 7, "name": "UTILITY_ADDRESS_CROSSREF", "weight": 0.75, "description": "Utility consumer number and normalized street address link"}
]

# Harmonization Classification Thresholds
SCORE_THRESHOLDS = {
    "HIGH_CONFIDENCE": 80.0,   # Score >= 80 -> Green, Harmonized
    "MODERATE_CONFIDENCE": 50.0 # Score 50-79 -> Yellow, Review Required
    # Score < 50 -> Red, Critical Conflict
}

# Dynamic Status Determination
def get_harmonization_status(score: float) -> str:
    if score >= SCORE_THRESHOLDS["HIGH_CONFIDENCE"]:
        return "harmonized"
    elif score >= SCORE_THRESHOLDS["MODERATE_CONFIDENCE"]:
        return "review_required"
    return "critical_conflict"


def get_status_color(score: float) -> str:
    """
    Returns hex color dynamically determined by database-backed harmonization score:
    - >= 80: Green (#22c55e)
    - 50-79: Yellow (#eab308)
    - < 50:  Red (#ef4444)
    """
    if score >= SCORE_THRESHOLDS["HIGH_CONFIDENCE"]:
        return "#22c55e"
    elif score >= SCORE_THRESHOLDS["MODERATE_CONFIDENCE"]:
        return "#eab308"
    return "#ef4444"
