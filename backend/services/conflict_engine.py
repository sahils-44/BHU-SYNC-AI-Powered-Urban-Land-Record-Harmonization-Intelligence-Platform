import pandas as pd


def detect_conflicts(df):
    conflicts = []

    for _, row in df.iterrows():

        parcel_id = row["parcel_id"]

        # --------------------------------
        # Missing in Municipal
        # --------------------------------

        if row.get("_merge") == "left_only":

            conflicts.append({
                "parcel_id": parcel_id,
                "conflict_type": "MISSING_IN_MUNICIPAL",
                "severity": "HIGH",
                "description": (
                    "Parcel exists in cadastral records "
                    "but is missing from municipal records."
                ),
                "recommended_action": (
                    "Verify municipal land record."
                )
            })

            continue

        # --------------------------------
        # Missing in Cadastral
        # --------------------------------

        if row.get("_merge") == "right_only":

            conflicts.append({
                "parcel_id": parcel_id,
                "conflict_type": "MISSING_IN_CADASTRAL",
                "severity": "HIGH",
                "description": (
                    "Parcel exists in municipal records "
                    "but is missing from cadastral records."
                ),
                "recommended_action": (
                    "Verify cadastral land record."
                )
            })

            continue

        # --------------------------------
        # Owner mismatch
        # --------------------------------

        owner_cadastral = str(
            row.get("owner_normalized_cadastral", "")
        ).strip()

        owner_municipal = str(
            row.get("owner_normalized_municipal", "")
        ).strip()

        if owner_cadastral != owner_municipal:

            conflicts.append({
                "parcel_id": parcel_id,
                "conflict_type": "OWNER_MISMATCH",
                "severity": "HIGH",
                "description": (
                    f"Owner differs: "
                    f"{row.get('owner_name_cadastral', '')} vs "
                    f"{row.get('owner_name_municipal', '')}"
                ),
                "recommended_action": (
                    "Verify owner information across source records."
                )
            })

        # --------------------------------
        # Area mismatch
        # --------------------------------

        area_cadastral = row.get("area_cadastral")
        area_municipal = row.get("area_municipal")

        if (
            pd.notna(area_cadastral)
            and pd.notna(area_municipal)
        ):

            difference = abs(
                float(area_cadastral) - float(area_municipal)
            )

            if difference > 1:

                conflicts.append({
                    "parcel_id": parcel_id,
                    "conflict_type": "AREA_MISMATCH",
                    "severity": "MEDIUM",
                    "difference_value": difference,
                    "description": (
                        f"Area differs by "
                        f"{difference} square meters."
                    ),
                    "recommended_action": (
                        "Verify latest survey or measurement record."
                    )
                })

        # --------------------------------
        # Location mismatch
        # --------------------------------

        lat_cadastral = row.get("latitude_cadastral")
        lat_municipal = row.get("latitude_municipal")

        lon_cadastral = row.get("longitude_cadastral")
        lon_municipal = row.get("longitude_municipal")

        if (
            pd.notna(lat_cadastral)
            and pd.notna(lat_municipal)
            and pd.notna(lon_cadastral)
            and pd.notna(lon_municipal)
        ):

            location_difference = (
                abs(float(lat_cadastral) - float(lat_municipal))
                + abs(float(lon_cadastral) - float(lon_municipal))
            )

            if location_difference > 0.0005:

                conflicts.append({
                    "parcel_id": parcel_id,
                    "conflict_type": "LOCATION_MISMATCH",
                    "severity": "MEDIUM",
                    "description": (
                        "Parcel coordinates differ "
                        "between source datasets."
                    ),
                    "recommended_action": (
                        "Verify survey/GIS coordinates."
                    )
                })

    return conflicts


def detect_multi_source_conflicts(parcel_id: str, sources_data: dict) -> list:
    """
    Evaluates multi-source discrepancies across up to 10 source record categories:
    CADASTRAL, MUNICIPAL, REGISTRY, SURVEY_OF_INDIA, BANK_MORTGAGE, etc.
    """
    conflicts = []
    
    # 1. Check Missing Sources
    has_cadastral = "CADASTRAL" in sources_data
    has_municipal = "MUNICIPAL" in sources_data
    has_registry = "REGISTRY" in sources_data

    if has_cadastral and not has_municipal:
        conflicts.append({
            "parcel_id": parcel_id,
            "conflict_type": "MISSING_IN_MUNICIPAL",
            "severity": "HIGH",
            "description": "Parcel is registered in Cadastral records but has no Municipal property tax link.",
            "recommended_action": "Verify municipal tax assessment and link property ID."
        })

    if has_municipal and not has_cadastral:
        conflicts.append({
            "parcel_id": parcel_id,
            "conflict_type": "MISSING_IN_CADASTRAL",
            "severity": "HIGH",
            "description": "Parcel is active in Municipal records but missing from Revenue Cadastre.",
            "recommended_action": "Initiate revenue survey and mutation check."
        })

    # 2. Ownership Conflicts
    owners = {}
    for s_name, data in sources_data.items():
        o_name = data.get("owner_name") or data.get("property_owner") or data.get("owner")
        if o_name:
            owners[s_name] = str(o_name).strip()

    if len(owners) >= 2:
        names = list(owners.values())
        # Compare normalized
        norm_names = [n.lower().replace(".", " ").strip() for n in names]
        if len(set(norm_names)) > 1:
            sources_str = ", ".join([f"{k}: '{v}'" for k, v in owners.items()])
            conflicts.append({
                "parcel_id": parcel_id,
                "conflict_type": "OWNER_MISMATCH",
                "severity": "HIGH",
                "description": f"Owner name discrepancy detected across sources: {sources_str}",
                "recommended_action": "Reconcile latest registered conveyance deed against revenue records."
            })

    # 3. Area Discrepancies
    areas = {}
    for s_name, data in sources_data.items():
        area_val = data.get("area_sqm") or data.get("built_area_sqm") or data.get("area")
        if area_val is not None:
            try:
                areas[s_name] = float(area_val)
            except (ValueError, TypeError):
                pass

    if len(areas) >= 2:
        vals = list(areas.values())
        max_a = max(vals)
        min_a = min(vals)
        diff = max_a - min_a
        # Flag if difference > 5 sqm and > 2% of min
        if diff > 5.0 and (diff / (min_a if min_a > 0 else 1.0)) > 0.02:
            sources_str = ", ".join([f"{k}: {v} sqm" for k, v in areas.items()])
            conflicts.append({
                "parcel_id": parcel_id,
                "conflict_type": "AREA_MISMATCH",
                "severity": "MEDIUM",
                "difference_value": round(diff, 2),
                "description": f"Area variance across sources exceeds threshold: {sources_str} (delta: {round(diff, 2)} sqm)",
                "recommended_action": "Commission ground physical verification or DGPS measurement."
            })

    # 4. Bank Mortgage / Encumbrance Alert
    if "BANK_MORTGAGE" in sources_data:
        bm = sources_data["BANK_MORTGAGE"]
        loan_amount = bm.get("loan_amount") or bm.get("mortgage_value", "Active")
        conflicts.append({
            "parcel_id": parcel_id,
            "conflict_type": "ENCUMBRANCE_ALERT",
            "severity": "CRITICAL",
            "description": f"Active financial encumbrance registered (CERSAI/Bank Mortgage): {loan_amount}",
            "recommended_action": "Verify No Objection Certificate (NOC) from lending institution before mutation."
        })

    # 5. Spatial Centroid Shift
    coords = {}
    for s_name, data in sources_data.items():
        lat = data.get("latitude") or data.get("centroid_lat")
        lon = data.get("longitude") or data.get("centroid_lng")
        if lat is not None and lon is not None:
            try:
                coords[s_name] = (float(lat), float(lon))
            except (ValueError, TypeError):
                pass

    if len(coords) >= 2:
        items = list(coords.items())
        p1_name, (lat1, lon1) = items[0]
        p2_name, (lat2, lon2) = items[1]
        dist_deg = abs(lat1 - lat2) + abs(lon1 - lon2)
        if dist_deg > 0.0005:  # approx > 50 meters
            conflicts.append({
                "parcel_id": parcel_id,
                "conflict_type": "CENTROID_MISMATCH",
                "severity": "HIGH",
                "description": f"Centroid shift observed between {p1_name} and {p2_name} (~{round(dist_deg * 111000, 1)}m shift)",
                "recommended_action": "Realign GIS coordinates to Survey of India geodetic reference."
            })

    return conflicts

