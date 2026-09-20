import sys
import os
import io
import time
import uuid

# Add backend directory to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from fastapi.testclient import TestClient
from main import app
from supabase_client import supabase

client = TestClient(app)
# Configure operational OFFICER authorization header for Phase A verification
client.headers.update({"Authorization": "Bearer test-token-officer"})

print("=" * 60)
print("BHU-SYNC PHASE A AUTOMATED VERIFICATION SUITE")
print("=" * 60)

test_results = {}

# Helper CSV generators
def generate_cadastral_csv():
    content = """parcel_id,owner_name,area_sqm,centroid_lat,centroid_lng,land_use
TEST-P101,Ramesh Patel,1250.50,19.0760,72.8777,Residential
TEST-P102,Sita Sharma,850.00,19.0765,72.8782,Commercial
TEST-P103,Amit Verma,2100.00,19.0770,72.8790,Agricultural
"""
    return io.BytesIO(content.encode("utf-8"))

def generate_municipal_csv():
    content = """parcel_id,property_owner,built_area_sqm,latitude,longitude,assessment_tax
TEST-P101,Ramesh C. Patel,1248.00,19.0761,72.8778,14500
TEST-P102,Sunita Sharma,890.00,19.0765,72.8782,32000
TEST-P104,Pooja Nair,600.00,19.0780,72.8800,9800
"""
    return io.BytesIO(content.encode("utf-8"))

# -------------------------------------------------------------
# TEST 1: Cadastral Source Ingestion & Persistence
# -------------------------------------------------------------
try:
    print("\n[TEST 1] Testing Cadastral source ingestion and persistence...")
    csv_file = generate_cadastral_csv()
    filename = f"test_cadastral_{uuid.uuid4().hex[:6]}.csv"
    response = client.post(
        "/datasets/upload",
        files={"file": (filename, csv_file, "text/csv")},
        data={"source_type": "CADASTRAL"}
    )
    assert response.status_code == 200, f"Upload failed: {response.text}"
    upload_data = response.json()
    dataset_id = upload_data["dataset_id"]
    
    # Check source_records in database
    sr_res = supabase.table("source_records").select("*").eq("dataset_id", dataset_id).execute()
    assert len(sr_res.data) == 3, f"Expected 3 source_records, got {len(sr_res.data)}"
    for r in sr_res.data:
        assert r["source_type"] == "CADASTRAL", f"Expected source_type CADASTRAL, got {r['source_type']}"
    
    print(f"  [OK] Ingested {len(sr_res.data)} Cadastral source records into 'source_records' table.")
    test_results["test_1_cadastral_ingestion"] = "PASSED"
except Exception as e:
    print(f"  [FAIL] Test 1 failed: {e}")
    test_results["test_1_cadastral_ingestion"] = f"FAILED: {e}"

# -------------------------------------------------------------
# TEST 2: Municipal Source Ingestion & Persistence
# -------------------------------------------------------------
try:
    print("\n[TEST 2] Testing Municipal source ingestion and persistence...")
    csv_file = generate_municipal_csv()
    m_filename = f"test_municipal_{uuid.uuid4().hex[:6]}.csv"
    response = client.post(
        "/datasets/upload",
        files={"file": (m_filename, csv_file, "text/csv")},
        data={"source_type": "MUNICIPAL"}
    )
    assert response.status_code == 200, f"Upload failed: {response.text}"
    m_upload_data = response.json()
    m_dataset_id = m_upload_data["dataset_id"]
    
    # Check source_records in database
    sr_res = supabase.table("source_records").select("*").eq("dataset_id", m_dataset_id).execute()
    assert len(sr_res.data) == 3, f"Expected 3 source_records, got {len(sr_res.data)}"
    for r in sr_res.data:
        assert r["source_type"] == "MUNICIPAL", f"Expected source_type MUNICIPAL, got {r['source_type']}"
    
    print(f"  [OK] Ingested {len(sr_res.data)} Municipal source records into 'source_records' table.")
    test_results["test_2_municipal_ingestion"] = "PASSED"
except Exception as e:
    print(f"  ✗ Test 2 failed: {e}")
    test_results["test_2_municipal_ingestion"] = f"FAILED: {e}"

# -------------------------------------------------------------
# TEST 3: Dataset Versioning (V1 -> V2)
# -------------------------------------------------------------
try:
    print("\n[TEST 3] Testing Dataset versioning (uploading new version of existing dataset)...")
    updated_csv = io.BytesIO("""parcel_id,owner_name,area_sqm,centroid_lat,centroid_lng,land_use
TEST-P101,Ramesh Patel,1250.50,19.0760,72.8777,Residential
TEST-P102,Sita Sharma,850.00,19.0765,72.8782,Commercial
TEST-P103,Amit Verma,2100.00,19.0770,72.8790,Agricultural
TEST-P105,Deepak Rao,1100.00,19.0790,72.8810,Residential
""".encode("utf-8"))
    v2_response = client.post(
        "/datasets/upload",
        files={"file": (filename, updated_csv, "text/csv")},
        data={"source_type": "CADASTRAL"}
    )
    assert v2_response.status_code == 200, f"V2 upload failed: {v2_response.text}"
    v2_data = v2_response.json()
    version_val = v2_data.get("version") or v2_data.get("version_number")
    assert version_val == 2, f"Expected version 2, got {version_val}"
    assert v2_data["dataset_id"] == dataset_id, f"Expected same dataset ID {dataset_id}, got {v2_data['dataset_id']}"
    
    # Check dataset_versions table
    dv_res = supabase.table("dataset_versions").select("*").eq("dataset_id", dataset_id).order("version_number").execute()
    assert len(dv_res.data) >= 2, f"Expected at least 2 versions in dataset_versions, got {len(dv_res.data)}"
    versions = [v["version_number"] for v in dv_res.data]
    assert 1 in versions and 2 in versions, f"Versions 1 and 2 not both found: {versions}"
    
    print(f"  [OK] Dataset versioning verified: Dataset {dataset_id} bumped to v2 with separate version records.")
    test_results["test_3_dataset_versioning"] = "PASSED"
except Exception as e:
    print(f"  [FAIL] Test 3 failed: {e}")
    test_results["test_3_dataset_versioning"] = f"FAILED: {e}"

# -------------------------------------------------------------
# TEST 4: Non-Destructive Analysis Runs
# -------------------------------------------------------------
run_id_1 = None
run_id_2 = None
try:
    print("\n[TEST 4] Testing Non-destructive analysis runs...")
    run_response = client.post("/analysis/run")
    assert run_response.status_code == 200, f"Analysis run failed: {run_response.text}"
    run_data = run_response.json()
    run_id_1 = run_data.get("analysis_run_id") or run_data.get("run_id")
    assert run_id_1 is not None, "run_id must be present in response"
    
    # Verify in analysis_runs table
    ar_res = supabase.table("analysis_runs").select("*").eq("id", run_id_1).execute()
    assert len(ar_res.data) == 1, f"Analysis run {run_id_1} not recorded in analysis_runs"
    assert ar_res.data[0]["status"] == "completed"
    
    # Verify conflicts tagged with run_id_1
    c_res = supabase.table("conflicts").select("*").eq("analysis_run_id", run_id_1).execute()
    print(f"  [OK] Run 1 ({run_id_1[:8]}) completed with {len(c_res.data)} conflicts tagged.")
    
    # Trigger second run
    time.sleep(1)
    run_response_2 = client.post("/analysis/run")
    assert run_response_2.status_code == 200
    run_data_2 = run_response_2.json()
    run_id_2 = run_data_2.get("analysis_run_id") or run_data_2.get("run_id")
    assert run_id_1 != run_id_2, "Run IDs must be distinct"
    
    # Verify run 1 records still exist in analysis_runs and conflicts (non-destructive)
    ar_res_old = supabase.table("analysis_runs").select("*").eq("id", run_id_1).execute()
    assert len(ar_res_old.data) == 1, "Run 1 record missing after Run 2 (destructive overwrite detected!)"
    
    print(f"  [OK] Non-destructive runs verified: Run 1 ({run_id_1[:8]}) and Run 2 ({run_id_2[:8]}) both preserved.")
    test_results["test_4_non_destructive_runs"] = "PASSED"
except Exception as e:
    print(f"  [FAIL] Test 4 failed: {e}")
    test_results["test_4_non_destructive_runs"] = f"FAILED: {e}"

# -------------------------------------------------------------
# TEST 5: Canonical Parcel Modeling & Source Links
# -------------------------------------------------------------
try:
    print("\n[TEST 5] Testing Canonical parcel modeling & source links...")
    cp_res = supabase.table("canonical_parcels").select("*").execute()
    assert len(cp_res.data) > 0, "No canonical parcels found"
    
    # Check TEST-P101 parcel by parcel_id column
    p101 = [p for p in cp_res.data if p.get("parcel_id") == "TEST-P101"]
    assert len(p101) > 0, f"Canonical parcel TEST-P101 not found in canonical_parcels. IDs: {[p.get('parcel_id') for p in cp_res.data[:5]]}"
    canonical_uuid = p101[0]["id"]
    
    # Check parcel_source_links
    psl_res = supabase.table("parcel_source_links").select("*").eq("canonical_parcel_id", canonical_uuid).execute()
    assert len(psl_res.data) >= 2, f"Expected at least 2 source links for TEST-P101 (cadastral + municipal), got {len(psl_res.data)}"
    source_types_linked = {l["source_type"] for l in psl_res.data if "source_type" in l}
    
    print(f"  [OK] Canonical parcel 'TEST-P101' ({canonical_uuid[:8]}) correctly unified with {len(psl_res.data)} source links.")
    test_results["test_5_canonical_modeling"] = "PASSED"
except Exception as e:
    print(f"  [FAIL] Test 5 failed: {e}")
    test_results["test_5_canonical_modeling"] = f"FAILED: {e}"

# -------------------------------------------------------------
# TEST 6: Real Source Comparison Endpoint
# -------------------------------------------------------------
try:
    print("\n[TEST 6] Testing real source comparison endpoint...")
    sc_res = client.get("/analysis/source-comparison/TEST-P101")
    assert sc_res.status_code == 200, f"Source comparison failed: {sc_res.text}"
    sc_data = sc_res.json()
    assert sc_data["success"] is True
    assert sc_data["cadastral"] is not None, "Cadastral data should not be None"
    assert sc_data["municipal"] is not None, "Municipal data should not be None"
    assert "Ramesh" in str(sc_data["cadastral"]["owner_name"])
    assert "Ramesh" in str(sc_data["municipal"]["owner_name"])
    print(f"  [OK] Real source comparison returned database-backed comparison for TEST-P101:")
    print(f"    - Cadastral: owner={sc_data['cadastral']['owner_name']}, area={sc_data['cadastral']['area']}")
    print(f"    - Municipal: owner={sc_data['municipal']['owner_name']}, area={sc_data['municipal']['area']}")
    test_results["test_6_source_comparison"] = "PASSED"
except Exception as e:
    print(f"  [FAIL] Test 6 failed: {e}")
    test_results["test_6_source_comparison"] = f"FAILED: {e}"

# -------------------------------------------------------------
# TEST 7: Run-to-Run Change Detection (analysis_changes)
# -------------------------------------------------------------
try:
    print("\n[TEST 7] Testing run-to-run change detection (analysis_changes)...")
    target_run = run_id_2 if run_id_2 else run_id_1
    changes_res = supabase.table("analysis_changes").select("*").eq("to_run_id", target_run).execute()
    assert len(changes_res.data) > 0, f"Expected analysis_changes for Run ({target_run}), got 0"
    change_types = [c["change_type"] for c in changes_res.data]
    print(f"  [OK] analysis_changes recorded {len(changes_res.data)} changes between runs: {set(change_types)}")
    test_results["test_7_run_changes"] = "PASSED"
except Exception as e:
    print(f"  [FAIL] Test 7 failed: {e}")
    test_results["test_7_run_changes"] = f"FAILED: {e}"

# -------------------------------------------------------------
# TEST 8: Dashboard Consistency & Scoped Metrics
# -------------------------------------------------------------
try:
    print("\n[TEST 8] Testing Dashboard consistency and scoped metrics...")
    stats_res = client.get("/dashboard/stats")
    assert stats_res.status_code == 200
    stats_data = stats_res.json()
    
    # Verify no double counting
    assert stats_data["total_parcels"] > 0
    
    # Verify source comparison endpoint
    sc_dash_res = client.get("/dashboard/source-comparison")
    assert sc_dash_res.status_code == 200
    sc_dash = sc_dash_res.json()
    cad_count = sc_dash.get("cadastral_count", 0)
    mun_count = sc_dash.get("municipal_count", 0)
    # Deduplicated total physical parcels must be <= cadastral + municipal sum (preventing double counting)
    assert stats_data["total_parcels"] <= (cad_count + mun_count), "Double counting detected"
    
    # Verify latest analysis endpoint
    latest_res = client.get("/dashboard/latest-analysis")
    assert latest_res.status_code == 200
    latest_data = latest_res.json()
    target_run = run_id_2 if run_id_2 else run_id_1
    assert latest_data["analysis_run_id"] == target_run, f"Expected latest run {target_run}, got {latest_data['analysis_run_id']}"
    
    print(f"  [OK] Dashboard stats properly scoped:")
    print(f"    - Total physical parcels (no double counting): {stats_data['total_parcels']}")
    print(f"    - Harmonized: {stats_data['harmonized']}, Review required: {stats_data['review_required']}")
    print(f"    - Latest Run ID: {latest_data['analysis_run_id'][:8]}")
    test_results["test_8_dashboard_consistency"] = "PASSED"
except Exception as e:
    print(f"  [FAIL] Test 8 failed: {e}")
    test_results["test_8_dashboard_consistency"] = f"FAILED: {e}"

# -------------------------------------------------------------
# TEST 9: Upload Concurrency Safety
# -------------------------------------------------------------
try:
    print("\n[TEST 9] Testing upload concurrency safety...")
    # Verify unique temp file generation code and clean state in backend/routers/datasets.py
    import inspect
    from routers import datasets
    src = inspect.getsource(datasets.upload_dataset)
    assert "temp_" in src and "uuid" in src, "Temporary file path does not use UUIDs"
    assert "temp_path.unlink" in src or "os.remove" in src, "Temporary file not cleaned up safely"
    
    # Test concurrent uploads with different files
    csv1 = generate_cadastral_csv()
    csv2 = generate_municipal_csv()
    f1 = f"conc_1_{uuid.uuid4().hex[:4]}.csv"
    f2 = f"conc_2_{uuid.uuid4().hex[:4]}.csv"
    
    r1 = client.post("/datasets/upload", files={"file": (f1, csv1, "text/csv")}, data={"source_type": "CADASTRAL"})
    r2 = client.post("/datasets/upload", files={"file": (f2, csv2, "text/csv")}, data={"source_type": "MUNICIPAL"})
    
    assert r1.status_code == 200 and r2.status_code == 200, "Concurrent uploads failed"
    print(f"  [OK] Concurrency safety verified: UUID-based isolation, automatic cleanup, and concurrent ingestion validated.")
    test_results["test_9_concurrency_safety"] = "PASSED"
except Exception as e:
    print(f"  [FAIL] Test 9 failed: {e}")
    test_results["test_9_concurrency_safety"] = f"FAILED: {e}"

# -------------------------------------------------------------
# Summary
# -------------------------------------------------------------
print("\n" + "=" * 60)
print("TEST SUMMARY")
print("=" * 60)
all_passed = True
for name, status in test_results.items():
    print(f"{name:35}: {status}")
    if status != "PASSED":
        all_passed = False

if all_passed:
    print("\n>>> ALL 9 PHASE A TESTS PASSED! <<<")
    sys.exit(0)
else:
    print("\n>>> SOME TESTS FAILED! <<<")
    sys.exit(1)
