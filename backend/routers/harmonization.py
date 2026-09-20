from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Depends

from supabase_client import supabase
from dependencies.auth import require_permission


router = APIRouter(
    prefix="/harmonization",
    tags=["Harmonization"]
)


@router.get("/")
def get_harmonization(
    run_id: Optional[str] = Query(None, description="Optional analysis run ID filter"),
    profile: dict = Depends(require_permission("harmonization.view"))
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
            .table("harmonized_records")
            .select("*")
            .order(
                "harmonization_score",
                desc=True
            )
        )
        if active_run_id:
            query = query.eq("analysis_run_id", active_run_id)

        response = query.execute()

        return {
            "success": True,
            "run_id": active_run_id,
            "count": len(response.data or []),
            "records": response.data or []
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.post("/run")
def run_harmonization(
    profile: dict = Depends(require_permission("harmonization.run"))
):
    """
    Trigger harmonization pipeline execution.
    """
    # Import analysis runner lazily to avoid circular imports
    from routers.analysis import run_analysis
    return run_analysis(request=None, profile=profile)