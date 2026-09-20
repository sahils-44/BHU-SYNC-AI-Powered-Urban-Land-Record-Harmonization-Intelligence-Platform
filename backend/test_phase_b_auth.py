"""
BHU-SYNC PHASE B: AUTHENTICATION + GOVERNMENT ROLES AUTOMATED TEST SUITE
Verifies all 11 required Phase B security and RBAC scenarios:
1. Unauthenticated access rejected for protected routes (HTTP 401)
2. Valid authenticated user accepted (HTTP 200)
3. Invalid/expired auth rejected (HTTP 401)
4. VIEWER cannot upload datasets (HTTP 403)
5. VIEWER cannot execute analysis/harmonization (HTTP 403)
6. OFFICER can perform permitted operational actions (HTTP 200)
7. DEPARTMENT_ADMIN can manage eligible department users (HTTP 200)
8. Cross-organization management blocked for Department Admins (HTTP 403)
9. Inactive users blocked from protected operations (HTTP 403)
10. Database-driven role and permission resolution verified
11. Existing Phase A pipeline remains functional
"""

import io
import os
import sys
import uuid

# Add backend directory to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from fastapi.testclient import TestClient
from main import app
from services.auth_service import auth_service, TEST_USERS_STORE

client = TestClient(app)

print("=" * 70)
print("BHU-SYNC PHASE B AUTOMATED VERIFICATION SUITE")
print("=" * 70)

test_results = {}

def get_test_csv():
    content = """parcel_id,owner_name,area_sqm,centroid_lat,centroid_lng,land_use
TEST-B101,Ramesh Patel,1200.00,19.0760,72.8777,Residential
"""
    return io.BytesIO(content.encode("utf-8"))


# -------------------------------------------------------------
# TEST 1: Unauthenticated Access Rejection (HTTP 401)
# -------------------------------------------------------------
try:
    print("\n[TEST 1] Testing unauthenticated access rejection for protected routes...")
    r1 = client.get("/dashboard/stats")
    assert r1.status_code == 401, f"Expected 401 on /dashboard/stats, got {r1.status_code}"

    r2 = client.post("/datasets/upload", files={"file": ("t.csv", get_test_csv(), "text/csv")})
    assert r2.status_code == 401, f"Expected 401 on /datasets/upload, got {r2.status_code}"

    r3 = client.post("/analysis/run")
    assert r3.status_code == 401, f"Expected 401 on /analysis/run, got {r3.status_code}"

    r4 = client.get("/admin/users")
    assert r4.status_code == 401, f"Expected 401 on /admin/users, got {r4.status_code}"

    print("  [OK] All protected routes strictly reject unauthenticated access with HTTP 401.")
    test_results["test_1_unauthenticated_rejected"] = "PASSED"
except Exception as e:
    print(f"  [FAIL] Test 1 failed: {e}")
    test_results["test_1_unauthenticated_rejected"] = f"FAILED: {e}"


# -------------------------------------------------------------
# TEST 2: Valid Authenticated User Accepted (HTTP 200)
# -------------------------------------------------------------
try:
    print("\n[TEST 2] Testing valid authenticated user acceptance...")
    headers = {"Authorization": "Bearer test-token-officer"}
    r = client.get("/auth/me", headers=headers)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    data = r.json()
    assert data["email"] == "officer@test.local"
    assert data["role"] == "OFFICER"
    assert "datasets.upload" in data["permissions"]

    print(f"  [OK] Authenticated user accepted: {data['email']} ({data['role']})")
    test_results["test_2_valid_auth_accepted"] = "PASSED"
except Exception as e:
    print(f"  [FAIL] Test 2 failed: {e}")
    test_results["test_2_valid_auth_accepted"] = f"FAILED: {e}"


# -------------------------------------------------------------
# TEST 3: Invalid / Expired Auth Rejection (HTTP 401)
# -------------------------------------------------------------
try:
    print("\n[TEST 3] Testing invalid and expired token rejection...")
    bad_headers = {"Authorization": "Bearer invalid-tampered-token-xyz"}
    r = client.get("/dashboard/stats", headers=bad_headers)
    assert r.status_code == 401, f"Expected 401 on invalid token, got {r.status_code}"

    expired_headers = {"Authorization": "Bearer expired-token-12345"}
    r2 = client.get("/auth/me", headers=expired_headers)
    assert r2.status_code == 401, f"Expected 401 on expired token, got {r2.status_code}"

    print("  [OK] Invalid and expired tokens properly rejected with HTTP 401.")
    test_results["test_3_invalid_expired_rejected"] = "PASSED"
except Exception as e:
    print(f"  [FAIL] Test 3 failed: {e}")
    test_results["test_3_invalid_expired_rejected"] = f"FAILED: {e}"


# -------------------------------------------------------------
# TEST 4: VIEWER Cannot Upload (HTTP 403)
# -------------------------------------------------------------
try:
    print("\n[TEST 4] Testing that VIEWER cannot upload datasets...")
    viewer_headers = {"Authorization": "Bearer test-token-viewer"}
    csv_file = get_test_csv()
    r = client.post(
        "/datasets/upload",
        headers=viewer_headers,
        files={"file": ("test.csv", csv_file, "text/csv")},
        data={"source_type": "CADASTRAL"}
    )
    assert r.status_code == 403, f"Expected 403 for VIEWER upload, got {r.status_code}"
    assert "datasets.upload" in r.text

    print("  [OK] VIEWER upload blocked with HTTP 403 (requires 'datasets.upload').")
    test_results["test_4_viewer_cannot_upload"] = "PASSED"
except Exception as e:
    print(f"  [FAIL] Test 4 failed: {e}")
    test_results["test_4_viewer_cannot_upload"] = f"FAILED: {e}"


# -------------------------------------------------------------
# TEST 5: VIEWER Cannot Run Analysis (HTTP 403)
# -------------------------------------------------------------
try:
    print("\n[TEST 5] Testing that VIEWER cannot run analysis...")
    viewer_headers = {"Authorization": "Bearer test-token-viewer"}
    r = client.post("/analysis/run", headers=viewer_headers)
    assert r.status_code == 403, f"Expected 403 for VIEWER run, got {r.status_code}"
    assert "analysis.run" in r.text

    r_harm = client.post("/harmonization/run", headers=viewer_headers)
    assert r_harm.status_code == 403, f"Expected 403 for VIEWER harmonization run, got {r_harm.status_code}"

    print("  [OK] VIEWER execution blocked with HTTP 403 (requires 'analysis.run').")
    test_results["test_5_viewer_cannot_run_analysis"] = "PASSED"
except Exception as e:
    print(f"  [FAIL] Test 5 failed: {e}")
    test_results["test_5_viewer_cannot_run_analysis"] = f"FAILED: {e}"


# -------------------------------------------------------------
# TEST 6: OFFICER Can Perform Permitted Operational Actions (HTTP 200)
# -------------------------------------------------------------
try:
    print("\n[TEST 6] Testing that OFFICER can perform permitted actions...")
    officer_headers = {"Authorization": "Bearer test-token-officer"}

    # 1. View Dashboard
    r_dash = client.get("/dashboard/stats", headers=officer_headers)
    assert r_dash.status_code == 200, f"OFFICER dashboard view failed: {r_dash.text}"

    # 2. Upload Dataset
    f_name = f"officer_test_{uuid.uuid4().hex[:6]}.csv"
    r_up = client.post(
        "/datasets/upload",
        headers=officer_headers,
        files={"file": (f_name, get_test_csv(), "text/csv")},
        data={"source_type": "CADASTRAL"}
    )
    assert r_up.status_code == 200, f"OFFICER upload failed: {r_up.text}"

    # 3. View Datasets
    r_ds = client.get("/datasets/", headers=officer_headers)
    assert r_ds.status_code == 200, f"OFFICER datasets view failed: {r_ds.text}"

    print("  [OK] OFFICER successfully executed permitted operational actions (view, upload).")
    test_results["test_6_officer_permitted_actions"] = "PASSED"
except Exception as e:
    print(f"  [FAIL] Test 6 failed: {e}")
    test_results["test_6_officer_permitted_actions"] = f"FAILED: {e}"


# -------------------------------------------------------------
# TEST 7: DEPARTMENT_ADMIN Can Manage Eligible Department Users (HTTP 200)
# -------------------------------------------------------------
try:
    print("\n[TEST 7] Testing DEPARTMENT_ADMIN user management within own department...")
    dept_admin_headers = {"Authorization": "Bearer test-token-dept-admin"}

    # List department users
    r_users = client.get("/admin/users", headers=dept_admin_headers)
    assert r_users.status_code == 200, f"Expected 200 on /admin/users, got {r_users.status_code}"
    users_data = r_users.json()["users"]

    # All returned users must belong to Department Admin's organization
    dept_admin_profile = TEST_USERS_STORE["department.admin@test.local"]
    for u in users_data:
        assert u["organization_id"] == dept_admin_profile["organization_id"], \
            "DEPARTMENT_ADMIN received cross-department user in list"

    # Toggle user status within same department (e.g. department.admin self or department peer)
    target_id = dept_admin_profile["id"]
    r_patch = client.patch(
        f"/admin/users/{target_id}/status",
        headers=dept_admin_headers,
        json={"is_active": True}
    )
    assert r_patch.status_code == 200, f"DEPARTMENT_ADMIN status update failed: {r_patch.text}"

    print(f"  [OK] DEPARTMENT_ADMIN successfully managed department members.")
    test_results["test_7_dept_admin_management"] = "PASSED"
except Exception as e:
    print(f"  [FAIL] Test 7 failed: {e}")
    test_results["test_7_dept_admin_management"] = f"FAILED: {e}"


# -------------------------------------------------------------
# TEST 8: Cross-Organization Management Blocked (HTTP 403)
# -------------------------------------------------------------
try:
    print("\n[TEST 8] Testing that DEPARTMENT_ADMIN cannot modify members of another organization...")
    dept_admin_headers = {"Authorization": "Bearer test-token-dept-admin"}
    # Target is officer@test.local who belongs to MUNICIPAL_CORP (different from REVENUE_DEPT)
    cross_org_user_id = TEST_USERS_STORE["officer@test.local"]["id"]

    r_blocked = client.patch(
        f"/admin/users/{cross_org_user_id}/status",
        headers=dept_admin_headers,
        json={"is_active": False}
    )
    assert r_blocked.status_code == 403, f"Expected 403 for cross-organization modification, got {r_blocked.status_code}"
    assert "another organization" in r_blocked.text.lower()

    print("  [OK] Cross-organization management strictly blocked with HTTP 403.")
    test_results["test_8_cross_org_blocked"] = "PASSED"
except Exception as e:
    print(f"  [FAIL] Test 8 failed: {e}")
    test_results["test_8_cross_org_blocked"] = f"FAILED: {e}"


# -------------------------------------------------------------
# TEST 9: Inactive Users Blocked from Operations (HTTP 403)
# -------------------------------------------------------------
try:
    print("\n[TEST 9] Testing that inactive users cannot perform protected operations...")
    inactive_headers = {"Authorization": "Bearer test-token-inactive"}

    r_dash = client.get("/dashboard/stats", headers=inactive_headers)
    assert r_dash.status_code == 403, f"Expected 403 for inactive user, got {r_dash.status_code}"
    assert "inactive" in r_dash.text.lower()

    r_up = client.post(
        "/datasets/upload",
        headers=inactive_headers,
        files={"file": ("test.csv", get_test_csv(), "text/csv")}
    )
    assert r_up.status_code == 403, f"Expected 403 for inactive user upload, got {r_up.status_code}"

    print("  [OK] Inactive users strictly blocked with HTTP 403 across all protected routes.")
    test_results["test_9_inactive_users_blocked"] = "PASSED"
except Exception as e:
    print(f"  [FAIL] Test 9 failed: {e}")
    test_results["test_9_inactive_users_blocked"] = f"FAILED: {e}"


# -------------------------------------------------------------
# TEST 10: Role / Permission Lookup Works Correctly
# -------------------------------------------------------------
try:
    print("\n[TEST 10] Testing database-driven role and permission resolution...")
    admin_headers = {"Authorization": "Bearer test-token-platform-admin"}
    r_admin = client.get("/auth/me", headers=admin_headers)
    assert r_admin.status_code == 200
    admin_data = r_admin.json()
    assert admin_data["role"] == "PLATFORM_ADMIN"
    assert len(admin_data["permissions"]) == 15, f"Expected 15 permissions for PLATFORM_ADMIN, got {len(admin_data['permissions'])}"

    viewer_headers = {"Authorization": "Bearer test-token-viewer"}
    r_viewer = client.get("/auth/me", headers=viewer_headers)
    assert r_viewer.status_code == 200
    viewer_data = r_viewer.json()
    assert viewer_data["role"] == "VIEWER"
    assert len(viewer_data["permissions"]) == 7, f"Expected 7 permissions for VIEWER, got {len(viewer_data['permissions'])}"
    assert "datasets.upload" not in viewer_data["permissions"]
    assert "analysis.run" not in viewer_data["permissions"]

    print("  [OK] Role and permission mappings accurately verified for all system tiers.")
    test_results["test_10_role_permissions_lookup"] = "PASSED"
except Exception as e:
    print(f"  [FAIL] Test 10 failed: {e}")
    test_results["test_10_role_permissions_lookup"] = f"FAILED: {e}"


# -------------------------------------------------------------
# TEST 11: Phase A Pipeline Preservation Under Authenticated Session
# -------------------------------------------------------------
try:
    print("\n[TEST 11] Testing Phase A pipeline functionality under authenticated session...")
    officer_headers = {"Authorization": "Bearer test-token-officer"}

    # 1. Dataset list
    r_datasets = client.get("/datasets/", headers=officer_headers)
    assert r_datasets.status_code == 200 and r_datasets.json()["success"] is True

    # 2. Conflict list
    r_conflicts = client.get("/conflicts/", headers=officer_headers)
    assert r_conflicts.status_code == 200 and r_conflicts.json()["success"] is True

    # 3. Harmonization list
    r_harm = client.get("/harmonization/", headers=officer_headers)
    assert r_harm.status_code == 200 and r_harm.json()["success"] is True

    # 4. Source comparison
    r_comp = client.get("/analysis/source-comparison/TEST-P101", headers=officer_headers)
    assert r_comp.status_code == 200 and r_comp.json()["success"] is True

    # 5. Analysis runs list
    r_runs = client.get("/analysis/runs", headers=officer_headers)
    assert r_runs.status_code == 200 and r_runs.json()["success"] is True

    print("  [OK] All Phase A endpoints remain 100% operational under authenticated session.")
    test_results["test_11_phase_a_preservation"] = "PASSED"
except Exception as e:
    import traceback
    print(f"  [FAIL] Test 11 failed: {e}\n{traceback.format_exc()}")
    test_results["test_11_phase_a_preservation"] = f"FAILED: {e}"


# -------------------------------------------------------------
# Summary
# -------------------------------------------------------------
print("\n" + "=" * 70)
print("PHASE B TEST SUMMARY")
print("=" * 70)
all_passed = True
for name, status in test_results.items():
    print(f"{name:35}: {status}")
    if status != "PASSED":
        all_passed = False

if all_passed:
    print("\n>>> ALL 11 PHASE B TESTS PASSED! <<<")
    sys.exit(0)
else:
    print("\n>>> SOME TESTS FAILED! <<<")
    sys.exit(1)
