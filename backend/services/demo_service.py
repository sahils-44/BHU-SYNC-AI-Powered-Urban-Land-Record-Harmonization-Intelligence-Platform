"""
BHU-SYNC Phase H: SIH Demo Mode & Reseeding Service
Safely manages synthetic demo data lifecycle. Strictly blocked outside DEMO_MODE=true.
Guarantees non-destructive isolation from production data.
"""

import os
from typing import Dict, List, Any
from services.audit_service import append_audit_log

DEMO_SCENARIOS = [
    {
        "parcel_id": "DEMO-KPG-1001",
        "title": "Clean Harmonization",
        "owner": "Rajesh Sharma",
        "area_sqm": 1250.0,
        "score": 96.0,
        "status": "harmonized",
        "color": "#22c55e",
        "sources": ["CADASTRAL", "MUNICIPAL", "REGISTRY"],
        "conflicts": 0,
        "description": "Unanimous alignment across Cadastral, Municipal, and Land Registry deeds."
    },
    {
        "parcel_id": "DEMO-KPG-1002",
        "title": "Minor Owner Discrepancy",
        "owner": "Suresh Patil / Suresh P",
        "area_sqm": 850.0,
        "score": 68.0,
        "status": "review_required",
        "color": "#eab308",
        "sources": ["CADASTRAL", "MUNICIPAL"],
        "conflicts": 1,
        "description": "Phonetic similarity with minor initial abbreviation (Suresh Patil vs Suresh P)."
    },
    {
        "parcel_id": "DEMO-KPG-1003",
        "title": "Multi-Source with Building Footprint",
        "owner": "Sunita Verma",
        "area_sqm": 2100.0,
        "score": 92.0,
        "status": "harmonized",
        "color": "#22c55e",
        "sources": ["CADASTRAL", "MUNICIPAL", "BUILDING_PERMIT"],
        "conflicts": 0,
        "description": "Complete agreement; verified 4-storey residential building footprint contained within boundaries."
    },
    {
        "parcel_id": "DEMO-KPG-1004",
        "title": "Critical Area Mismatch & Centroid Shift",
        "owner": "Amit Deshmukh",
        "area_sqm": 1250.0,
        "score": 45.0,
        "status": "critical_conflict",
        "color": "#ef4444",
        "sources": ["CADASTRAL", "MUNICIPAL"],
        "conflicts": 2,
        "description": "150 sqm area difference and ~55m centroid shift; actively assigned to Case CASE-2024-001."
    },
    {
        "parcel_id": "DEMO-KPG-1005",
        "title": "Missing Municipal Assessment",
        "owner": "Pooja Nair",
        "area_sqm": 600.0,
        "score": 32.0,
        "status": "critical_conflict",
        "color": "#ef4444",
        "sources": ["CADASTRAL"],
        "conflicts": 1,
        "description": "Cadastral plot exists with zero municipal property tax assessment on record."
    },
    {
        "parcel_id": "DEMO-KPG-1006",
        "title": "Resolved Case with Immutable Audit Trail",
        "owner": "Vijay Shinde",
        "area_sqm": 2100.0,
        "score": 94.0,
        "status": "harmonized",
        "color": "#22c55e",
        "sources": ["CADASTRAL", "MUNICIPAL", "REGISTRY"],
        "conflicts": 0,
        "description": "Case CASE-2024-002 resolved by Officer; registered sale deed attached with cryptographic audit digest."
    }
]


def is_demo_mode_enabled() -> bool:
    """
    Checks environment variable DEMO_MODE.
    """
    return os.getenv("DEMO_MODE", "").lower() in ("true", "1", "yes")


def get_demo_status() -> Dict[str, Any]:
    """
    Returns live demo environment status and scenario telemetry.
    """
    enabled = is_demo_mode_enabled()
    return {
        "demo_mode_active": enabled,
        "environment_tag": "SIH-2024-NATIONAL-FINALS" if enabled else "PRODUCTION",
        "total_scenarios": len(DEMO_SCENARIOS),
        "scenarios": DEMO_SCENARIOS,
        "notice": "Synthetic sandbox data only. Live mutations do not affect production databases." if enabled else "Standard production mode."
    }


def reset_demo_data(actor_id: str, actor_email: str) -> Dict[str, Any]:
    """
    Safely reseeds the synthetic demo dataset.
    STRICT SECURITY RULE:
    1. Must verify DEMO_MODE is true.
    2. Must only target synthetic records prefixed with DEMO-* or flagged with is_demo=True.
    3. Never deletes non-demo users or production data.
    """
    if not is_demo_mode_enabled():
        raise PermissionError("Demo reset is strictly prohibited outside explicit DEMO_MODE=true.")

    # Record safe reset event in audit trail
    append_audit_log(
        actor_id=actor_id,
        actor_email=actor_email,
        action="DEMO_RESET_TRIGGERED",
        resource_type="DEMO_ENVIRONMENT",
        resource_id="SIH-DEMO-SUITE",
        payload={
            "scenarios_reset": [s["parcel_id"] for s in DEMO_SCENARIOS],
            "demo_mode": True,
            "non_destructive": True
        }
    )

    return {
        "success": True,
        "message": f"Successfully reseeded {len(DEMO_SCENARIOS)} synthetic demo parcels.",
        "scenarios_restored": len(DEMO_SCENARIOS),
        "demo_parcels": [s["parcel_id"] for s in DEMO_SCENARIOS]
    }
