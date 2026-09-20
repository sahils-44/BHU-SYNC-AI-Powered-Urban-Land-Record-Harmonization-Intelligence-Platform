import os
import pandas as pd
from fastapi import APIRouter, HTTPException, Depends

from supabase_client import supabase
from dependencies.auth import require_permission


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)


@router.get("/stats")
def get_dashboard_stats(
    profile: dict = Depends(require_permission("dashboard.view"))
):
    try:
        # ---------------------------------------------------------
        # 1. Fetch Latest Analysis Run ID
        # ---------------------------------------------------------
        run_res = (
            supabase
            .table("analysis_runs")
            .select("id, completed_at, started_at, records_compared, conflicts_detected, harmonized_records_count")
            .eq("status", "completed")
            .order("started_at", desc=True)
            .limit(1)
            .execute()
        )
        latest_run = run_res.data[0] if run_res.data else None
        latest_run_id = latest_run["id"] if latest_run else None

        # ---------------------------------------------------------
        # 2. Harmonized records for Current Run (No historical mixing)
        # ---------------------------------------------------------
        if latest_run_id:
            harmonized_response = (
                supabase
                .table("harmonized_records")
                .select("parcel_id, harmonization_score, conflict_count")
                .eq("analysis_run_id", latest_run_id)
                .execute()
            )
        else:
            harmonized_response = (
                supabase
                .table("harmonized_records")
                .select("parcel_id, harmonization_score, conflict_count")
                .execute()
            )

        records = harmonized_response.data or []

        # Keep one record per parcel (deduplicate by parcel_id)
        unique_records = {}
        for record in records:
            parcel_id = record.get("parcel_id")
            if parcel_id:
                unique_records[parcel_id] = record

        harmonized_records = list(unique_records.values())

        # Total unique parcels in the current universe
        total_parcels = len(harmonized_records)

        # ---------------------------------------------------------
        # 3. Calculate harmonized vs review required
        # ---------------------------------------------------------
        harmonized = sum(
            1
            for record in harmonized_records
            if (
                float(record.get("harmonization_score") or 0) >= 80
                and int(record.get("conflict_count") or 0) == 0
            )
        )

        review_required = total_parcels - harmonized

        # ---------------------------------------------------------
        # 4. Average harmonization score
        # ---------------------------------------------------------
        average_score = (
            sum(
                float(record.get("harmonization_score") or 0)
                for record in harmonized_records
            ) / total_parcels
            if total_parcels > 0
            else 0
        )

        # ---------------------------------------------------------
        # 5. Active conflicts for Current Run
        # ---------------------------------------------------------
        if latest_run_id:
            conflicts_response = (
                supabase
                .table("conflicts")
                .select("id, parcel_id, conflict_type, severity, status")
                .eq("analysis_run_id", latest_run_id)
                .eq("status", "open")
                .execute()
            )
        else:
            conflicts_response = (
                supabase
                .table("conflicts")
                .select("id, parcel_id, conflict_type, severity, status")
                .eq("status", "open")
                .execute()
            )

        conflicts_data = conflicts_response.data or []
        active_conflicts = len(conflicts_data)

        # High priority conflicts
        high_priority = sum(
            1
            for c in conflicts_data
            if str(c.get("severity") or "").upper() == "HIGH"
        )

        # Unique parcels with conflicts
        conflict_parcel_ids = set(
            c.get("parcel_id")
            for c in conflicts_data
            if c.get("parcel_id")
        )
        unique_conflict_parcels = len(conflict_parcel_ids)
        if unique_conflict_parcels == 0 and total_parcels > 0:
            unique_conflict_parcels = sum(
                1
                for r in harmonized_records
                if int(r.get("conflict_count") or 0) > 0
            )

        # Conflict breakdown counts by category
        owner_mismatch = 0
        area_mismatch = 0
        location_mismatch = 0
        missing_parcel = 0

        for c in conflicts_data:
            ctype = str(c.get("conflict_type") or "").upper()
            if "OWNER" in ctype:
                owner_mismatch += 1
            elif "AREA" in ctype:
                area_mismatch += 1
            elif "LOCATION" in ctype:
                location_mismatch += 1
            elif "MISSING" in ctype:
                missing_parcel += 1

        # Score distribution buckets for latest analysis run
        score_distribution = {
            "80_100": sum(
                1
                for r in harmonized_records
                if float(r.get("harmonization_score") or 0) >= 80
            ),
            "60_79": sum(
                1
                for r in harmonized_records
                if 60 <= float(r.get("harmonization_score") or 0) < 80
            ),
            "0_59": sum(
                1
                for r in harmonized_records
                if float(r.get("harmonization_score") or 0) < 60
            ),
        }

        return {
            "success": True,
            "run_id": latest_run_id,
            "total_parcels": total_parcels,
            "harmonized": harmonized,
            "review_required": review_required,
            "active_conflicts": active_conflicts,
            "unique_conflict_parcels": unique_conflict_parcels,
            "high_priority": high_priority,
            "average_score": round(average_score, 1),
            "score_distribution": score_distribution,
            "conflict_breakdown": {
                "owner_mismatch": owner_mismatch,
                "area_mismatch": area_mismatch,
                "location_mismatch": location_mismatch,
                "missing_parcel": missing_parcel,
                "total": active_conflicts,
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.get("/source-comparison")
def get_source_comparison(
    profile: dict = Depends(require_permission("dashboard.view"))
):
    try:
        # ---------------------------------------------------------
        # Query real database source records from Supabase
        # ---------------------------------------------------------
        cad_res = (
            supabase
            .table("source_records")
            .select("parcel_id, owner_name, area, ward, latitude, longitude")
            .eq("source_type", "CADASTRAL")
            .order("created_at", desc=True)
            .execute()
        )

        mun_res = (
            supabase
            .table("source_records")
            .select("parcel_id, owner_name, area, ward, latitude, longitude")
            .eq("source_type", "MUNICIPAL")
            .order("created_at", desc=True)
            .execute()
        )

        cadastral_records = cad_res.data or []
        municipal_records = mun_res.data or []

        # Fallback to local sample files if database has not been seeded yet
        if not cadastral_records and os.path.exists("data/cadastral.csv"):
            cad_df = pd.read_csv("data/cadastral.csv")
            for _, row in cad_df.iterrows():
                cadastral_records.append(row.to_dict())

        if not municipal_records and os.path.exists("data/municipal.csv"):
            mun_df = pd.read_csv("data/municipal.csv")
            for _, row in mun_df.iterrows():
                municipal_records.append(row.to_dict())

        # Create parcel maps
        cadastral_map = {}
        for record in cadastral_records:
            pid = str(record.get("parcel_id") or "").strip()
            if pid and pid not in cadastral_map:
                cadastral_map[pid] = record

        municipal_map = {}
        for record in municipal_records:
            pid = str(record.get("parcel_id") or "").strip()
            if pid and pid not in municipal_map:
                municipal_map[pid] = record

        cadastral_ids = set(cadastral_map.keys())
        municipal_ids = set(municipal_map.keys())

        matched_ids = cadastral_ids & municipal_ids
        only_cadastral = cadastral_ids - municipal_ids
        only_municipal = municipal_ids - cadastral_ids

        # Attribute agreement
        owner_matches = 0
        area_matches = 0
        location_matches = 0

        for parcel_id in matched_ids:
            c = cadastral_map[parcel_id]
            m = municipal_map[parcel_id]

            # Owner
            c_owner = str(c.get("owner_name") or "").strip().lower()
            m_owner = str(m.get("owner_name") or "").strip().lower()
            if c_owner and m_owner and c_owner == m_owner:
                owner_matches += 1

            # Area
            try:
                c_area = float(c.get("area"))
                m_area = float(m.get("area"))
                if abs(c_area - m_area) <= 0.01:
                    area_matches += 1
            except (TypeError, ValueError):
                pass

            # Location
            try:
                c_lat = float(c.get("latitude"))
                c_lon = float(c.get("longitude"))
                m_lat = float(m.get("latitude"))
                m_lon = float(m.get("longitude"))
                if (
                    abs(c_lat - m_lat) < 0.0001
                    and abs(c_lon - m_lon) < 0.0001
                ):
                    location_matches += 1
            except (TypeError, ValueError):
                pass

        return {
            "success": True,
            "cadastral": len(cadastral_map),
            "municipal": len(municipal_map),
            "cadastral_count": len(cadastral_map),
            "municipal_count": len(municipal_map),
            "matched": len(matched_ids),
            "only_cadastral": len(only_cadastral),
            "only_municipal": len(only_municipal),
            "owner_matches": owner_matches,
            "area_matches": area_matches,
            "location_matches": location_matches
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.get("/latest-analysis")
def get_latest_analysis(
    profile: dict = Depends(require_permission("dashboard.view"))
):
    try:
        stats = get_dashboard_stats(profile=profile)

        # Query latest analysis run
        run_res = (
            supabase
            .table("analysis_runs")
            .select("*")
            .eq("status", "completed")
            .order("started_at", desc=True)
            .limit(1)
            .execute()
        )
        run = run_res.data[0] if run_res.data else None

        cad_version_label = "Cadastral V1"
        mun_version_label = "Municipal V1"
        completed_at = "Latest Run"

        if run:
            completed_at = run.get("completed_at") or run.get("started_at") or "Latest Run"
            
            # Fetch version labels
            if run.get("cadastral_version_id"):
                v_res = supabase.table("dataset_versions").select("version_number").eq("id", run["cadastral_version_id"]).execute()
                if v_res.data:
                    cad_version_label = f"Cadastral V{v_res.data[0]['version_number']}"

            if run.get("municipal_version_id"):
                v_res = supabase.table("dataset_versions").select("version_number").eq("id", run["municipal_version_id"]).execute()
                if v_res.data:
                    mun_version_label = f"Municipal V{v_res.data[0]['version_number']}"

        return {
            "success": True,
            "run_id": run.get("id") if run else None,
            "analysis_run_id": run.get("id") if run else None,
            "cadastral_version": cad_version_label,
            "municipal_version": mun_version_label,
            "parcels_compared": stats["total_parcels"],
            "harmonized": stats["harmonized"],
            "review_required": stats["review_required"],
            "average_score": stats["average_score"],
            "active_conflicts": stats["active_conflicts"],
            "status": run.get("status", "completed") if run else "completed",
            "completed_at": completed_at
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )