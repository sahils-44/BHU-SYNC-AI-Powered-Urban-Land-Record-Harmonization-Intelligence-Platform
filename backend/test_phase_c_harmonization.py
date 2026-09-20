"""
BHU-SYNC PHASE C: MULTI-SOURCE HARMONIZATION AUTOMATED TEST SUITE
Verifies 25 test scenarios covering 10 source types, 7-level matching hierarchy,
normalizer utilities, multi-source conflict detection, provenance, and dynamic scoring.
"""

import os
import sys

# Add backend directory to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from services.matching_config import (
    SUPPORTED_SOURCES,
    SOURCE_AUTHORITY,
    MATCHING_HIERARCHY,
    SCORE_THRESHOLDS,
    get_harmonization_status,
    get_status_color
)
from services.normalizer import (
    normalize_owner_name_advanced,
    calculate_soundex,
    string_similarity,
    convert_area_to_sqm,
    parse_coordinates
)
from services.conflict_engine import detect_multi_source_conflicts
from services.harmonization_service import calculate_multi_source_harmonization

print("=" * 70)
print("BHU-SYNC PHASE C AUTOMATED VERIFICATION SUITE (25 TESTS)")
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

# 1. Supported Sources
def t1():
    assert len(SUPPORTED_SOURCES) == 10, f"Expected 10 sources, got {len(SUPPORTED_SOURCES)}"
    expected = {"CADASTRAL", "MUNICIPAL", "REGISTRY", "SURVEY_OF_INDIA", "UTILITY_WATER", "UTILITY_ELECTRICITY", "BUILDING_PERMIT", "BANK_MORTGAGE", "TAX_ASSESSMENT", "SATELLITE_IMAGERY"}
    assert set(SUPPORTED_SOURCES) == expected
run_test("test_1_supported_sources_count", "10 registered government sources", t1)

# 2. Authority weights boundary
def t2():
    w = SOURCE_AUTHORITY["boundary"]
    assert round(sum(w.values()), 2) == 1.00
    assert w["CADASTRAL"] == 0.45 and w["SURVEY_OF_INDIA"] == 0.35
run_test("test_2_authority_weights_boundary", "Boundary authority weights sum to 1.0", t2)

# 3. Authority weights ownership
def t3():
    w = SOURCE_AUTHORITY["ownership"]
    assert round(sum(w.values()), 2) == 1.00
    assert w["REGISTRY"] == 0.50
run_test("test_3_authority_weights_ownership", "Ownership authority weights sum to 1.0", t3)

# 4. Authority weights structure
def t4():
    w = SOURCE_AUTHORITY["built_structure"]
    assert round(sum(w.values()), 2) == 1.00
    assert w["MUNICIPAL"] == 0.45
run_test("test_4_authority_weights_structure", "Structure authority weights sum to 1.0", t4)

# 5. Authority weights encumbrance
def t5():
    w = SOURCE_AUTHORITY["encumbrance"]
    assert round(sum(w.values()), 2) == 1.00
    assert w["BANK_MORTGAGE"] == 0.60
run_test("test_5_authority_weights_encumbrance", "Encumbrance authority weights sum to 1.0", t5)

# 6. Hierarchy levels
def t6():
    assert len(MATCHING_HIERARCHY) == 7
    levels = [h["level"] for h in MATCHING_HIERARCHY]
    assert levels == [1, 2, 3, 4, 5, 6, 7]
run_test("test_6_matching_hierarchy_levels", "7-level identity resolution hierarchy", t6)

# 7. Normalizer honorific stripping
def t7():
    res = normalize_owner_name_advanced("Shri Ramesh Patel")
    assert res == "ramesh patel", f"Got: {res}"
run_test("test_7_owner_name_honorific_stripping", "Honorific stripping", t7)

# 8. Normalizer noise cleaning
def t8():
    res = normalize_owner_name_advanced("Smt. Sunita A. Sharma (W/o Amit)")
    assert "sunita" in res and "sharma" in res
run_test("test_8_owner_name_noise_cleaning", "Punctuation & parenthetical noise cleaning", t8)

# 9. Phonetic Soundex
def t9():
    code1 = calculate_soundex("Patel")
    code2 = calculate_soundex("Patil")
    assert code1 == code2 == "P340", f"Expected P340, got {code1}, {code2}"
run_test("test_9_phonetic_soundex_matching", "Phonetic Soundex encoding", t9)

# 10. String similarity exact
def t10():
    assert string_similarity("ramesh patel", "ramesh patel") == 1.0
run_test("test_10_string_similarity_exact", "Exact string similarity = 1.0", t10)

# 11. String similarity fuzzy
def t11():
    sim = string_similarity("suresh patil", "suresh p")
    assert sim >= 0.70, f"Expected >= 0.70, got {sim}"
run_test("test_11_string_similarity_fuzzy", "Fuzzy name abbreviation similarity", t11)

# 12. Area conversion sqft
def t12():
    sqm = convert_area_to_sqm(10763.9, "sqft")
    assert 990.0 <= sqm <= 1010.0, f"Got: {sqm}"
run_test("test_12_area_unit_conversion_sqft", "Area conversion from sqft to sqm", t12)

# 13. Area conversion guntha
def t13():
    sqm = convert_area_to_sqm(10.0, "guntha")
    assert 1010.0 <= sqm <= 1013.0, f"Got: {sqm}"
run_test("test_13_area_unit_conversion_guntha", "Area conversion from guntha to sqm", t13)

# 14. Area conversion acre
def t14():
    sqm = convert_area_to_sqm(1.0, "acre")
    assert 4040.0 <= sqm <= 4050.0, f"Got: {sqm}"
run_test("test_14_area_unit_conversion_acre", "Area conversion from acre to sqm", t14)

# 15. Area conversion hectare
def t15():
    sqm = convert_area_to_sqm(1.0, "hectare")
    assert sqm == 10000.0, f"Got: {sqm}"
run_test("test_15_area_unit_conversion_hectare", "Area conversion from hectare to sqm", t15)

# 16. Coordinate parsing valid
def t16():
    lat, lng = parse_coordinates("19.0760", "72.8777")
    assert lat == 19.076 and lng == 72.8777
run_test("test_16_coordinate_parsing_valid", "Valid coordinate parsing", t16)

# 17. Coordinate parsing invalid
def t17():
    lat, lng = parse_coordinates("999.0", "72.8777")
    assert lat is None and lng is None
run_test("test_17_coordinate_parsing_invalid", "Invalid coordinate rejection", t17)

# 18. Multi-source missing municipal
def t18():
    data = {"CADASTRAL": {"owner_name": "Ramesh", "area_sqm": 1200.0}}
    confs = detect_multi_source_conflicts("P-101", data)
    assert any(c["conflict_type"] == "MISSING_IN_MUNICIPAL" for c in confs)
run_test("test_18_multi_source_conflict_missing_municipal", "Detect missing municipal record", t18)

# 19. Multi-source missing cadastral
def t19():
    data = {"MUNICIPAL": {"property_owner": "Ramesh", "built_area_sqm": 1200.0}}
    confs = detect_multi_source_conflicts("P-102", data)
    assert any(c["conflict_type"] == "MISSING_IN_CADASTRAL" for c in confs)
run_test("test_19_multi_source_conflict_missing_cadastral", "Detect missing cadastral record", t19)

# 20. Multi-source owner mismatch
def t20():
    data = {
        "CADASTRAL": {"owner_name": "Rajesh More"},
        "REGISTRY": {"owner_name": "Anita Sharma"}
    }
    confs = detect_multi_source_conflicts("P-103", data)
    assert any(c["conflict_type"] == "OWNER_MISMATCH" for c in confs)
run_test("test_20_multi_source_conflict_owner_mismatch", "Detect multi-source owner mismatch", t20)

# 21. Multi-source area mismatch
def t21():
    data = {
        "CADASTRAL": {"area_sqm": 1250.0},
        "MUNICIPAL": {"built_area_sqm": 1400.0}
    }
    confs = detect_multi_source_conflicts("P-104", data)
    assert any(c["conflict_type"] == "AREA_MISMATCH" for c in confs)
run_test("test_21_multi_source_conflict_area_mismatch", "Detect multi-source area mismatch", t21)

# 22. Multi-source encumbrance alert
def t22():
    data = {
        "CADASTRAL": {"owner_name": "Ramesh"},
        "BANK_MORTGAGE": {"loan_amount": "INR 45,00,000"}
    }
    confs = detect_multi_source_conflicts("P-105", data)
    assert any(c["conflict_type"] == "ENCUMBRANCE_ALERT" for c in confs)
run_test("test_22_multi_source_conflict_encumbrance", "Detect active bank mortgage encumbrance", t22)

# 23. Harmonization high score (Green)
def t23():
    data = {
        "CADASTRAL": {"owner_name": "Rajesh Sharma", "area_sqm": 1250.0, "centroid_lat": 19.0760, "centroid_lng": 72.8770},
        "MUNICIPAL": {"property_owner": "Rajesh Sharma", "built_area_sqm": 1250.0, "latitude": 19.0760, "longitude": 72.8770},
        "REGISTRY": {"owner_name": "Rajesh Sharma", "area_sqm": 1250.0}
    }
    res = calculate_multi_source_harmonization("DEMO-KPG-1001", data)
    assert res["harmonization_score"] >= 80.0, f"Score: {res['harmonization_score']}"
    assert res["status"] == "harmonized"
    assert res["color"] == "#22c55e"
run_test("test_23_multi_source_harmonization_high_score", "Multi-source high score (Green)", t23)

# 24. Harmonization moderate score (Yellow)
def t24():
    data = {
        "CADASTRAL": {"owner_name": "Suresh Patil", "area_sqm": 850.0, "centroid_lat": 19.0760, "centroid_lng": 72.8776},
        "MUNICIPAL": {"property_owner": "Suresh P", "built_area_sqm": 850.0, "latitude": 19.0760, "longitude": 72.8776}
    }
    res = calculate_multi_source_harmonization("DEMO-KPG-1002", data)
    assert 50.0 <= res["harmonization_score"] < 80.0, f"Score: {res['harmonization_score']}"
    assert res["status"] == "review_required"
    assert res["color"] == "#eab308"
run_test("test_24_multi_source_harmonization_moderate_score", "Moderate score review required (Yellow)", t24)

# 25. Harmonization critical conflict (Red)
def t25():
    data = {
        "CADASTRAL": {"owner_name": "Amit Deshmukh", "area_sqm": 1250.0, "centroid_lat": 19.0760, "centroid_lng": 72.8770},
        "MUNICIPAL": {"property_owner": "A Deshmukh", "built_area_sqm": 1400.0, "latitude": 19.0768, "longitude": 72.8780}
    }
    res = calculate_multi_source_harmonization("DEMO-KPG-1004", data)
    assert res["harmonization_score"] < 50.0, f"Score: {res['harmonization_score']}"
    assert res["status"] == "critical_conflict"
    assert res["color"] == "#ef4444"
run_test("test_25_multi_source_harmonization_critical_conflict", "Critical conflict low score (Red)", t25)

# Summary
print("\n" + "=" * 70)
print("PHASE C TEST SUMMARY")
print("=" * 70)
all_passed = True
for name, status in test_results.items():
    print(f"{name:45}: {status}")
    if status != "PASSED":
        all_passed = False

if all_passed:
    print("\n>>> ALL 25 PHASE C TESTS PASSED! <<<")
    sys.exit(0)
else:
    print("\n>>> SOME TESTS FAILED! <<<")
    sys.exit(1)
