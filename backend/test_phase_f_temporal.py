"""
BHU-SYNC PHASE F: TEMPORAL & CHANGE INTELLIGENCE AUTOMATED TEST SUITE
Verifies 34 test scenarios covering 17 change event types, before/after snapshots,
run-to-run deltas, chronological parcel lineage, and REST endpoints.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from fastapi.testclient import TestClient
from main import app
from services.temporal_service import (
    CHANGE_EVENT_TYPES,
    record_temporal_change,
    get_parcel_history,
    compare_runs_detailed,
    PARCEL_TIMELINE_STORE
)

client = TestClient(app)
AUTH_HEADERS = {"Authorization": "Bearer test-token-officer"}

print("=" * 70)
print("BHU-SYNC PHASE F AUTOMATED VERIFICATION SUITE (34 TESTS)")
print("=" * 70)

test_results = {}

def run_test(test_id, name, func):
    try:
        print(f"\n[{test_id.upper()}] Testing {name}...")
        func()
        print(f"  [OK] {name} passed.")
        test_results[test_id] = "PASSED"
    except Exception as e:
        import traceback
        print(f"  [FAIL] {name} failed: {e}\n{traceback.format_exc()}")
        test_results[test_id] = f"FAILED: {e}"

# 1-17: Verifying all 17 event types
EXPECTED_17_TYPES = [
    "PARCEL_CREATED", "PARCEL_SPLIT", "PARCEL_MERGED", "OWNER_TRANSFERRED",
    "AREA_EXPANDED", "AREA_SHRUNK", "BOUNDARY_ALTERED", "CENTROID_SHIFTED",
    "LAND_USE_CHANGED", "CONFLICT_DETECTED", "CONFLICT_RESOLVED", "MORTGAGE_ADDED",
    "MORTGAGE_DISCHARGED", "TAX_STATUS_UPDATED", "BUILDING_ADDED", "VERSION_BUMPED",
    "MANUAL_OVERRIDE"
]

for idx, ev_type in enumerate(EXPECTED_17_TYPES, start=1):
    def make_tester(t):
        def tester():
            assert t in CHANGE_EVENT_TYPES, f"{t} not in CHANGE_EVENT_TYPES"
        return tester
    run_test(f"test_{idx}_event_type_{ev_type.lower()}", f"Event type: {ev_type}", make_tester(ev_type))

# 18. Record change success
def t18():
    evt = record_temporal_change("TEST-F101", "PARCEL_CREATED", "Officer A", "Initial survey", None, {"area": 1200})
    assert evt["event_type"] == "PARCEL_CREATED"
    assert evt["after"] == {"area": 1200}
run_test("test_18_record_temporal_change_success", "Record valid change event", t18)

# 19. Record invalid event type rejected
def t19():
    try:
        record_temporal_change("TEST-F101", "INVALID_UNKNOWN_EVENT", "Officer A", "Desc")
        assert False, "Should raise ValueError"
    except ValueError:
        pass
run_test("test_19_record_invalid_event_type_rejected", "Reject invalid change event type", t19)

# 20. Event ID generation
def t20():
    evt = record_temporal_change("TEST-F102", "OWNER_TRANSFERRED", "Registry", "Deed 45", {"owner": "A"}, {"owner": "B"})
    assert evt["event_id"].startswith("EVT-")
run_test("test_20_event_id_generation_format", "Event ID prefix and format", t20)

# 21. ISO timestamp
def t21():
    evt = record_temporal_change("TEST-F103", "CONFLICT_DETECTED", "Engine", "Discrepancy")
    assert "T" in evt["timestamp"] and ("Z" in evt["timestamp"] or "+00:00" in evt["timestamp"] or ":" in evt["timestamp"])
run_test("test_21_iso_timestamp_adherence", "ISO 8601 UTC timestamp format", t21)

# 22. Actor attribution
def t22():
    evt = record_temporal_change("TEST-F104", "MANUAL_OVERRIDE", "officer@test.local", "Override")
    assert evt["actor"] == "officer@test.local"
run_test("test_22_actor_attribution", "Preserve actor identity in change event", t22)

# 23. Chronological sorting
def t23():
    history = get_parcel_history("DEMO-KPG-1004")
    assert len(history) >= 2
    ts = [h["timestamp"] for h in history]
    assert ts == sorted(ts)
run_test("test_23_chronological_sorting", "Parcel history returned in chronological order", t23)

# 24. Before after delta tracking
def t24():
    history = get_parcel_history("DEMO-KPG-1004")
    expanded_evt = next((e for e in history if e["event_type"] == "AREA_EXPANDED"), None)
    assert expanded_evt is not None
    assert expanded_evt["before"] is not None and expanded_evt["after"] is not None
run_test("test_24_before_after_delta_tracking", "Before and after snapshot tracking", t24)

# 25. Compare runs detailed
def t25():
    res = compare_runs_detailed("run-1", "run-2")
    assert "summary" in res and "deltas" in res
    assert res["summary"]["total_parcels_compared"] > 0
run_test("test_25_compare_runs_detailed_summary", "Run-to-run summary metrics computed", t25)

# 26. Score changes tracking
def t26():
    res = compare_runs_detailed("run-1", "run-2")
    assert res["summary"]["score_improved_count"] >= 1
run_test("test_26_score_changes_tracking", "Score improvements tracked across runs", t26)

# 27. Resolved conflicts tracking
def t27():
    res = compare_runs_detailed("run-1", "run-2")
    assert res["summary"]["conflicts_resolved"] >= 1
run_test("test_27_resolved_conflicts_tracking", "Conflict resolutions tracked across runs", t27)

# 28. Net harmonization gain
def t28():
    res = compare_runs_detailed("run-1", "run-2")
    assert "net_harmonization_gain_pct" in res["summary"]
run_test("test_28_net_harmonization_gain", "Net percentage harmonization progress computed", t28)

# 29. Run delta reasons
def t29():
    res = compare_runs_detailed("run-1", "run-2")
    d = res["deltas"][0]
    assert "reason" in d and "from_score" in d and "to_score" in d
run_test("test_29_run_delta_reasons", "Lineage reason explanation for each parcel change", t29)

# 30. REST history unauthenticated
def t30():
    r = client.get("/temporal/parcel/DEMO-KPG-1001/history")
    assert r.status_code == 401
run_test("test_30_rest_history_unauthenticated", "Unauthenticated GET /temporal/parcel/history rejected (401)", t30)

# 31. REST history authenticated
def t31():
    r = client.get("/temporal/parcel/DEMO-KPG-1001/history", headers=AUTH_HEADERS)
    assert r.status_code == 200
    data = r.json()
    assert data.get("success") is True
    assert len(data.get("timeline", [])) > 0
run_test("test_31_rest_history_authenticated", "Authenticated GET /temporal/parcel/history returns timeline", t31)

# 32. REST compare runs missing params
def t32():
    r = client.get("/temporal/compare/runs", headers=AUTH_HEADERS)
    assert r.status_code in [400, 422]
run_test("test_32_rest_compare_runs_missing_params", "Missing query parameters rejected with 400/422", t32)

# 33. REST compare runs authenticated
def t33():
    r = client.get("/temporal/compare/runs?from_run_id=run-1&to_run_id=run-2", headers=AUTH_HEADERS)
    assert r.status_code == 200
    assert r.json().get("success") is True
run_test("test_33_rest_compare_runs_authenticated", "GET /temporal/compare/runs returns structured delta", t33)

# 34. REST temporal summary
def t34():
    r = client.get("/temporal/summary", headers=AUTH_HEADERS)
    assert r.status_code == 200
    assert r.json().get("success") is True
run_test("test_34_rest_temporal_summary", "GET /temporal/summary returns macro temporal trends", t34)

# Summary
print("\n" + "=" * 70)
print("PHASE F TEST SUMMARY")
print("=" * 70)
all_passed = True
for name, status in test_results.items():
    print(f"{name:45}: {status}")
    if status != "PASSED":
        all_passed = False

if all_passed:
    print("\n>>> ALL 34 PHASE F TESTS PASSED! <<<")
    sys.exit(0)
else:
    print("\n>>> SOME TESTS FAILED! <<<")
    sys.exit(1)
