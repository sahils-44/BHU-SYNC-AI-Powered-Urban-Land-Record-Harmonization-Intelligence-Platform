"""
BHU-SYNC PHASE G: WORKFLOW & TAMPER-EVIDENT SHA-256 AUDIT AUTOMATED TEST SUITE
Verifies 36 test scenarios covering Finite State Machine transitions, case management,
investigation notes, evidence linking, SHA-256 audit chaining, and immutability controls.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from fastapi.testclient import TestClient
from main import app
from services.workflow_service import (
    create_case,
    transition_case_status,
    add_case_note,
    link_case_evidence,
    get_case,
    CASES_STORE
)
from services.audit_service import (
    append_audit_log,
    verify_chain_integrity,
    get_audit_logs,
    AUDIT_LOG_LEDGER,
    GENESIS_HASH
)

client = TestClient(app)
OFFICER_HEADERS = {"Authorization": "Bearer test-token-officer"}
VIEWER_HEADERS = {"Authorization": "Bearer test-token-viewer"}

print("=" * 70)
print("BHU-SYNC PHASE G AUTOMATED VERIFICATION SUITE (36 TESTS)")
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

# 1. NEW -> UNDER_INVESTIGATION
def t1():
    c = create_case("TEST-G101", "Boundary Shift", "HIGH", "officer@test.local", "org-1", "user-1", "officer@test.local")
    res = transition_case_status(c["case_id"], "UNDER_INVESTIGATION", "user-1", "officer@test.local")
    assert res["status"] == "UNDER_INVESTIGATION"
run_test("test_1_transition_new_to_investigation", "FSM transition NEW -> UNDER_INVESTIGATION", t1)

# 2. UNDER_INVESTIGATION -> PENDING_REVIEW
def t2():
    c = create_case("TEST-G102", "Area Mismatch", "MEDIUM", "officer@test.local", "org-1", "user-1", "officer@test.local")
    transition_case_status(c["case_id"], "UNDER_INVESTIGATION", "user-1", "officer@test.local")
    res = transition_case_status(c["case_id"], "PENDING_REVIEW", "user-1", "officer@test.local")
    assert res["status"] == "PENDING_REVIEW"
run_test("test_2_transition_investigation_to_pending", "FSM transition UNDER_INVESTIGATION -> PENDING_REVIEW", t2)

# 3. PENDING_REVIEW -> RESOLVED
def t3():
    c = create_case("TEST-G103", "Owner Variation", "LOW", "officer@test.local", "org-1", "user-1", "officer@test.local")
    transition_case_status(c["case_id"], "UNDER_INVESTIGATION", "user-1", "officer@test.local")
    transition_case_status(c["case_id"], "PENDING_REVIEW", "user-1", "officer@test.local")
    res = transition_case_status(c["case_id"], "RESOLVED", "user-1", "officer@test.local")
    assert res["status"] == "RESOLVED"
run_test("test_3_transition_pending_to_resolved", "FSM transition PENDING_REVIEW -> RESOLVED", t3)

# 4. RESOLVED -> CLOSED
def t4():
    c = create_case("TEST-G104", "Centroid Deviation", "MEDIUM", "officer@test.local", "org-1", "user-1", "officer@test.local")
    transition_case_status(c["case_id"], "UNDER_INVESTIGATION", "user-1", "officer@test.local")
    transition_case_status(c["case_id"], "PENDING_REVIEW", "user-1", "officer@test.local")
    transition_case_status(c["case_id"], "RESOLVED", "user-1", "officer@test.local")
    res = transition_case_status(c["case_id"], "CLOSED", "user-1", "officer@test.local")
    assert res["status"] == "CLOSED"
run_test("test_4_transition_resolved_to_closed", "FSM transition RESOLVED -> CLOSED", t4)

# 5. NEW -> REJECTED
def t5():
    c = create_case("TEST-G105", "Spam Report", "LOW", "officer@test.local", "org-1", "user-1", "officer@test.local")
    res = transition_case_status(c["case_id"], "REJECTED", "user-1", "officer@test.local")
    assert res["status"] == "REJECTED"
run_test("test_5_transition_new_to_rejected", "FSM transition NEW -> REJECTED", t5)

# 6. Invalid transition NEW -> RESOLVED blocked
def t6():
    c = create_case("TEST-G106", "Skipping", "HIGH", "officer@test.local", "org-1", "user-1", "officer@test.local")
    try:
        transition_case_status(c["case_id"], "RESOLVED", "user-1", "officer@test.local")
        assert False, "Should raise ValueError"
    except ValueError:
        pass
run_test("test_6_invalid_new_to_resolved_blocked", "Reject invalid transition NEW -> RESOLVED", t6)

# 7. Transition from CLOSED blocked
def t7():
    c = create_case("TEST-G107", "Terminal", "LOW", "officer@test.local", "org-1", "user-1", "officer@test.local")
    transition_case_status(c["case_id"], "UNDER_INVESTIGATION", "user-1", "officer@test.local")
    transition_case_status(c["case_id"], "PENDING_REVIEW", "user-1", "officer@test.local")
    transition_case_status(c["case_id"], "RESOLVED", "user-1", "officer@test.local")
    transition_case_status(c["case_id"], "CLOSED", "user-1", "officer@test.local")
    try:
        transition_case_status(c["case_id"], "UNDER_INVESTIGATION", "user-1", "officer@test.local")
        assert False, "Should raise ValueError from closed"
    except ValueError:
        pass
run_test("test_7_transition_from_closed_blocked", "Reject transition from terminal CLOSED status", t7)

# 8. Transition from REJECTED blocked
def t8():
    c = create_case("TEST-G108", "Rejected", "LOW", "officer@test.local", "org-1", "user-1", "officer@test.local")
    transition_case_status(c["case_id"], "REJECTED", "user-1", "officer@test.local")
    try:
        transition_case_status(c["case_id"], "PENDING_REVIEW", "user-1", "officer@test.local")
        assert False, "Should raise ValueError from rejected"
    except ValueError:
        pass
run_test("test_8_transition_from_rejected_blocked", "Reject transition from terminal REJECTED status", t8)

# 9. Case initialized to NEW
def t9():
    c = create_case("TEST-G109", "Initialization", "MEDIUM", "officer@test.local", "org-1", "user-1", "officer@test.local")
    assert c["status"] == "NEW"
run_test("test_9_case_initialized_to_new", "Case initialized in NEW state", t9)

# 10. Updated timestamp and reason
def t10():
    c = create_case("TEST-G110", "Timestamp test", "LOW", "officer@test.local", "org-1", "user-1", "officer@test.local")
    res = transition_case_status(c["case_id"], "UNDER_INVESTIGATION", "user-1", "officer@test.local", reason="Field inspection scheduled")
    assert "T" in res["updated_at"]
run_test("test_10_updated_timestamp_and_reason", "Update timestamp and record transition reason", t10)

# 11. Append note
def t11():
    c = create_case("TEST-G111", "Notes test", "LOW", "officer@test.local", "org-1", "user-1", "officer@test.local")
    note = add_case_note(c["case_id"], "Inspected field boundaries.", "user-1", "officer@test.local")
    assert note["text"] == "Inspected field boundaries."
run_test("test_11_append_case_note", "Append officer investigation note", t11)

# 12. Empty note rejected
def t12():
    c = create_case("TEST-G112", "Empty note test", "LOW", "officer@test.local", "org-1", "user-1", "officer@test.local")
    r = client.post(f"/workflow/cases/{c['case_id']}/notes", json={"text": "   "}, headers=OFFICER_HEADERS)
    assert r.status_code == 400
run_test("test_12_empty_note_rejected", "Reject empty note with HTTP 400", t12)

# 13. Multiple notes preserved
def t13():
    c = create_case("TEST-G113", "Multi note test", "LOW", "officer@test.local", "org-1", "user-1", "officer@test.local")
    add_case_note(c["case_id"], "Note 1", "user-1", "officer@test.local")
    add_case_note(c["case_id"], "Note 2", "user-1", "officer@test.local")
    fetched = get_case(c["case_id"])
    assert len(fetched["notes"]) == 2
run_test("test_13_multiple_notes_preserved", "Multiple notes preserved in sequence", t13)

# 14. Link survey map evidence
def t14():
    c = create_case("TEST-G114", "Evidence test", "LOW", "officer@test.local", "org-1", "user-1", "officer@test.local")
    ev = link_case_evidence(c["case_id"], "Cadastral Map", "SURVEY_MAP", "MAP-902", "user-1", "officer@test.local")
    assert ev["evidence_type"] == "SURVEY_MAP"
run_test("test_14_link_survey_map_evidence", "Link survey map evidence", t14)

# 15. Link registry deed evidence
def t15():
    c = create_case("TEST-G115", "Deed evidence test", "LOW", "officer@test.local", "org-1", "user-1", "officer@test.local")
    ev = link_case_evidence(c["case_id"], "Sale Deed", "REGISTRY_DEED", "DEED-552", "user-1", "officer@test.local")
    assert ev["evidence_type"] == "REGISTRY_DEED"
run_test("test_15_link_registry_deed_evidence", "Link registry deed evidence", t15)

# 16. Case details returns notes and evidence
def t16():
    r = client.get("/workflow/cases/CASE-2024-001", headers=OFFICER_HEADERS)
    assert r.status_code == 200
    data = r.json()["case"]
    assert len(data.get("notes", [])) > 0 and len(data.get("evidence", [])) > 0
run_test("test_16_case_details_notes_evidence", "Retrieve case with notes and evidence", t16)

# 17. Case assignment
def t17():
    c = create_case("TEST-G117", "Assign test", "HIGH", "surveyor@bhusync.gov.in", "org-1", "user-1", "officer@test.local")
    assert c["assigned_to"] == "surveyor@bhusync.gov.in"
run_test("test_17_case_assignment", "Officer case assignment", t17)

# 18. Workflow stats report
def t18():
    r = client.get("/workflow/dashboard/stats", headers=OFFICER_HEADERS)
    assert r.status_code == 200
    stats = r.json()
    assert stats["total_cases"] >= 2
    assert "under_investigation" in stats
run_test("test_18_workflow_stats_report", "Workflow dashboard throughput stats", t18)

# 19. Genesis hash baseline
def t19():
    assert len(GENESIS_HASH) == 64
    assert GENESIS_HASH.startswith("0000")
run_test("test_19_genesis_hash_baseline", "Genesis hash baseline initialized", t19)

# 20. Audit entry SHA-256 hash length
def t20():
    entry = append_audit_log("user-1", "officer@test.local", "TEST_ACTION", "PARCEL", "P-101")
    assert len(entry["hash"]) == 64
    assert len(entry["previous_hash"]) == 64
run_test("test_20_audit_sha256_hash_length", "Cryptographic 64-character SHA-256 hash", t20)

# 21. Previous hash chaining
def t21():
    e1 = append_audit_log("user-1", "officer@test.local", "CHAIN_1", "PARCEL", "P-1")
    e2 = append_audit_log("user-1", "officer@test.local", "CHAIN_2", "PARCEL", "P-2")
    assert e2["previous_hash"] == e1["hash"]
run_test("test_21_previous_hash_chaining", "Current previous_hash links to preceding entry hash", t21)

# 22. Audit verify chain passes
def t22():
    valid, count, msg = verify_chain_integrity()
    assert valid is True
    assert count > 0
run_test("test_22_audit_verify_chain_passes", "Cryptographic verification of untampered chain", t22)

# 23. Tampering causes verify failure
def t23():
    orig = AUDIT_LOG_LEDGER[-1]["action"]
    AUDIT_LOG_LEDGER[-1]["action"] = "TAMPERED_ACTION"
    valid, _, msg = verify_chain_integrity()
    assert valid is False
    assert "Tampered entry detected" in msg
    # Restore
    AUDIT_LOG_LEDGER[-1]["action"] = orig
run_test("test_23_tampering_causes_verify_failure", "Tampered payload triggers verification failure", t23)

# 24. Restoring restores verify chain
def t24():
    valid, _, _ = verify_chain_integrity()
    assert valid is True
run_test("test_24_restoring_restores_verify_chain", "Restoring entry restores valid cryptographic chain", t24)

# 25. Case creation triggers audit
def t25():
    count_before = len(AUDIT_LOG_LEDGER)
    create_case("TEST-G125", "Audit creation", "LOW", "officer@test.local", "org-1", "user-1", "officer@test.local")
    assert len(AUDIT_LOG_LEDGER) == count_before + 1
    assert AUDIT_LOG_LEDGER[-1]["action"] == "CASE_CREATED"
run_test("test_25_case_creation_triggers_audit", "Automated audit entry on case creation", t25)

# 26. Status transition triggers audit
def t26():
    c = create_case("TEST-G126", "Audit transition", "LOW", "officer@test.local", "org-1", "user-1", "officer@test.local")
    count_before = len(AUDIT_LOG_LEDGER)
    transition_case_status(c["case_id"], "UNDER_INVESTIGATION", "user-1", "officer@test.local")
    assert len(AUDIT_LOG_LEDGER) == count_before + 1
    assert AUDIT_LOG_LEDGER[-1]["action"] == "CASE_STATUS_TRANSITION"
run_test("test_26_status_transition_triggers_audit", "Automated audit entry on status transition", t26)

# 27. Note triggers audit
def t27():
    c = create_case("TEST-G127", "Audit note", "LOW", "officer@test.local", "org-1", "user-1", "officer@test.local")
    count_before = len(AUDIT_LOG_LEDGER)
    add_case_note(c["case_id"], "Audit test note", "user-1", "officer@test.local")
    assert len(AUDIT_LOG_LEDGER) == count_before + 1
    assert AUDIT_LOG_LEDGER[-1]["action"] == "CASE_NOTE_ADDED"
run_test("test_27_note_triggers_audit", "Automated audit entry on note addition", t27)

# 28. Evidence triggers audit
def t28():
    c = create_case("TEST-G128", "Audit evidence", "LOW", "officer@test.local", "org-1", "user-1", "officer@test.local")
    count_before = len(AUDIT_LOG_LEDGER)
    link_case_evidence(c["case_id"], "Audit Map", "MAP", "REF-1", "user-1", "officer@test.local")
    assert len(AUDIT_LOG_LEDGER) == count_before + 1
    assert AUDIT_LOG_LEDGER[-1]["action"] == "CASE_EVIDENCE_LINKED"
run_test("test_28_evidence_triggers_audit", "Automated audit entry on evidence linking", t28)

# 29. REST cases unauthenticated
def t29():
    r = client.get("/workflow/cases")
    assert r.status_code == 401
run_test("test_29_rest_cases_unauthenticated", "Unauthenticated GET /workflow/cases rejected (401)", t29)

# 30. REST cases authenticated
def t30():
    r = client.get("/workflow/cases", headers=OFFICER_HEADERS)
    assert r.status_code == 200
    assert r.json().get("success") is True
run_test("test_30_rest_cases_authenticated", "Authenticated GET /workflow/cases returns list", t30)

# 31. REST create case without permission (Viewer)
def t31():
    r = client.post(
        "/workflow/cases",
        json={"parcel_id": "P-99", "title": "Unauthorized"},
        headers=VIEWER_HEADERS
    )
    assert r.status_code == 403
run_test("test_31_rest_create_case_viewer_forbidden", "Viewer cannot create workflow case (403)", t31)

# 32. REST create case with permission (Officer)
def t32():
    r = client.post(
        "/workflow/cases",
        json={"parcel_id": "DEMO-KPG-1004", "title": "Area Conflict Case", "priority": "HIGH"},
        headers=OFFICER_HEADERS
    )
    assert r.status_code == 200
    assert r.json().get("success") is True
run_test("test_32_rest_create_case_officer_success", "Officer creates workflow case (200)", t32)

# 33. REST valid transition
def t33():
    c = create_case("TEST-G133", "REST valid", "LOW", "officer@test.local", "org-1", "user-1", "officer@test.local")
    r = client.patch(
        f"/workflow/cases/{c['case_id']}/status",
        json={"status": "UNDER_INVESTIGATION", "reason": "Officer started verification"},
        headers=OFFICER_HEADERS
    )
    assert r.status_code == 200
    assert r.json()["case"]["status"] == "UNDER_INVESTIGATION"
run_test("test_33_rest_valid_transition", "PATCH valid status transition returns 200", t33)

# 34. REST invalid transition
def t34():
    c = create_case("TEST-G134", "REST invalid", "LOW", "officer@test.local", "org-1", "user-1", "officer@test.local")
    r = client.patch(
        f"/workflow/cases/{c['case_id']}/status",
        json={"status": "RESOLVED"},
        headers=OFFICER_HEADERS
    )
    assert r.status_code == 400
run_test("test_34_rest_invalid_transition", "PATCH invalid status transition returns 400", t34)

# 35. REST audit logs authenticated
def t35():
    r = client.get("/audit/logs", headers=OFFICER_HEADERS)
    assert r.status_code == 200
    assert r.json().get("count") > 0
run_test("test_35_rest_audit_logs_authenticated", "GET /audit/logs returns verified trail", t35)

# 36. Mutating audit logs rejected
def t36():
    r1 = client.post("/audit/logs", json={"action": "ILLEGAL"}, headers=OFFICER_HEADERS)
    assert r1.status_code == 405
    r2 = client.delete("/audit/logs", headers=OFFICER_HEADERS)
    assert r2.status_code == 405
run_test("test_36_mutating_audit_logs_rejected", "POST/DELETE /audit/logs returns 405 Method Not Allowed", t36)

# Summary
print("\n" + "=" * 70)
print("PHASE G TEST SUMMARY")
print("=" * 70)
all_passed = True
for name, status in test_results.items():
    print(f"{name:45}: {status}")
    if status != "PASSED":
        all_passed = False

if all_passed:
    print("\n>>> ALL 36 PHASE G TESTS PASSED! <<<")
    sys.exit(0)
else:
    print("\n>>> SOME TESTS FAILED! <<<")
    sys.exit(1)
