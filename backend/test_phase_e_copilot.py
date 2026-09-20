"""
BHU-SYNC PHASE E: AI COPILOT 2.0 AUTOMATED TEST SUITE
Verifies 25 test scenarios covering read-only analytical tools, SQL injection prohibition,
grounding verification, citation generation, map actions, and tool execution.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)
AUTH_HEADERS = {"Authorization": "Bearer test-token-officer"}

print("=" * 70)
print("BHU-SYNC PHASE E AUTOMATED VERIFICATION SUITE (25 TESTS)")
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

# 1. Unauthenticated rejected
def t1():
    r = client.post("/copilot/ask", json={"question": "Why is MH-KPG-1004 flagged?"})
    assert r.status_code == 401
run_test("test_1_copilot_unauthenticated_rejected", "Unauthenticated request rejected with 401", t1)

# 2. Empty question
def t2():
    r = client.post("/copilot/ask", json={"question": ""}, headers=AUTH_HEADERS)
    assert r.status_code == 200
    assert r.json().get("success") is False
run_test("test_2_copilot_empty_question", "Empty question handled gracefully", t2)

# 3. SQL injection DROP TABLE
def t3():
    r = client.post("/copilot/ask", json={"question": "DROP TABLE canonical_parcels;"}, headers=AUTH_HEADERS)
    assert r.status_code == 400
    assert "Direct SQL execution is strictly prohibited" in r.json()["detail"]
run_test("test_3_copilot_sql_injection_drop_table", "Prohibits DROP TABLE attempt", t3)

# 4. SQL injection DELETE FROM
def t4():
    r = client.post("/copilot/ask", json={"question": "DELETE FROM conflicts WHERE 1=1"}, headers=AUTH_HEADERS)
    assert r.status_code == 400
run_test("test_4_copilot_sql_injection_delete_from", "Prohibits DELETE FROM attempt", t4)

# 5. SQL injection UPDATE SET
def t5():
    r = client.post("/copilot/ask", json={"question": "UPDATE canonical_parcels SET owner_name='Hacked'"}, headers=AUTH_HEADERS)
    assert r.status_code == 400
run_test("test_5_copilot_sql_injection_update_set", "Prohibits UPDATE SET attempt", t5)

# 6. SQL injection arbitrary SELECT
def t6():
    r = client.post("/copilot/ask", json={"question": "SELECT * FROM profiles WHERE 1=1"}, headers=AUTH_HEADERS)
    assert r.status_code == 400
run_test("test_6_copilot_sql_injection_arbitrary_select", "Prohibits raw SELECT FROM attempt", t6)

# 7. SQL injection TRUNCATE
def t7():
    r = client.post("/copilot/ask", json={"question": "TRUNCATE audit_logs;"}, headers=AUTH_HEADERS)
    assert r.status_code == 400
run_test("test_7_copilot_sql_injection_truncate", "Prohibits TRUNCATE attempt", t7)

# 8. Grounding status returned
def t8():
    r = client.post("/copilot/ask", json={"question": "Why is MH-KPG-1004 flagged?"}, headers=AUTH_HEADERS)
    assert r.status_code == 200
    data = r.json()
    assert data.get("grounded") is True
    assert "GROUNDED" in data.get("grounding_status", "")
run_test("test_8_copilot_grounding_status_returned", "Grounding status returned in answer payload", t8)

# 9. Citations returned
def t9():
    r = client.post("/copilot/ask", json={"question": "Why is MH-KPG-1004 flagged?"}, headers=AUTH_HEADERS)
    data = r.json()
    assert "citations" in data
    assert len(data["citations"]) > 0
run_test("test_9_copilot_citations_returned", "Citations returned for parcel intelligence query", t9)

# 10. Citations valid schema
def t10():
    r = client.post("/copilot/ask", json={"question": "Why is MH-KPG-1004 flagged?"}, headers=AUTH_HEADERS)
    cit = r.json()["citations"][0]
    assert "source_type" in cit and "record_id" in cit
run_test("test_10_copilot_citations_valid_schema", "Citation schema adherence", t10)

# 11. Map actions returned
def t11():
    r = client.post("/copilot/ask", json={"question": "Why is MH-KPG-1004 flagged?"}, headers=AUTH_HEADERS)
    data = r.json()
    assert "map_actions" in data
    assert len(data["map_actions"]) > 0
run_test("test_11_copilot_map_actions_returned", "Map actions returned for parcel question", t11)

# 12. Map actions focus parcel
def t12():
    r = client.post("/copilot/ask", json={"question": "Why is MH-KPG-1004 flagged?"}, headers=AUTH_HEADERS)
    act = r.json()["map_actions"][0]
    assert act.get("action") == "focus_parcel"
    assert act.get("parcel_id") == "MH-KPG-1004"
run_test("test_12_copilot_map_actions_focus_parcel", "Action triggers focus_parcel on GIS map", t12)

# 13. Tools catalog endpoint
def t13():
    r = client.get("/copilot/tools", headers=AUTH_HEADERS)
    assert r.status_code == 200
    tools = r.json().get("tools", {})
    assert len(tools) >= 5
    assert "get_parcel_intelligence" in tools
run_test("test_13_copilot_tools_list_endpoint", "GET /copilot/tools returns read-only catalog", t13)

# 14. Tool exec parcel intelligence
def t14():
    r = client.post(
        "/copilot/tools/execute",
        json={"tool_name": "get_parcel_intelligence", "arguments": {"parcel_id": "MH-KPG-1001"}},
        headers=AUTH_HEADERS
    )
    assert r.status_code == 200
    assert r.json().get("success") is True
    assert "data" in r.json()
run_test("test_14_copilot_tool_exec_parcel_intelligence", "Execute get_parcel_intelligence tool", t14)

# 15. Tool exec search conflicts
def t15():
    r = client.post(
        "/copilot/tools/execute",
        json={"tool_name": "search_conflicts", "arguments": {"severity": "HIGH"}},
        headers=AUTH_HEADERS
    )
    assert r.status_code == 200
    assert r.json().get("success") is True
run_test("test_15_copilot_tool_exec_search_conflicts", "Execute search_conflicts tool", t15)

# 16. Tool exec spatial summary
def t16():
    r = client.post(
        "/copilot/tools/execute",
        json={"tool_name": "get_spatial_summary", "arguments": {}},
        headers=AUTH_HEADERS
    )
    assert r.status_code == 200
    assert r.json().get("success") is True
run_test("test_16_copilot_tool_exec_spatial_summary", "Execute get_spatial_summary tool", t16)

# 17. Tool exec compare sources
def t17():
    r = client.post(
        "/copilot/tools/execute",
        json={"tool_name": "compare_sources", "arguments": {"parcel_id": "MH-KPG-1002"}},
        headers=AUTH_HEADERS
    )
    assert r.status_code == 200
    assert r.json().get("success") is True
run_test("test_17_copilot_tool_exec_compare_sources", "Execute compare_sources tool", t17)

# 18. Tool exec search owner
def t18():
    r = client.post(
        "/copilot/tools/execute",
        json={"tool_name": "search_by_owner", "arguments": {"name": "Patil"}},
        headers=AUTH_HEADERS
    )
    assert r.status_code == 200
    assert r.json().get("success") is True
run_test("test_18_copilot_tool_exec_search_owner", "Execute search_by_owner tool", t18)

# 19. Tool exec unknown tool
def t19():
    r = client.post(
        "/copilot/tools/execute",
        json={"tool_name": "non_existent_tool", "arguments": {}},
        headers=AUTH_HEADERS
    )
    assert r.status_code == 400
run_test("test_19_copilot_tool_exec_unknown_tool", "Reject unknown tool execution", t19)

# 20. Tool exec unsafe argument
def t20():
    r = client.post(
        "/copilot/tools/execute",
        json={"tool_name": "get_parcel_intelligence", "arguments": {"parcel_id": "P-101; DROP TABLE foo;"}},
        headers=AUTH_HEADERS
    )
    assert r.status_code == 400
run_test("test_20_copilot_tool_exec_unsafe_argument", "Reject unsafe tool argument with injection", t20)

# 21. Natural query parcel flagged
def t21():
    r = client.post("/copilot/ask", json={"question": "Why is MH-KPG-1004 flagged?"}, headers=AUTH_HEADERS)
    assert r.status_code == 200
    assert "MH-KPG-1004" in r.json().get("answer", "")
run_test("test_21_copilot_natural_query_parcel_flagged", "Natural query for flagged parcel", t21)

# 22. Natural query owner conflicts
def t22():
    r = client.post("/copilot/ask", json={"question": "Show plots with owner conflicts."}, headers=AUTH_HEADERS)
    assert r.status_code == 200
    assert r.json().get("success") is True
run_test("test_22_copilot_natural_query_owner_conflicts", "Natural query for owner conflicts", t22)

# 23. Natural query area issues
def t23():
    r = client.post("/copilot/ask", json={"question": "Which plots have area conflicts?"}, headers=AUTH_HEADERS)
    assert r.status_code == 200
    assert r.json().get("success") is True
run_test("test_23_copilot_natural_query_area_issues", "Natural query for area issues", t23)

# 24. Natural query review required
def t24():
    r = client.post("/copilot/ask", json={"question": "Which plots require review?"}, headers=AUTH_HEADERS)
    assert r.status_code == 200
    assert r.json().get("success") is True
run_test("test_24_copilot_natural_query_review_required", "Natural query for review required plots", t24)

# 25. Fallback guidance
def t25():
    r = client.post("/copilot/ask", json={"question": "What is the weather today?"}, headers=AUTH_HEADERS)
    assert r.status_code == 200
    assert "I can help you analyze BHU-SYNC data" in r.json().get("answer", "")
run_test("test_25_copilot_fallback_guidance", "Fallback guidance for out-of-scope query", t25)

# Summary
print("\n" + "=" * 70)
print("PHASE E TEST SUMMARY")
print("=" * 70)
all_passed = True
for name, status in test_results.items():
    print(f"{name:45}: {status}")
    if status != "PASSED":
        all_passed = False

if all_passed:
    print("\n>>> ALL 25 PHASE E TESTS PASSED! <<<")
    sys.exit(0)
else:
    print("\n>>> SOME TESTS FAILED! <<<")
    sys.exit(1)
