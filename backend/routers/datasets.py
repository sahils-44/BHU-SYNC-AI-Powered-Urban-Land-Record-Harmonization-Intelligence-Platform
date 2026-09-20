import os
import uuid
import pandas as pd

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends

from services.cleaner import clean_dataset
from services.quality import calculate_quality_score
from supabase_client import supabase
from dependencies.auth import require_permission
from middleware.security import validate_uploaded_file


router = APIRouter(
    prefix="/datasets",
    tags=["Datasets"]
)


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


# =========================================
# POST /datasets/upload
# Upload, version, and persist source records
# =========================================

@router.post("/upload")
async def upload_dataset(
    file: UploadFile = File(...),
    source_type: str = Form("CADASTRAL"),
    profile: dict = Depends(require_permission("datasets.upload"))
):
    # Read contents into memory
    contents = await file.read()

    # --------------------------------
    # 1. Security Validation (Path traversal, size limit, extensions)
    # --------------------------------
    validate_uploaded_file(file.filename, contents)

    extension = os.path.splitext(file.filename)[1].lower()

    # Normalize source_type
    normalized_source_type = source_type.strip().upper()
    if normalized_source_type not in ["CADASTRAL", "MUNICIPAL", "REGISTRY", "TAX", "SATELLITE", "SURVEY_OF_INDIA", "UTILITY_WATER", "UTILITY_ELECTRICITY", "BUILDING_PERMIT", "BANK_MORTGAGE"]:
        normalized_source_type = "CADASTRAL"

    # --------------------------------
    # 2. Write to unique temporary file (prevents concurrency collisions)
    # --------------------------------
    os.makedirs("data", exist_ok=True)
    unique_temp_name = f"temp_{uuid.uuid4().hex}{extension}"
    temp_path = os.path.join("data", unique_temp_name)

    with open(temp_path, "wb") as f:
        f.write(contents)


    try:
        # Read file with appropriate engine
        if extension == ".csv":
            df = pd.read_csv(temp_path)
        else:
            df = pd.read_excel(temp_path)

        if len(df) == 0:
            raise HTTPException(
                status_code=400,
                detail="Uploaded file is empty."
            )

        # --------------------------------
        # 3. Clean dataset & calculate quality
        # --------------------------------
        cleaned_df = clean_dataset(df)
        quality_score = calculate_quality_score(cleaned_df)

        dataset_base_name = os.path.splitext(file.filename)[0].strip()

        # --------------------------------
        # 4. Handle Dataset & Versioning
        # --------------------------------
        # Check if dataset with this name & source_type already exists
        existing_ds_res = (
            supabase
            .table("datasets")
            .select("*")
            .eq("name", dataset_base_name)
            .eq("source_type", normalized_source_type)
            .execute()
        )

        existing_datasets = existing_ds_res.data or []

        if existing_datasets:
            dataset_record = existing_datasets[0]
            dataset_id = dataset_record["id"]

            # Query highest version number for this dataset
            ver_res = (
                supabase
                .table("dataset_versions")
                .select("version_number")
                .eq("dataset_id", dataset_id)
                .order("version_number", desc=True)
                .limit(1)
                .execute()
            )

            if ver_res.data:
                version_number = int(ver_res.data[0]["version_number"]) + 1
            else:
                version_number = 1

            # Update master dataset summary metadata
            supabase.table("datasets").update({
                "record_count": len(cleaned_df),
                "quality_score": quality_score,
                "file_name": file.filename,
                "status": "processed"
            }).eq("id", dataset_id).execute()

        else:
            # Create new dataset
            dataset_payload = {
                "name": dataset_base_name,
                "source_type": normalized_source_type,
                "file_name": file.filename,
                "record_count": len(cleaned_df),
                "quality_score": quality_score,
                "status": "processed"
            }

            ds_insert_res = (
                supabase
                .table("datasets")
                .insert(dataset_payload)
                .execute()
            )

            if not ds_insert_res.data:
                raise RuntimeError("Failed to create dataset in Supabase.")

            dataset_record = ds_insert_res.data[0]
            dataset_id = dataset_record["id"]
            version_number = 1

        # --------------------------------
        # 5. Insert dataset_versions record
        # --------------------------------
        version_payload = {
            "dataset_id": dataset_id,
            "version_number": version_number,
            "record_count": len(cleaned_df),
            "quality_score": quality_score,
            "status": "processed"
        }

        ver_insert_res = (
            supabase
            .table("dataset_versions")
            .insert(version_payload)
            .execute()
        )

        if not ver_insert_res.data:
            raise RuntimeError("Failed to create dataset version in Supabase.")

        version_record = ver_insert_res.data[0]
        version_id = version_record["id"]

        # --------------------------------
        # 6. Persist individual source records (Do NOT discard!)
        # --------------------------------
        records_to_insert = []

        for idx, row in cleaned_df.iterrows():
            raw_row = df.iloc[idx].to_dict() if idx < len(df) else row.to_dict()

            rec = {
                "dataset_id": dataset_id,
                "version_id": version_id,
                "source_type": normalized_source_type,
                "parcel_id": clean_for_json(row.get("parcel_id")),
                "owner_name": clean_for_json(row.get("owner_name")),
                "area": clean_for_json(row.get("area")),
                "ward": clean_for_json(row.get("ward")),
                "latitude": clean_for_json(row.get("latitude")),
                "longitude": clean_for_json(row.get("longitude")),
                "raw_data": clean_record(raw_row)
            }
            records_to_insert.append(rec)

        # Batch insert into source_records (chunks of 100)
        chunk_size = 100
        for i in range(0, len(records_to_insert), chunk_size):
            chunk = records_to_insert[i:i + chunk_size]
            supabase.table("source_records").insert(chunk).execute()

        # --------------------------------
        # 7. Return enriched response
        # --------------------------------
        return {
            "success": True,
            "message": f"Dataset '{file.filename}' uploaded and persisted as {normalized_source_type} V{version_number}.",
            "dataset_id": dataset_id,
            "version_id": version_id,
            "version": version_number,
            "version_number": version_number,
            "source_type": normalized_source_type,
            "file_name": file.filename,
            "records": len(cleaned_df),
            "quality_score": quality_score
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Upload processing failed: {str(e)}"
        )

    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass


# =========================================
# GET /datasets/
# Get all datasets enriched with versions
# =========================================

@router.get("/")
def get_datasets(profile: dict = Depends(require_permission("datasets.view"))):
    try:
        response = (
            supabase
            .table("datasets")
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )

        datasets = response.data or []

        # Enrich datasets with latest version information
        try:
            versions_res = (
                supabase
                .table("dataset_versions")
                .select("dataset_id, version_number, created_at, record_count, quality_score")
                .order("version_number", desc=True)
                .execute()
            )
            all_versions = versions_res.data or []
            
            for d in datasets:
                d_vers = [v for v in all_versions if v.get("dataset_id") == d.get("id")]
                d["latest_version"] = d_vers[0]["version_number"] if d_vers else 1
                d["total_versions"] = len(d_vers) if d_vers else 1
        except Exception:
            for d in datasets:
                d["latest_version"] = 1
                d["total_versions"] = 1

        return {
            "success": True,
            "count": len(datasets),
            "datasets": datasets
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# =========================================
# GET /datasets/{dataset_id}/versions
# List versions for a dataset
# =========================================

@router.get("/{dataset_id}/versions")
def get_dataset_versions(
    dataset_id: str,
    profile: dict = Depends(require_permission("datasets.view"))
):
    try:
        response = (
            supabase
            .table("dataset_versions")
            .select("*")
            .eq("dataset_id", dataset_id)
            .order("version_number", desc=True)
            .execute()
        )

        return {
            "success": True,
            "count": len(response.data or []),
            "versions": response.data or []
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

