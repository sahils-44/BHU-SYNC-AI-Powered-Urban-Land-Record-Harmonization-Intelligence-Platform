"""
BHU-SYNC Phase D: Advanced GIS & Spatial Intelligence Engine
Leverages Shapely and PyProj for coordinate transformations, geometric validation,
planar area/distance calculations, polygon IoU, and building/zoning overlays.
"""

from typing import Dict, List, Optional, Tuple, Any
import pyproj
from shapely.geometry import shape, mapping, Polygon, MultiPolygon, Point
from shapely.validation import make_valid
from shapely.ops import transform


# Coordinate Reference System Transformers
# EPSG:4326 (WGS84 lat/lng) <-> EPSG:32643 (UTM Zone 43N - covers western & central India including Maharashtra)
transformer_to_utm = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:32643", always_xy=True)
transformer_to_wgs84 = pyproj.Transformer.from_crs("EPSG:32643", "EPSG:4326", always_xy=True)


def to_utm(geom):
    """
    Projects WGS84 geometry (lon, lat) to UTM Zone 43N metric planar coordinates.
    """
    return transform(transformer_to_utm.transform, geom)


def to_wgs84(geom):
    """
    Projects UTM Zone 43N planar geometry back to WGS84 (lon, lat).
    """
    return transform(transformer_to_wgs84.transform, geom)


def validate_and_repair_geometry(geojson_geom: dict) -> Tuple[dict, bool, str]:
    """
    Validates a GeoJSON geometry using Shapely. If invalid, applies make_valid repair.
    Returns (repaired_geojson_dict, was_valid, report_message).
    """
    try:
        geom = shape(geojson_geom)
        if geom.is_valid and not geom.is_empty:
            return geojson_geom, True, "Valid geometry"
        
        # Repair invalid geometry
        repaired = make_valid(geom)
        return mapping(repaired), False, f"Repaired invalid geometry (type: {repaired.geom_type})"
    except Exception as e:
        # Fallback to original
        return geojson_geom, False, f"Failed to parse or repair: {str(e)}"


def compute_planar_area_sqm(geojson_geom: dict) -> float:
    """
    Computes precise surface area in square meters using UTM Zone 43N projection.
    """
    try:
        geom = shape(geojson_geom)
        utm_geom = to_utm(geom)
        return round(float(utm_geom.area), 2)
    except Exception:
        return 0.0


def compute_centroid(geojson_geom: dict) -> Tuple[float, float]:
    """
    Computes geometric centroid in WGS84 (longitude, latitude).
    """
    try:
        geom = shape(geojson_geom)
        c = geom.centroid
        return round(c.x, 6), round(c.y, 6)
    except Exception:
        return 0.0, 0.0


def compute_polygon_iou(geom1_dict: dict, geom2_dict: dict) -> float:
    """
    Calculates Intersection-over-Union (IoU = Area(A ∩ B) / Area(A ∪ B)) between two polygons.
    """
    try:
        g1 = shape(geom1_dict)
        g2 = shape(geom2_dict)

        utm_g1 = to_utm(g1)
        utm_g2 = to_utm(g2)

        intersection_area = utm_g1.intersection(utm_g2).area
        union_area = utm_g1.union(utm_g2).area

        if union_area <= 0:
            return 0.0

        return round(intersection_area / union_area, 4)
    except Exception:
        return 0.0


def compute_centroid_distance_meters(geom1_dict: dict, geom2_dict: dict) -> float:
    """
    Computes Euclidean distance in meters between centroids of two geometries.
    """
    try:
        g1 = shape(geom1_dict)
        g2 = shape(geom2_dict)

        utm_g1 = to_utm(g1)
        utm_g2 = to_utm(g2)

        c1 = utm_g1.centroid
        c2 = utm_g2.centroid

        return round(float(c1.distance(c2)), 2)
    except Exception:
        return 0.0


def evaluate_building_overlay(parcel_geom_dict: dict, building_geom_dict: dict) -> dict:
    """
    Analyzes building footprint against parcel boundaries:
    - Checks whether the building is strictly within parcel bounds.
    - Measures protruding area in square meters.
    """
    try:
        p_geom = to_utm(shape(parcel_geom_dict))
        b_geom = to_utm(shape(building_geom_dict))

        building_area = b_geom.area
        intersection_geom = b_geom.intersection(p_geom)
        intersection_area = intersection_geom.area

        protrusion_sqm = max(0.0, building_area - intersection_area)
        is_fully_contained = protrusion_sqm < 0.5  # 0.5 sqm tolerance

        return {
            "building_area_sqm": round(building_area, 2),
            "contained_area_sqm": round(intersection_area, 2),
            "protruding_area_sqm": round(protrusion_sqm, 2),
            "is_fully_contained": is_fully_contained,
            "has_violation": not is_fully_contained,
            "violation_type": "ENCROACHMENT" if not is_fully_contained else "NONE"
        }
    except Exception as e:
        return {
            "error": str(e),
            "is_fully_contained": False,
            "has_violation": True
        }


def evaluate_zoning_compliance(parcel_geom_dict: dict, parcel_land_use: str, zoning_zone: str) -> dict:
    """
    Checks parcel land use against designated master plan zoning.
    """
    use_clean = parcel_land_use.lower().strip()
    zone_clean = zoning_zone.lower().strip()

    is_compliant = True
    reason = "Complies with master plan zoning"

    if "residential" in zone_clean and "commercial" in use_clean:
        is_compliant = False
        reason = "Commercial activity detected within strictly Residential designated zone"
    elif "green_belt" in zone_clean or "agricultural" in zone_clean:
        if "residential" in use_clean or "commercial" in use_clean or "industrial" in use_clean:
            is_compliant = False
            reason = f"Non-agricultural development ({parcel_land_use}) in protected {zoning_zone} zone"

    return {
        "land_use": parcel_land_use,
        "zoning_zone": zoning_zone,
        "is_compliant": is_compliant,
        "violation_type": "ZONING_MISMATCH" if not is_compliant else "NONE",
        "description": reason
    }
