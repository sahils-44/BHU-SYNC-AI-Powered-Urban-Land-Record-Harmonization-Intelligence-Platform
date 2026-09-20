"""
BHU-SYNC Phase G: Tamper-Evident SHA-256 Audit Router
Exposes read-only append-verified audit logs and cryptographic chain verification.
No mutating (PUT/PATCH/DELETE) endpoints exist on this router.
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status

from dependencies.auth import get_current_user, require_permission
from services.audit_service import get_audit_logs, verify_chain_integrity

router = APIRouter(
    prefix="/audit",
    tags=["Audit & Compliance"]
)


@router.get("/logs")
def fetch_audit_logs(
    limit: int = Query(100, ge=1, le=500),
    resource_id: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """
    Returns verified append-only audit trail. Paginated and strictly read-only.
    """
    logs = get_audit_logs(limit=limit, resource_id=resource_id, action=action)
    return {
        "success": True,
        "count": len(logs),
        "logs": logs
    }


@router.get("/verify-chain")
def verify_hash_chain(current_user: dict = Depends(get_current_user)):
    """
    Cryptographically verifies SHA-256 hash chaining from the Genesis block to the latest entry.
    """
    is_valid, verified_count, message = verify_chain_integrity()
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Audit chain verification failed: {message}"
        )

    return {
        "success": True,
        "is_tamper_free": True,
        "verified_entries": verified_count,
        "algorithm": "SHA-256 Chained Digest",
        "message": message
    }
