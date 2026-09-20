"""
BHU-SYNC Phase G: Workflow Case Management Service
Finite State Machine (FSM), case assignment, investigation notes, and evidence linking with automated audit logging.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from services.audit_service import append_audit_log

ALLOWED_TRANSITIONS = {
    "NEW": ["UNDER_INVESTIGATION", "REJECTED"],
    "UNDER_INVESTIGATION": ["PENDING_REVIEW", "REJECTED"],
    "PENDING_REVIEW": ["RESOLVED", "UNDER_INVESTIGATION", "REJECTED"],
    "RESOLVED": ["CLOSED"],
    "CLOSED": [],
    "REJECTED": []
}

# In-memory case repository for state transitions and demo workflows
CASES_STORE: Dict[str, Dict[str, Any]] = {
    "CASE-2024-001": {
        "case_id": "CASE-2024-001",
        "parcel_id": "DEMO-KPG-1004",
        "title": "Area Mismatch & Centroid Shift Investigation",
        "priority": "HIGH",
        "status": "UNDER_INVESTIGATION",
        "assigned_to": "officer@test.local",
        "organization_id": "org-revenue-pune",
        "created_at": "2024-03-01T10:00:00Z",
        "updated_at": "2024-03-02T11:30:00Z",
        "notes": [
            {
                "note_id": "NOTE-001",
                "author": "officer@test.local",
                "text": "Initial inspection shows municipal survey captured physical boundary fence which extends 150 sqm into adjacent plot.",
                "created_at": "2024-03-02T11:30:00Z"
            }
        ],
        "evidence": [
            {
                "evidence_id": "EVID-001",
                "title": "Site Inspection Field Survey 2024",
                "evidence_type": "SURVEY_MAP",
                "reference": "DOC-PUNE-REV-8891",
                "attached_by": "officer@test.local",
                "created_at": "2024-03-02T11:35:00Z"
            }
        ]
    },
    "CASE-2024-002": {
        "case_id": "CASE-2024-002",
        "parcel_id": "DEMO-KPG-1006",
        "title": "Owner Name Discrepancy Resolution",
        "priority": "MEDIUM",
        "status": "RESOLVED",
        "assigned_to": "officer@test.local",
        "organization_id": "org-revenue-pune",
        "created_at": "2024-02-15T09:00:00Z",
        "updated_at": "2024-02-20T16:00:00Z",
        "notes": [
            {
                "note_id": "NOTE-002",
                "author": "officer@test.local",
                "text": "Conveyance deed confirmed full legal name matches Vijay Shinde; municipal tax entry corrected.",
                "created_at": "2024-02-20T15:45:00Z"
            }
        ],
        "evidence": [
            {
                "evidence_id": "EVID-002",
                "title": "Registered Sale Deed #4521/2018",
                "evidence_type": "REGISTRY_DEED",
                "reference": "REG-MH-PUN-4521",
                "attached_by": "officer@test.local",
                "created_at": "2024-02-20T15:50:00Z"
            }
        ]
    }
}


def list_cases(
    status_filter: Optional[str] = None,
    assigned_to: Optional[str] = None,
    parcel_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    cases = list(CASES_STORE.values())
    if status_filter:
        cases = [c for c in cases if c.get("status") == status_filter]
    if assigned_to:
        cases = [c for c in cases if c.get("assigned_to") == assigned_to]
    if parcel_id:
        cases = [c for c in cases if c.get("parcel_id") == parcel_id]
    return sorted(cases, key=lambda x: str(x.get("updated_at", "")), reverse=True)


def get_case(case_id: str) -> Optional[Dict[str, Any]]:
    return CASES_STORE.get(case_id)


def create_case(
    parcel_id: str,
    title: str,
    priority: str,
    assigned_to: str,
    organization_id: str,
    actor_id: str,
    actor_email: str
) -> Dict[str, Any]:
    new_num = len(CASES_STORE) + 1
    case_id = f"CASE-{datetime.now(timezone.utc).year}-{new_num:03d}"
    now_iso = datetime.now(timezone.utc).isoformat()

    new_case = {
        "case_id": case_id,
        "parcel_id": parcel_id,
        "title": title,
        "priority": priority.upper(),
        "status": "NEW",
        "assigned_to": assigned_to,
        "organization_id": organization_id,
        "created_at": now_iso,
        "updated_at": now_iso,
        "notes": [],
        "evidence": []
    }
    CASES_STORE[case_id] = new_case

    # Audit log
    append_audit_log(
        actor_id=actor_id,
        actor_email=actor_email,
        action="CASE_CREATED",
        resource_type="WORKFLOW_CASE",
        resource_id=case_id,
        payload={"parcel_id": parcel_id, "title": title, "priority": priority}
    )

    return new_case


def transition_case_status(
    case_id: str,
    target_status: str,
    actor_id: str,
    actor_email: str,
    reason: Optional[str] = None
) -> Dict[str, Any]:
    """
    Applies Finite State Machine transitions. Raises ValueError on invalid state transition.
    """
    case = CASES_STORE.get(case_id)
    if not case:
        raise KeyError(f"Case '{case_id}' does not exist")

    current_status = case.get("status", "NEW")
    target_status = target_status.upper()

    allowed = ALLOWED_TRANSITIONS.get(current_status, [])
    if target_status not in allowed:
        raise ValueError(
            f"Invalid transition from '{current_status}' to '{target_status}'. Allowed target states: {allowed}"
        )

    now_iso = datetime.now(timezone.utc).isoformat()
    case["status"] = target_status
    case["updated_at"] = now_iso

    # Audit log
    append_audit_log(
        actor_id=actor_id,
        actor_email=actor_email,
        action="CASE_STATUS_TRANSITION",
        resource_type="WORKFLOW_CASE",
        resource_id=case_id,
        payload={
            "from_status": current_status,
            "to_status": target_status,
            "reason": reason
        }
    )

    return case


def add_case_note(
    case_id: str,
    note_text: str,
    actor_id: str,
    actor_email: str
) -> Dict[str, Any]:
    case = CASES_STORE.get(case_id)
    if not case:
        raise KeyError(f"Case '{case_id}' does not exist")

    note_id = f"NOTE-{len(case['notes']) + 1:03d}"
    now_iso = datetime.now(timezone.utc).isoformat()
    note_obj = {
        "note_id": note_id,
        "author": actor_email,
        "text": note_text,
        "created_at": now_iso
    }
    case["notes"].append(note_obj)
    case["updated_at"] = now_iso

    append_audit_log(
        actor_id=actor_id,
        actor_email=actor_email,
        action="CASE_NOTE_ADDED",
        resource_type="WORKFLOW_CASE",
        resource_id=case_id,
        payload={"note_id": note_id, "text_preview": note_text[:100]}
    )

    return note_obj


def link_case_evidence(
    case_id: str,
    title: str,
    evidence_type: str,
    reference: str,
    actor_id: str,
    actor_email: str
) -> Dict[str, Any]:
    case = CASES_STORE.get(case_id)
    if not case:
        raise KeyError(f"Case '{case_id}' does not exist")

    ev_id = f"EVID-{len(case['evidence']) + 1:03d}"
    now_iso = datetime.now(timezone.utc).isoformat()
    evidence_obj = {
        "evidence_id": ev_id,
        "title": title,
        "evidence_type": evidence_type.upper(),
        "reference": reference,
        "attached_by": actor_email,
        "created_at": now_iso
    }
    case["evidence"].append(evidence_obj)
    case["updated_at"] = now_iso

    append_audit_log(
        actor_id=actor_id,
        actor_email=actor_email,
        action="CASE_EVIDENCE_LINKED",
        resource_type="WORKFLOW_CASE",
        resource_id=case_id,
        payload={"evidence_id": ev_id, "evidence_type": evidence_type, "reference": reference}
    )

    return evidence_obj
