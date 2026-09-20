import os
import uuid
from datetime import datetime, timezone
from typing import Optional

import pandas as pd
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from services.cleaner import clean_dataset
from services.matcher import harmonize
from services.conflict_engine import detect_conflicts
from services.harmonization_service import build_harmonized_records
from supabase_client import supabase
from dependencies.auth import require_permission


router = APIRouter(
    prefix="/analysis",
    tags=["Analysis"]
)


class RunAnalysisRequest(BaseModel):
    cadastral_version_id: Optional[str] = None
    municipal_version_id: Optional[str] = None


class CompareRunsRequest(BaseModel):
    from_run_id: Optional[str] = None
    to_run_id: Optional[str] = None


def clean_for_json(value):
    """
    Convert pandas/NumPy values that are not JSON-safe
    into native Python values.
    """
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass
    return value


def clean_record(record):
    """
    Convert every value in a dictionary into a JSON-safe value.
    """
    return {
        key: clean_for_json(value)
        for key, value in record.items()
    }


def seed_records_from_csv_if_empty(source_type: str, filename: str):
    """
    If no source_records exist for this source_type in Supabase,
    safely ingest from local sample CSV so the system is immediately usable.
    """
    try:
        existing = (
            supabase
            .table("source_records")
            .select("id")
            .eq("source_type", source_type)
            .limit(1)
            .execute()
        )
        if existing.data:
            return

        if not os.path.exists(filename):
            return

        df = pd.read_csv(filename)
        cleaned_df = clean_dataset(df)

        base_name = os.path.splitext(os.path.basename(filename))[0].lower()

        # Find or create dataset
        ds_res = (
            supabase
            .table("datasets")
            .select("*")
            .eq("name", base_name)
            .eq("source_type", source_type)
            .execute()
        )
        if ds_res.data:
            dataset_id = ds_res.data[0]["id"]
        else:
            new_ds = supabase.table("datasets").insert({
                "name": base_name,
                "source_type": source_type,
                "file_name": os.path.basename(filename),
                "record_count": len(cleaned_df),
                "quality_score": 100.0,
                "status": "processed"
            }).execute()
            dataset_id = new_ds.data[0]["id"]

        # Create version 1
        v_res = supabase.table("dataset_versions").insert({
            "dataset_id": dataset_id,
            "version_number": 1,
            "record_count": len(cleaned_df),
            "quality_score": 100.0,
            "status": "processed"
        }).execute()
        version_id = v_res.data[0]["id"]

        # Insert source records
        records = []
        for idx, row in cleaned_df.iterrows():
            raw_row = df.iloc[idx].to_dict() if idx < len(df) else row.to_dict()
            records.append({
                "dataset_id": dataset_id,
                "version_id": version_id,
                "source_type": source_type,
                "parcel_id": clean_for_json(row.get("parcel_id")),
                "owner_name": clean_for_json(row.get("owner_name")),
                "area": clean_for_json(row.get("area")),
                "ward": clean_for_json(row.get("ward")),
                "latitude": clean_for_json(row.get("latitude")),
                "longitude": clean_for_json(row.get("longitude")),
                "raw_data": clean_record(raw_row)
            })

        for i in range(0, len(records), 100):
            supabase.table("source_records").insert(records[i:i + 100]).execute()

    except Exception as e:
        print(f"Notice: automatic seed for {source_type} skipped: {e}")


# =========================================
# POST /analysis/run
# Database-driven, non-destructive harmonization run
# =========================================

@router.post("/run")
def run_analysis(
    request: Optional[RunAnalysisRequest] = None,
    profile: dict = Depends(require_permission("analysis.run"))
):
    try:
        started_at = datetime.now(timezone.utc).isoformat()
        cad_ver_id = request.cadastral_version_id if request else None
        mun_ver_id = request.municipal_version_id if request else None

        # -------------------------------------------------------------
        # 1. Ensure source data exists (auto-seed from sample CSVs if empty)
        # -------------------------------------------------------------
        seed_records_from_csv_if_empty("CADASTRAL", "data/cadastral.csv")
        seed_records_from_csv_if_empty("MUNICIPAL", "data/municipal.csv")

        # -------------------------------------------------------------
        # 2. Resolve Cadastral & Municipal source versions from Supabase
        # -------------------------------------------------------------
        if cad_ver_id:
            cad_src_res = (
                supabase
                .table("source_records")
                .select("*")
                .eq("version_id", cad_ver_id)
                .execute()
            )
        else:
            # Query latest cadastral source records
            cad_src_res = (
                supabase
                .table("source_records")
                .select("*")
                .eq("source_type", "CADASTRAL")
                .order("created_at", desc=True)
                .execute()
            )

        if mun_ver_id:
            mun_src_res = (
                supabase
                .table("source_records")
                .select("*")
                .eq("version_id", mun_ver_id)
                .execute()
            )
        else:
            # Query latest municipal source records
            mun_src_res = (
                supabase
                .table("source_records")
                .select("*")
                .eq("source_type", "MUNICIPAL")
                .order("created_at", desc=True)
                .execute()
            )

        cad_records = cad_src_res.data or []
        mun_records = mun_src_res.data or []

        if not cad_records or not mun_records:
            raise HTTPException(
                status_code=400,
                detail="Both Cadastral and Municipal source records must be present in the database to run analysis."
            )

        # Extract version and dataset IDs from records
        cad_dataset_id = cad_records[0].get("dataset_id")
        cad_version_id = cad_records[0].get("version_id")
        mun_dataset_id = mun_records[0].get("dataset_id")
        mun_version_id = mun_records[0].get("version_id")

        # Map source records by ID for source linking later
        cad_by_parcel = {}
        for r in cad_records:
            pid = str(r.get("parcel_id") or "").strip()
            if pid and pid not in cad_by_parcel:
                cad_by_parcel[pid] = r

        mun_by_parcel = {}
        for r in mun_records:
            pid = str(r.get("parcel_id") or "").strip()
            if pid and pid not in mun_by_parcel:
                mun_by_parcel[pid] = r

        # -------------------------------------------------------------
        # 3. Build DataFrames from database source records
        # -------------------------------------------------------------
        cadastral_df = pd.DataFrame([
            {
                "parcel_id": r.get("parcel_id"),
                "owner_name": r.get("owner_name"),
                "area": r.get("area"),
                "ward": r.get("ward"),
                "latitude": r.get("latitude"),
                "longitude": r.get("longitude")
            }
            for r in cad_records
        ])

        municipal_df = pd.DataFrame([
            {
                "parcel_id": r.get("parcel_id"),
                "owner_name": r.get("owner_name"),
                "area": r.get("area"),
                "ward": r.get("ward"),
                "latitude": r.get("latitude"),
                "longitude": r.get("longitude")
            }
            for r in mun_records
        ])

        # -------------------------------------------------------------
        # 4. Clean & Harmonize
        # -------------------------------------------------------------
        cadastral_df = clean_dataset(cadastral_df)
        municipal_df = clean_dataset(municipal_df)

        merged = harmonize(cadastral_df, municipal_df)
        conflicts = detect_conflicts(merged)
        harmonized_records = build_harmonized_records(merged)

        # -------------------------------------------------------------
        # 5. Create Analysis Run Record (Non-Destructive History)
        # -------------------------------------------------------------
        run_id = str(uuid.uuid4())

        # Clean conflict records with run_id
        cleaned_conflicts = []
        for conflict in conflicts:
            cleaned_conflict = {
                "analysis_run_id": run_id,
                "parcel_id": clean_for_json(conflict.get("parcel_id")),
                "conflict_type": clean_for_json(conflict.get("conflict_type")),
                "severity": clean_for_json(conflict.get("severity")),
                "description": clean_for_json(conflict.get("description")),
                "difference_value": clean_for_json(conflict.get("difference_value")),
                "recommended_action": clean_for_json(conflict.get("recommended_action")),
                "confidence_score": 0,
                "status": "open"
            }
            cleaned_conflicts.append(cleaned_conflict)

        # Clean harmonized records with run_id
        cleaned_harmonized_records = []
        for record in harmonized_records:
            cleaned_record_data = clean_record(record)
            cleaned_record_data["analysis_run_id"] = run_id
            cleaned_harmonized_records.append(cleaned_record_data)

        # Retrieve previous run to compare against for change history
        prev_run_res = (
            supabase
            .table("analysis_runs")
            .select("id")
            .eq("status", "completed")
            .order("started_at", desc=True)
            .limit(1)
            .execute()
        )
        prev_run_id = prev_run_res.data[0]["id"] if prev_run_res.data else None

        # Insert analysis run
        run_payload = {
            "id": run_id,
            "cadastral_dataset_id": cad_dataset_id,
            "cadastral_version_id": cad_version_id,
            "municipal_dataset_id": mun_dataset_id,
            "municipal_version_id": mun_version_id,
            "status": "completed",
            "records_compared": int(len(merged)),
            "conflicts_detected": int(len(cleaned_conflicts)),
            "harmonized_records_count": int(len(cleaned_harmonized_records)),
            "started_at": started_at,
            "completed_at": datetime.now(timezone.utc).isoformat()
        }

        supabase.table("analysis_runs").insert(run_payload).execute()

        # -------------------------------------------------------------
        # 6. Insert Conflicts & Harmonized Records (Non-Destructive!)
        # -------------------------------------------------------------
        if cleaned_conflicts:
            for i in range(0, len(cleaned_conflicts), 100):
                supabase.table("conflicts").insert(cleaned_conflicts[i:i + 100]).execute()

        if cleaned_harmonized_records:
            for i in range(0, len(cleaned_harmonized_records), 100):
                supabase.table("harmonized_records").insert(cleaned_harmonized_records[i:i + 100]).execute()

        # -------------------------------------------------------------
        # 7. Upsert Canonical Parcels & Source-to-Canonical Links
        # -------------------------------------------------------------
        canonical_map = {}
        for h_rec in cleaned_harmonized_records:
            pid = h_rec["parcel_id"]
            if not pid:
                continue

            cad_item = cad_by_parcel.get(pid)
            mun_item = mun_by_parcel.get(pid)

            lat = cad_item.get("latitude") if cad_item and cad_item.get("latitude") is not None else (
                mun_item.get("latitude") if mun_item else None
            )
            lon = cad_item.get("longitude") if cad_item and cad_item.get("longitude") is not None else (
                mun_item.get("longitude") if mun_item else None
            )

            canonical_payload = {
                "parcel_id": pid,
                "owner_name": h_rec.get("owner_name"),
                "area": h_rec.get("area"),
                "ward": h_rec.get("ward"),
                "latitude": clean_for_json(lat),
                "longitude": clean_for_json(lon),
                "harmonization_score": h_rec.get("harmonization_score"),
                "status": "Harmonized" if float(h_rec.get("harmonization_score") or 0) >= 80 and int(h_rec.get("conflict_count") or 0) == 0 else "Review Required",
                "source_count": h_rec.get("source_count", 1),
                "matching_sources": h_rec.get("matching_sources", 1),
                "conflict_count": h_rec.get("conflict_count", 0),
                "explanation": h_rec.get("explanation"),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }

            try:
                # Upsert into canonical_parcels
                up_res = (
                    supabase
                    .table("canonical_parcels")
                    .upsert(canonical_payload, on_conflict="parcel_id")
                    .execute()
                )
                if up_res.data:
                    canonical_id = up_res.data[0]["id"]
                    canonical_map[pid] = canonical_id
            except Exception as e:
                # Fallback to select ID
                sel = supabase.table("canonical_parcels").select("id").eq("parcel_id", pid).execute()
                if sel.data:
                    canonical_map[pid] = sel.data[0]["id"]

        # Insert parcel_source_links
        links_to_insert = []
        for pid, c_id in canonical_map.items():
            if pid in cad_by_parcel:
                links_to_insert.append({
                    "canonical_parcel_id": c_id,
                    "source_record_id": cad_by_parcel[pid]["id"],
                    "match_method": "EXACT_PARCEL_ID",
                    "match_score": 100.0,
                    "is_primary": True
                })
            if pid in mun_by_parcel:
                links_to_insert.append({
                    "canonical_parcel_id": c_id,
                    "source_record_id": mun_by_parcel[pid]["id"],
                    "match_method": "EXACT_PARCEL_ID",
                    "match_score": 100.0,
                    "is_primary": False
                })

        if links_to_insert:
            for i in range(0, len(links_to_insert), 100):
                try:
                    supabase.table("parcel_source_links").insert(links_to_insert[i:i + 100]).execute()
                except Exception:
                    pass

        # -------------------------------------------------------------
        # 8. Compute Change Detection Deltas if Previous Run Exists
        # -------------------------------------------------------------
        if prev_run_id:
            try:
                compute_and_save_run_changes(prev_run_id, run_id)
            except Exception as e:
                print(f"Notice: change detection skipped: {e}")

        # -------------------------------------------------------------
        # 9. Return Detailed Response
        # -------------------------------------------------------------
        return {
            "success": True,
            "run_id": run_id,
            "analysis_run_id": run_id,
            "records_compared": int(len(merged)),
            "parcels_processed": int(len(merged)),
            "conflicts_detected": int(len(cleaned_conflicts)),
            "conflicts_found": int(len(cleaned_conflicts)),
            "harmonized_records": int(len(cleaned_harmonized_records)),
            "harmonized_count": int(len(cleaned_harmonized_records)),
            "cadastral_version_id": cad_version_id,
            "municipal_version_id": mun_version_id,
            "started_at": started_at,
            "completed_at": run_payload["completed_at"]
        }

    except HTTPException:
        raise
    except Exception as e:
        print("ANALYSIS ERROR:", repr(e))
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


def compute_and_save_run_changes(from_run_id: str, to_run_id: str):
    """
    Compare two completed analysis runs and record detected deltas in analysis_changes.
    """
    from_records_res = supabase.table("harmonized_records").select("*").eq("analysis_run_id", from_run_id).execute()
    to_records_res = supabase.table("harmonized_records").select("*").eq("analysis_run_id", to_run_id).execute()

    from_conflicts_res = supabase.table("conflicts").select("*").eq("analysis_run_id", from_run_id).execute()
    to_conflicts_res = supabase.table("conflicts").select("*").eq("analysis_run_id", to_run_id).execute()

    from_by_pid = {r.get("parcel_id"): r for r in (from_records_res.data or []) if r.get("parcel_id")}
    to_by_pid = {r.get("parcel_id"): r for r in (to_records_res.data or []) if r.get("parcel_id")}

    changes = []

    # 1. New & removed parcels
    for pid in to_by_pid:
        if pid not in from_by_pid:
            changes.append({
                "from_run_id": from_run_id,
                "to_run_id": to_run_id,
                "parcel_id": pid,
                "change_type": "NEW_PARCEL",
                "field_name": "parcel_id",
                "old_value": None,
                "new_value": pid,
                "description": f"Parcel {pid} introduced in this analysis run.",
                "severity": "LOW"
            })

    for pid in from_by_pid:
        if pid not in to_by_pid:
            changes.append({
                "from_run_id": from_run_id,
                "to_run_id": to_run_id,
                "parcel_id": pid,
                "change_type": "REMOVED_PARCEL",
                "field_name": "parcel_id",
                "old_value": pid,
                "new_value": None,
                "description": f"Parcel {pid} removed from analysis universe.",
                "severity": "HIGH"
            })

    # 2. Attribute changes for common parcels
    for pid, to_rec in to_by_pid.items():
        if pid in from_by_pid:
            from_rec = from_by_pid[pid]

            # Owner
            if str(from_rec.get("owner_name") or "") != str(to_rec.get("owner_name") or ""):
                changes.append({
                    "from_run_id": from_run_id,
                    "to_run_id": to_run_id,
                    "parcel_id": pid,
                    "change_type": "OWNER_CHANGED",
                    "field_name": "owner_name",
                    "old_value": str(from_rec.get("owner_name")),
                    "new_value": str(to_rec.get("owner_name")),
                    "description": f"Owner modified from '{from_rec.get('owner_name')}' to '{to_rec.get('owner_name')}'.",
                    "severity": "MEDIUM"
                })

            # Area
            try:
                f_area = float(from_rec.get("area") or 0)
                t_area = float(to_rec.get("area") or 0)
                diff = abs(t_area - f_area)
                if diff > 0.01:
                    changes.append({
                        "from_run_id": from_run_id,
                        "to_run_id": to_run_id,
                        "parcel_id": pid,
                        "change_type": "AREA_CHANGED",
                        "field_name": "area",
                        "old_value": str(f_area),
                        "new_value": str(t_area),
                        "difference": diff,
                        "description": f"Harmonized area changed by {diff:.2f} sq.m.",
                        "severity": "MEDIUM"
                    })
            except Exception:
                pass

            # Score
            try:
                f_score = float(from_rec.get("harmonization_score") or 0)
                t_score = float(to_rec.get("harmonization_score") or 0)
                score_diff = abs(t_score - f_score)
                if score_diff >= 1.0:
                    changes.append({
                        "from_run_id": from_run_id,
                        "to_run_id": to_run_id,
                        "parcel_id": pid,
                        "change_type": "SCORE_CHANGED",
                        "field_name": "harmonization_score",
                        "old_value": str(f_score),
                        "new_value": str(t_score),
                        "difference": score_diff,
                        "description": f"Truth score changed from {f_score} to {t_score}.",
                        "severity": "LOW" if t_score > f_score else "MEDIUM"
                    })
            except Exception:
                pass

    # 3. Conflict delta detection
    from_conf_set = set((c.get("parcel_id"), c.get("conflict_type")) for c in (from_conflicts_res.data or []))
    to_conf_set = set((c.get("parcel_id"), c.get("conflict_type")) for c in (to_conflicts_res.data or []))

    for pid, ctype in to_conf_set - from_conf_set:
        changes.append({
            "from_run_id": from_run_id,
            "to_run_id": to_run_id,
            "parcel_id": pid,
            "change_type": "NEW_CONFLICT",
            "field_name": "conflict_type",
            "old_value": None,
            "new_value": ctype,
            "description": f"New discrepancy detected: {ctype}.",
            "severity": "HIGH"
        })

    for pid, ctype in from_conf_set - to_conf_set:
        changes.append({
            "from_run_id": from_run_id,
            "to_run_id": to_run_id,
            "parcel_id": pid,
            "change_type": "RESOLVED_CONFLICT",
            "field_name": "conflict_type",
            "old_value": ctype,
            "new_value": None,
            "description": f"Conflict {ctype} resolved.",
            "severity": "LOW"
        })

    if not changes and to_by_pid:
        first_pid = next(iter(to_by_pid.keys()))
        changes.append({
            "from_run_id": from_run_id,
            "to_run_id": to_run_id,
            "parcel_id": first_pid,
            "change_type": "UNCHANGED",
            "field_name": None,
            "old_value": None,
            "new_value": None,
            "description": "No attribute or conflict changes detected between runs.",
            "severity": "LOW"
        })

    if changes:
        for i in range(0, len(changes), 100):
            supabase.table("analysis_changes").insert(changes[i:i + 100]).execute()


# =======================================================
# GET /analysis/source-comparison/{parcel_id}
# Database-backed real source comparison
# =======================================================

@router.get("/source-comparison/{parcel_id}")
def source_comparison(
    parcel_id: str,
    profile: dict = Depends(require_permission("source_comparison.view"))
):
    clean_pid = parcel_id.strip()

    # 1. Fetch canonical parcel truth
    canon_res = (
        supabase
        .table("canonical_parcels")
        .select("*")
        .eq("parcel_id", clean_pid)
        .limit(1)
        .execute()
    )
    canonical = canon_res.data[0] if canon_res.data else None

    # 2. Fetch real source records from Supabase
    src_res = (
        supabase
        .table("source_records")
        .select("*")
        .eq("parcel_id", clean_pid)
        .order("created_at", desc=True)
        .execute()
    )
    src_records = src_res.data or []

    cadastral_rec = next((r for r in src_records if str(r.get("source_type") or "").upper() == "CADASTRAL"), None)
    municipal_rec = next((r for r in src_records if str(r.get("source_type") or "").upper() == "MUNICIPAL"), None)

    if not cadastral_rec and not municipal_rec and not canonical:
        raise HTTPException(
            status_code=404,
            detail=f"Parcel {clean_pid} not found in database source records."
        )

    # Clean dictionaries for client response with robust raw_data fallbacks
    cad_raw = cadastral_rec.get("raw_data") or {} if cadastral_rec else {}
    cadastral_data = (
        {
            "owner_name": cadastral_rec.get("owner_name") or cad_raw.get("owner_name") or cad_raw.get("property_owner"),
            "area": cadastral_rec.get("area") or cad_raw.get("area") or cad_raw.get("area_sqm") or cad_raw.get("built_area_sqm"),
            "ward": cadastral_rec.get("ward") or cad_raw.get("ward"),
            "latitude": cadastral_rec.get("latitude") or cad_raw.get("latitude") or cad_raw.get("centroid_lat"),
            "longitude": cadastral_rec.get("longitude") or cad_raw.get("longitude") or cad_raw.get("centroid_lng")
        }
        if cadastral_rec
        else None
    )

    mun_raw = municipal_rec.get("raw_data") or {} if municipal_rec else {}
    municipal_data = (
        {
            "owner_name": municipal_rec.get("owner_name") or mun_raw.get("owner_name") or mun_raw.get("property_owner"),
            "area": municipal_rec.get("area") or mun_raw.get("area") or mun_raw.get("built_area_sqm") or mun_raw.get("area_sqm"),
            "ward": municipal_rec.get("ward") or mun_raw.get("ward"),
            "latitude": municipal_rec.get("latitude") or mun_raw.get("latitude") or mun_raw.get("centroid_lat"),
            "longitude": municipal_rec.get("longitude") or mun_raw.get("longitude") or mun_raw.get("centroid_lng")
        }
        if municipal_rec
        else None
    )

    sources_list = [r for r in [cadastral_rec, municipal_rec] if r is not None]

    return {
        "success": True,
        "parcel_id": clean_pid,
        "canonical": canonical,
        "sources": sources_list,
        "source_count": len(sources_list),
        "cadastral": cadastral_data,
        "municipal": municipal_data
    }


# =======================================================
# GET /analysis/runs
# List historical analysis executions
# =======================================================

@router.get("/runs")
def get_analysis_runs(
    profile: dict = Depends(require_permission("analysis.view"))
):
    try:
        response = (
            supabase
            .table("analysis_runs")
            .select("*")
            .order("started_at", desc=True)
            .execute()
        )
        runs = response.data or []
        return {
            "success": True,
            "count": len(runs),
            "runs": runs
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# =======================================================
# GET /analysis/runs/{run_id}
# Retrieve single run details
# =======================================================

@router.get("/runs/{run_id}")
def get_analysis_run(
    run_id: str,
    profile: dict = Depends(require_permission("analysis.view"))
):
    try:
        if run_id == "latest":
            response = (
                supabase
                .table("analysis_runs")
                .select("*")
                .eq("status", "completed")
                .order("started_at", desc=True)
                .limit(1)
                .execute()
            )
        else:
            response = (
                supabase
                .table("analysis_runs")
                .select("*")
                .eq("id", run_id)
                .execute()
            )

        if not response.data:
            raise HTTPException(status_code=404, detail="Analysis run not found.")

        return {
            "success": True,
            "run": response.data[0]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# =======================================================
# GET /analysis/runs/{run_id}/summary
# =======================================================

@router.get("/runs/{run_id}/summary")
def get_analysis_run_summary(
    run_id: str,
    profile: dict = Depends(require_permission("analysis.view"))
):
    try:
        if run_id == "latest":
            response = (
                supabase
                .table("analysis_runs")
                .select("*")
                .eq("status", "completed")
                .order("started_at", desc=True)
                .limit(1)
                .execute()
            )
        else:
            response = (
                supabase
                .table("analysis_runs")
                .select("*")
                .eq("id", run_id)
                .execute()
            )

        if not response.data:
            raise HTTPException(status_code=404, detail="Analysis run summary not found.")

        return {
            "success": True,
            "summary": response.data[0]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# =======================================================
# POST /analysis/compare-runs
# Compare two runs and generate change history
# =======================================================

@router.post("/compare-runs")
def compare_runs(
    request: Optional[CompareRunsRequest] = None,
    profile: dict = Depends(require_permission("analysis.run"))
):
    try:
        from_id = request.from_run_id if request else None
        to_id = request.to_run_id if request else None

        if not from_id or not to_id:
            recent_runs = (
                supabase
                .table("analysis_runs")
                .select("id")
                .eq("status", "completed")
                .order("started_at", desc=True)
                .limit(2)
                .execute()
            )
            data = recent_runs.data or []
            if len(data) < 2:
                return {
                    "success": False,
                    "message": "At least two completed analysis runs are required to compare."
                }
            to_id = data[0]["id"]
            from_id = data[1]["id"]

        compute_and_save_run_changes(from_id, to_id)

        changes_res = (
            supabase
            .table("analysis_changes")
            .select("*")
            .eq("from_run_id", from_id)
            .eq("to_run_id", to_id)
            .execute()
        )

        return {
            "success": True,
            "from_run_id": from_id,
            "to_run_id": to_id,
            "changes_detected": len(changes_res.data or []),
            "changes": changes_res.data or []
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# =======================================================
# GET /analysis/changes
# Retrieve change history
# =======================================================

@router.get("/changes")
def get_analysis_changes(
    limit: int = 100,
    profile: dict = Depends(require_permission("analysis.view"))
):
    try:
        response = (
            supabase
            .table("analysis_changes")
            .select("*")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return {
            "success": True,
            "count": len(response.data or []),
            "changes": response.data or []
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# =======================================================
# GET /analysis/changes/summary
# Summarize change delta metrics
# =======================================================

@router.get("/changes/summary")
def get_changes_summary(
    profile: dict = Depends(require_permission("analysis.view"))
):
    try:
        response = (
            supabase
            .table("analysis_changes")
            .select("change_type, severity")
            .execute()
        )
        data = response.data or []

        type_counts = {}
        severity_counts = {}

        for item in data:
            ct = item.get("change_type", "UNKNOWN")
            sev = item.get("severity", "MEDIUM")
            type_counts[ct] = type_counts.get(ct, 0) + 1
            severity_counts[sev] = severity_counts.get(sev, 0) + 1

        return {
            "success": True,
            "total_changes": len(data),
            "by_type": type_counts,
            "by_severity": severity_counts
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
