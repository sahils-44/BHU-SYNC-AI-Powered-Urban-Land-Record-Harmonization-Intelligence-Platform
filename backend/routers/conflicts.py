from typing import Optional, Dict, Any
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Query, Depends

from supabase_client import supabase
from dependencies.auth import require_permission


router = APIRouter(
    prefix="/conflicts",
    tags=["Conflicts"]
)


class UpdateConflictRequest(BaseModel):
    status: Optional[str] = "resolved"
    resolution_notes: Optional[str] = None


@router.get("/")
def get_conflicts(
    run_id: Optional[str] = Query(None, description="Optional analysis run ID filter"),
    profile: dict = Depends(require_permission("conflicts.view"))
):
    try:
        active_run_id = run_id
        if not active_run_id:
            run_res = (
                supabase
                .table("analysis_runs")
                .select("id")
                .eq("status", "completed")
                .order("started_at", desc=True)
                .limit(1)
                .execute()
            )
            if run_res.data and len(run_res.data) > 0:
                active_run_id = run_res.data[0]["id"]

        query = (
            supabase
            .table("conflicts")
            .select("*")
            .order("created_at", desc=True)
        )
        if active_run_id:
            query = query.eq("analysis_run_id", active_run_id)

        response = query.execute()

        return {
            "success": True,
            "run_id": active_run_id,
            "count": len(response.data or []),
            "conflicts": response.data or []
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.patch("/{conflict_id}")
def update_conflict(
    conflict_id: str,
    request: UpdateConflictRequest,
    profile: dict = Depends(require_permission("conflicts.update"))
):
    try:
        update_data = {"status": request.status}
        if request.resolution_notes:
            update_data["resolution_notes"] = request.resolution_notes

        res = (
            supabase
            .table("conflicts")
            .update(update_data)
            .eq("id", conflict_id)
            .execute()
        )
        return {
            "success": True,
            "conflict_id": conflict_id,
            "status": request.status,
            "data": res.data or []
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )