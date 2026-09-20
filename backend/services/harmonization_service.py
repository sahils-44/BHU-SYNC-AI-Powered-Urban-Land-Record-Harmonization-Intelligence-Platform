import pandas as pd

from services.spatial_matcher import calculate_distance


def calculate_harmonization_score(row):

    score = 0

    # Parcel identity
    if row["_merge"] == "both":
        score += 30

    # Owner
    owner_cadastral = str(
        row.get("owner_normalized_cadastral", "")
    )

    owner_municipal = str(
        row.get("owner_normalized_municipal", "")
    )

    if (
        owner_cadastral
        and owner_cadastral == owner_municipal
    ):
        score += 25

    # Area
    area_cadastral = row.get("area_cadastral")
    area_municipal = row.get("area_municipal")

    if (
        pd.notna(area_cadastral)
        and pd.notna(area_municipal)
    ):
        difference = abs(
            area_cadastral - area_municipal
        )

        if difference <= 5:
            score += 20
        elif difference <= 20:
            score += 10

    # Location
    distance = calculate_distance(
        row.get("latitude_cadastral"),
        row.get("longitude_cadastral"),
        row.get("latitude_municipal"),
        row.get("longitude_municipal")
    )

    if distance is not None:

        if distance <= 20:
            score += 25

        elif distance <= 50:
            score += 15

        elif distance <= 100:
            score += 5

    return score, distance


def build_harmonized_records(merged):

    records = []

    for _, row in merged.iterrows():

        score, distance = (
            calculate_harmonization_score(row)
        )

        conflicts = 0

        owner_cadastral = str(
            row.get(
                "owner_normalized_cadastral",
                ""
            )
        )

        owner_municipal = str(
            row.get(
                "owner_normalized_municipal",
                ""
            )
        )

        if (
            owner_cadastral
            and owner_municipal
            and owner_cadastral != owner_municipal
        ):
            conflicts += 1

        area_cadastral = row.get(
            "area_cadastral"
        )

        area_municipal = row.get(
            "area_municipal"
        )

        if (
            pd.notna(area_cadastral)
            and pd.notna(area_municipal)
            and abs(
                area_cadastral - area_municipal
            ) > 1
        ):
            conflicts += 1

        if distance is not None and distance > 50:
            conflicts += 1

        if row["_merge"] != "both":
            conflicts += 1

        status = "Harmonized"

        if score < 70:
            status = "Review Required"

        if row["_merge"] != "both":
            status = "Missing Source"

        records.append({
            "parcel_id": row["parcel_id"],
            "owner_name": (
                row.get("owner_name_cadastral")
                if pd.notna(
                    row.get("owner_name_cadastral")
                )
                else row.get(
                    "owner_name_municipal"
                )
            ),
            "area": (
                row.get("area_cadastral")
                if pd.notna(
                    row.get("area_cadastral")
                )
                else row.get("area_municipal")
            ),
            "ward": (
                row.get("ward_cadastral")
                if pd.notna(
                    row.get("ward_cadastral")
                )
                else row.get("ward_municipal")
            ),
            "harmonization_score": score,
            "source_count": 2
                if row["_merge"] == "both"
                else 1,
            "matching_sources": 2
                if row["_merge"] == "both"
                else 1,
            "conflict_count": conflicts,
            "explanation": (
                f"Harmonization score: {score}/100. "
                f"Spatial distance: "
                f"{round(distance, 2) if distance is not None else 'N/A'} meters."
            )
        })

    return records


def calculate_multi_source_harmonization(parcel_id: str, sources_data: dict) -> dict:
    """
    Computes a composite multi-source harmonization result, dynamic status, color, and field provenance
    across up to 10 integrated source record types.
    """
    from services.matching_config import get_harmonization_status, get_status_color, SOURCE_AUTHORITY
    from services.conflict_engine import detect_multi_source_conflicts
    from services.normalizer import normalize_owner_name_advanced, string_similarity

    detected_conflicts = detect_multi_source_conflicts(parcel_id, sources_data)
    num_sources = len(sources_data)

    # Base score
    score = 0.0

    # 1. Multi-source presence credit (up to 30 points)
    if num_sources >= 3:
        score += 30.0
    elif num_sources == 2:
        score += 20.0
    elif num_sources == 1:
        score += 10.0

    # 2. Ownership consensus (up to 25 points)
    owners = [
        normalize_owner_name_advanced(d.get("owner_name") or d.get("property_owner") or d.get("owner"))
        for d in sources_data.values()
        if (d.get("owner_name") or d.get("property_owner") or d.get("owner"))
    ]
    if len(owners) >= 2:
        sim = string_similarity(owners[0], owners[1])
        if sim >= 0.95:
            score += 25.0
        elif sim >= 0.70:
            score += 15.0
        else:
            score += 5.0
    elif len(owners) == 1:
        score += 15.0

    # 3. Area consistency (up to 25 points)
    areas = [
        float(d.get("area_sqm") or d.get("built_area_sqm") or d.get("area"))
        for d in sources_data.values()
        if (d.get("area_sqm") or d.get("built_area_sqm") or d.get("area")) is not None
    ]
    if len(areas) >= 2:
        diff = abs(areas[0] - areas[1])
        pct_diff = diff / max(areas[0], 1.0)
        if pct_diff <= 0.01:
            score += 25.0
        elif pct_diff <= 0.05:
            score += 15.0
        elif pct_diff <= 0.15:
            score += 5.0
    elif len(areas) == 1:
        score += 15.0

    # 4. Spatial consistency (up to 20 points)
    coords = [
        (float(d.get("latitude") or d.get("centroid_lat")), float(d.get("longitude") or d.get("centroid_lng")))
        for d in sources_data.values()
        if (d.get("latitude") or d.get("centroid_lat")) is not None and (d.get("longitude") or d.get("centroid_lng")) is not None
    ]
    if len(coords) >= 2:
        dist_deg = abs(coords[0][0] - coords[1][0]) + abs(coords[0][1] - coords[1][1])
        if dist_deg <= 0.0001:  # ~10m
            score += 20.0
        elif dist_deg <= 0.0005:  # ~50m
            score += 10.0
    elif len(coords) == 1:
        score += 10.0

    # Apply penalty deductions for detected conflicts
    for conf in detected_conflicts:
        c_type = conf.get("conflict_type")
        if c_type == "MISSING_IN_MUNICIPAL":
            score -= 35.0
        elif c_type == "OWNER_MISMATCH":
            score -= 25.0
        elif c_type == "AREA_MISMATCH":
            score -= 15.0
        elif c_type == "CENTROID_MISMATCH":
            score -= 20.0
        elif c_type == "ENCUMBRANCE_ALERT":
            score -= 10.0

    final_score = round(max(0.0, min(100.0, score)), 1)
    status_label = get_harmonization_status(final_score)
    color = get_status_color(final_score)

    # Provenance attribution
    # Canonical owner selected by authority: REGISTRY > CADASTRAL > MUNICIPAL
    canonical_owner = None
    owner_provenance = None
    for src in ["REGISTRY", "CADASTRAL", "MUNICIPAL"]:
        if src in sources_data:
            val = sources_data[src].get("owner_name") or sources_data[src].get("property_owner") or sources_data[src].get("owner")
            if val:
                canonical_owner = val
                owner_provenance = {"source": src, "authority_weight": SOURCE_AUTHORITY["ownership"].get(src, 0.3)}
                break

    # Canonical area selected by authority: CADASTRAL > SURVEY_OF_INDIA > MUNICIPAL
    canonical_area = None
    area_provenance = None
    for src in ["CADASTRAL", "SURVEY_OF_INDIA", "MUNICIPAL"]:
        if src in sources_data:
            val = sources_data[src].get("area_sqm") or sources_data[src].get("built_area_sqm") or sources_data[src].get("area")
            if val is not None:
                canonical_area = float(val)
                area_provenance = {"source": src, "authority_weight": SOURCE_AUTHORITY["boundary"].get(src, 0.3)}
                break

    return {
        "parcel_id": parcel_id,
        "harmonization_score": final_score,
        "status": status_label,
        "color": color,
        "source_count": num_sources,
        "conflict_count": len(detected_conflicts),
        "conflicts": detected_conflicts,
        "canonical_owner": canonical_owner,
        "owner_provenance": owner_provenance,
        "canonical_area": canonical_area,
        "area_provenance": area_provenance,
        "sources_present": list(sources_data.keys())
    }