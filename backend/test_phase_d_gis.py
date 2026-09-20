"""
BHU-SYNC PHASE D: ADVANCED GIS & SPATIAL INTELLIGENCE AUTOMATED TEST SUITE
Verifies 30 test scenarios covering Shapely validation, PyProj coordinate transforms,
polygon IoU, centroid distance, building footprint overlays, zoning compliance,
and GeoJSON REST endpoints with dynamic scoring colors.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from fastapi.testclient import TestClient
from main import app
from services.spatial_engine import (
    validate_and_repair_geometry,
    compute_planar_area_sqm,
    compute_centroid,
    compute_polygon_iou,
    compute_centroid_distance_meters,
    evaluate_building_overlay,
    evaluate_zoning_compliance
)

client = TestClient(app)
AUTH_HEADERS = {"Authorization": "Bearer test-token-officer"}

print("=" * 70)
print("BHU-SYNC PHASE D AUTOMATED VERIFICATION SUITE (30 TESTS)")
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

# Sample polygons
poly_valid = {
    "type": "Polygon",
    "coordinates": [[[72.8770, 19.0760], [72.8780, 19.0760], [72.8780, 19.0770], [72.8770, 19.0770], [72.8770, 19.0760]]]
}

poly_bowtie_invalid = {
    "type": "Polygon",
    "coordinates": [[[72.8770, 19.0760], [72.8780, 19.0770], [72.8780, 19.0760], [72.8770, 19.0770], [72.8770, 19.0760]]]
}

poly_adjacent = {
    "type": "Polygon",
    "coordinates": [[[72.8780, 19.0760], [72.8790, 19.0760], [72.8790, 19.0770], [72.8780, 19.0770], [72.8780, 19.0760]]]
}

poly_overlap = {
    "type": "Polygon",
    "coordinates": [[[72.8775, 19.0760], [72.8785, 19.0760], [72.8785, 19.0770], [72.8775, 19.0770], [72.8775, 19.0760]]]
}

# 1. Valid polygon
def t1():
    geom, valid, _ = validate_and_repair_geometry(poly_valid)
    assert valid is True
run_test("test_1_shapely_valid_polygon", "Valid polygon check", t1)

# 2. Self-intersecting repair
def t2():
    repaired, valid, msg = validate_and_repair_geometry(poly_bowtie_invalid)
    assert valid is False
    assert "Repaired" in msg
run_test("test_2_shapely_self_intersecting_repair", "Repair self-intersecting polygon", t2)

# 3. UTM transformation forward
def t3():
    area = compute_planar_area_sqm(poly_valid)
    assert area > 1000.0, f"Area: {area}"
run_test("test_3_utm_transformation_forward", "WGS84 to UTM planar transformation", t3)

# 4. UTM reverse
def t4():
    lon, lat = compute_centroid(poly_valid)
    assert round(lon, 4) == 72.8775 and round(lat, 4) == 19.0765
run_test("test_4_utm_transformation_reverse", "Planar centroid to WGS84", t4)

# 5. Planar area computation
def t5():
    area = compute_planar_area_sqm(poly_valid)
    assert 11000.0 <= area <= 14000.0, f"Got: {area}"
run_test("test_5_planar_area_computation", "Planar area in square meters", t5)

# 6. Centroid computation
def t6():
    c = compute_centroid(poly_valid)
    assert len(c) == 2 and isinstance(c[0], float)
run_test("test_6_centroid_computation", "Centroid coordinate tuple", t6)

# 7. Polygon IoU identical
def t7():
    iou = compute_polygon_iou(poly_valid, poly_valid)
    assert iou == 1.0, f"Got {iou}"
run_test("test_7_polygon_iou_identical", "Polygon IoU with itself is 1.0", t7)

# 8. Polygon IoU disjoint
def t8():
    poly_far = {
        "type": "Polygon",
        "coordinates": [[[73.0, 20.0], [73.01, 20.0], [73.01, 20.01], [73.0, 20.01], [73.0, 20.0]]]
    }
    iou = compute_polygon_iou(poly_valid, poly_far)
    assert iou == 0.0, f"Got {iou}"
run_test("test_8_polygon_iou_disjoint", "Polygon IoU disjoint is 0.0", t8)

# 9. Polygon IoU partial overlap
def t9():
    iou = compute_polygon_iou(poly_valid, poly_overlap)
    assert 0.30 <= iou <= 0.40, f"Got {iou}"
run_test("test_9_polygon_iou_partial", "Polygon IoU partial overlap ~0.33", t9)

# 10. Centroid distance concentric
def t10():
    dist = compute_centroid_distance_meters(poly_valid, poly_valid)
    assert dist == 0.0, f"Got {dist}"
run_test("test_10_centroid_distance_concentric", "Centroid distance identical = 0", t10)

# 11. Centroid distance offset
def t11():
    dist = compute_centroid_distance_meters(poly_valid, poly_adjacent)
    assert 90.0 <= dist <= 120.0, f"Got {dist}"
run_test("test_11_centroid_distance_offset", "Centroid distance offset ~105m", t11)

# 12. Building overlay contained
def t12():
    building_inside = {
        "type": "Polygon",
        "coordinates": [[[72.8772, 19.0762], [72.8778, 19.0762], [72.8778, 19.0768], [72.8772, 19.0768], [72.8772, 19.0762]]]
    }
    res = evaluate_building_overlay(poly_valid, building_inside)
    assert res["is_fully_contained"] is True
    assert res["protruding_area_sqm"] == 0.0
run_test("test_12_building_overlay_contained", "Building footprint contained within parcel", t12)

# 13. Building overlay protrusion
def t13():
    building_protruding = {
        "type": "Polygon",
        "coordinates": [[[72.8775, 19.0765], [72.8785, 19.0765], [72.8785, 19.0775], [72.8775, 19.0775], [72.8775, 19.0765]]]
    }
    res = evaluate_building_overlay(poly_valid, building_protruding)
    assert res["is_fully_contained"] is False
    assert res["protruding_area_sqm"] > 10.0
run_test("test_13_building_overlay_protrusion", "Building footprint protrusion violation", t13)

# 14. Zoning compliance allowed
def t14():
    res = evaluate_zoning_compliance(poly_valid, "Residential", "Residential R1")
    assert res["is_compliant"] is True
run_test("test_14_zoning_compliance_allowed", "Residential land use in Residential R1 zone", t14)

# 15. Zoning compliance violation
def t15():
    res = evaluate_zoning_compliance(poly_valid, "Commercial Shop", "Residential R1")
    assert res["is_compliant"] is False
    assert res["violation_type"] == "ZONING_MISMATCH"
run_test("test_15_zoning_compliance_violation", "Commercial land use in Residential R1 zone flagged", t15)

# 16. Zoning greenbelt violation
def t16():
    res = evaluate_zoning_compliance(poly_valid, "Residential Villa", "Green_Belt")
    assert res["is_compliant"] is False
run_test("test_16_zoning_greenbelt_violation", "Residential building in Green Belt zone flagged", t16)

# 17. GIS endpoint unauthenticated
def t17():
    r = client.get("/gis/parcels")
    assert r.status_code == 401
run_test("test_17_gis_endpoint_unauthenticated", "Unauthenticated GET /gis/parcels rejected (401)", t17)

# 18. GIS endpoint authenticated
def t18():
    r = client.get("/gis/parcels", headers=AUTH_HEADERS)
    assert r.status_code == 200
    data = r.json()
    assert data.get("type") == "FeatureCollection"
run_test("test_18_gis_endpoint_authenticated", "Authenticated GET /gis/parcels returns FeatureCollection", t18)

# 19. GIS endpoint feature structure
def t19():
    r = client.get("/gis/parcels", headers=AUTH_HEADERS)
    features = r.json().get("features", [])
    assert len(features) > 0
    f = features[0]
    assert "geometry" in f and "properties" in f
    assert "parcel_id" in f["properties"]
run_test("test_19_gis_endpoint_valid_feature_structure", "GeoJSON Feature standard schema adherence", t19)

# 20. Dynamic color Green (>=80)
def t20():
    r = client.get("/gis/parcels", headers=AUTH_HEADERS)
    p = next((f for f in r.json()["features"] if f["properties"]["parcel_id"] == "DEMO-KPG-1001"), None)
    assert p is not None
    assert p["properties"]["harmonization_score"] >= 80.0
    assert p["properties"]["color"] == "#22c55e"
run_test("test_20_gis_endpoint_dynamic_color_green", "Dynamic color Green (#22c55e) for score >= 80", t20)

# 21. Dynamic color Yellow (50-79)
def t21():
    r = client.get("/gis/parcels", headers=AUTH_HEADERS)
    p = next((f for f in r.json()["features"] if f["properties"]["parcel_id"] == "DEMO-KPG-1002"), None)
    assert p is not None
    assert 50.0 <= p["properties"]["harmonization_score"] < 80.0
    assert p["properties"]["color"] == "#eab308"
run_test("test_21_gis_endpoint_dynamic_color_yellow", "Dynamic color Yellow (#eab308) for score 50-79", t21)

# 22. Dynamic color Red (<50)
def t22():
    r = client.get("/gis/parcels", headers=AUTH_HEADERS)
    p = next((f for f in r.json()["features"] if f["properties"]["parcel_id"] == "DEMO-KPG-1004"), None)
    assert p is not None
    assert p["properties"]["harmonization_score"] < 50.0
    assert p["properties"]["color"] == "#ef4444"
run_test("test_22_gis_endpoint_dynamic_color_red", "Dynamic color Red (#ef4444) for score < 50", t22)

# 23. Single parcel endpoint
def t23():
    r = client.get("/gis/parcels/DEMO-KPG-1001", headers=AUTH_HEADERS)
    assert r.status_code == 200
    data = r.json()
    assert "computed_spatial" in data
run_test("test_23_gis_single_parcel_endpoint", "GET /gis/parcels/{id} returns feature & spatial metrics", t23)

# 24. Single parcel not found
def t24():
    r = client.get("/gis/parcels/NONEXISTENT-999", headers=AUTH_HEADERS)
    assert r.status_code == 404
run_test("test_24_gis_single_parcel_not_found", "GET /gis/parcels/NONEXISTENT returns 404", t24)

# 25. Layer zoning
def t25():
    r = client.get("/gis/layers/zoning", headers=AUTH_HEADERS)
    assert r.status_code == 200
    assert r.json().get("type") == "FeatureCollection"
run_test("test_25_gis_layer_zoning", "GET /gis/layers/zoning returns layer overlay", t25)

# 26. Layer buildings
def t26():
    r = client.get("/gis/layers/building_footprints", headers=AUTH_HEADERS)
    assert r.status_code == 200
    assert r.json().get("type") == "FeatureCollection"
run_test("test_26_gis_layer_buildings", "GET /gis/layers/building_footprints returns layer overlay", t26)

# 27. Layer encroachments
def t27():
    r = client.get("/gis/layers/encroachments", headers=AUTH_HEADERS)
    assert r.status_code == 200
    assert r.json().get("type") == "FeatureCollection"
run_test("test_27_gis_layer_encroachments", "GET /gis/layers/encroachments returns layer overlay", t27)

# 28. Layer invalid
def t28():
    r = client.get("/gis/layers/unknown_layer", headers=AUTH_HEADERS)
    assert r.status_code == 400
run_test("test_28_gis_layer_invalid", "Invalid layer query returns HTTP 400", t28)

# 29. Spatial summary
def t29():
    r = client.get("/gis/spatial-summary", headers=AUTH_HEADERS)
    assert r.status_code == 200
    assert r.json().get("success") is True
run_test("test_29_gis_spatial_summary", "GET /gis/spatial-summary returns macro GIS metrics", t29)

# 30. Bounding box filter
def t30():
    r = client.get("/gis/parcels?min_lon=72.87&min_lat=19.07&max_lon=72.89&max_lat=19.08", headers=AUTH_HEADERS)
    assert r.status_code == 200
    assert len(r.json().get("features", [])) > 0
run_test("test_30_gis_bounding_box_filter", "Bounding-box spatial query filtering", t30)

# Summary
print("\n" + "=" * 70)
print("PHASE D TEST SUMMARY")
print("=" * 70)
all_passed = True
for name, status in test_results.items():
    print(f"{name:45}: {status}")
    if status != "PASSED":
        all_passed = False

if all_passed:
    print("\n>>> ALL 30 PHASE D TESTS PASSED! <<<")
    sys.exit(0)
else:
    print("\n>>> SOME TESTS FAILED! <<<")
    sys.exit(1)
