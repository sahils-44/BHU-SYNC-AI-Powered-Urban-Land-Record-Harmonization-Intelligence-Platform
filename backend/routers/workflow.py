"""
BHU-SYNC Phase G: Workflow Case Management Router
Handles dispute resolution lifecycle, FSM status transitions, investigation notes, and evidence linking.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, Query, status

from dependencies.auth import get_current_user, require_permission
from services.workflow_service import (
    list_cases,
    get_case,
    create_case,
    transition_case_status,
    add_case_note,
    link_case_evidence,
    CASES_STORE
)

router = APIRouter(
    prefix="/workflow",
    tags=["Workflow & Case Management"]
)


class CreateCaseRequest(BaseModel):
    parcel_id: str
    title: str
    priority: str = "MEDIUM"
    assigned_to: Optional[str] = None


class TransitionStatusRequest(BaseModel):
    status: str
    reason: Optional[str] = None


class AddNoteRequest(BaseModel):
    text: str


class LinkEvidenceRequest(BaseModel):
    title: str
    evidence_type: str
    reference: str


@router.get("/cases")
def get_all_cases(
    status: Optional[str] = Query(None),
    assigned_to: Optional[str] = Query(None),
    parcel_id: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """
    Returns list of workflow dispute and investigation cases.
    """
    cases = list_cases(status_filter=status, assigned_to=assigned_to, parcel_id=parcel_id)
    return {
        "success": True,
        "count": len(cases),
        "cases": cases
    }


@router.post("/cases")
def open_new_case(
    request: CreateCaseRequest,
    current_user: dict = Depends(require_permission("conflicts.update"))
):
    """
    Creates a new workflow investigation case for a parcel conflict.
    """
    assigned = request.assigned_to or current_user.get("email", "unassigned")
    org_id = current_user.get("organization_id", "default-org")
    case = create_case(
        parcel_id=request.parcel_id,
        title=request.title,
        priority=request.priority,
        assigned_to=assigned,
        organization_id=org_id,
        actor_id=current_user.get("id"),
        actor_email=current_user.get("email")
    )
    return {
        "success": True,
        "message": f"Case {case['case_id']} created successfully.",
        "case": case
    }


@router.get("/cases/{case_id}")
def get_case_details(
    case_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Retrieves full case details including audit trail, notes, and attached evidence.
    """
    case = get_case(case_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case '{case_id}' not found"
        )
    return {
        "success": True,
        "case": case
    }


@router.patch("/cases/{case_id}/status")
def update_case_status(
    case_id: str,
    request: TransitionStatusRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Executes a Finite State Machine state transition.
    Rejects invalid or unauthorized transitions with HTTP 400.
    """
    try:
        updated_case = transition_case_status(
            case_id=case_id,
            target_status=request.status,
            actor_id=current_user.get("id"),
            actor_email=current_user.get("email"),
            reason=request.reason
        )
        return {
            "success": True,
            "message": f"Case {case_id} transitioned to {request.status}.",
            "case": updated_case
        }
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/cases/{case_id}/notes")
def append_note(
    case_id: str,
    request: AddNoteRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Appends an officer investigation note to the case.
    """
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Note text cannot be empty")

    try:
        note = add_case_note(
            case_id=case_id,
            note_text=request.text,
            actor_id=current_user.get("id"),
            actor_email=current_user.get("email")
        )
        return {"success": True, "note": note}
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/cases/{case_id}/evidence")
def attach_evidence(
    case_id: str,
    request: LinkEvidenceRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Links verified documentation or survey proof to an investigation case.
    """
    try:
        evidence = link_case_evidence(
            case_id=case_id,
            title=request.title,
            evidence_type=request.evidence_type,
            reference=request.reference,
            actor_id=current_user.get("id"),
            actor_email=current_user.get("email")
        )
        return {"success": True, "evidence": evidence}
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/dashboard/stats")
def get_workflow_stats(current_user: dict = Depends(get_current_user)):
    """
    Returns workflow throughput and case backlog metrics.
    """
    cases = list(CASES_STORE.values())
    return {
        "success": True,
        "total_cases": len(cases),
        "new": sum(1 for c in cases if c.get("status") == "NEW"),
        "under_investigation": sum(1 for c in cases if c.get("status") == "UNDER_INVESTIGATION"),
        "pending_review": sum(1 for c in cases if c.get("status") == "PENDING_REVIEW"),
        "resolved": sum(1 for c in cases if c.get("status") == "RESOLVED"),
        "closed": sum(1 for c in cases if c.get("status") == "CLOSED")
    }
