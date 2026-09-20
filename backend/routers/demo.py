"""
BHU-SYNC Phase H: SIH Demo Mode Router
Provides endpoints for querying demo mode status and safely triggering non-destructive demo reset.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from dependencies.auth import get_current_user, require_permission
from services.demo_service import get_demo_status, reset_demo_data, is_demo_mode_enabled

router = APIRouter(
    prefix="/demo",
    tags=["SIH Demo Mode"]
)


@router.get("/status")
def check_demo_status(current_user: dict = Depends(get_current_user)):
    """
    Returns current SIH demo mode configuration, active synthetic scenarios, and isolation status.
    """
    return {
        "success": True,
        **get_demo_status()
    }


@router.post("/reset")
def trigger_demo_reset(
    current_user: dict = Depends(require_permission("datasets.upload"))
):
    """
    Safely resets synthetic demo data back to clean demonstration baseline.
    Strictly blocked outside explicit DEMO_MODE=true.
    """
    if not is_demo_mode_enabled():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demo reset is disabled in non-demo environment."
        )

    try:
        result = reset_demo_data(
            actor_id=current_user.get("id", "00000000-0000-0000-0000-000000000000"),
            actor_email=current_user.get("email", "officer@test.local")
        )
        return result
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
