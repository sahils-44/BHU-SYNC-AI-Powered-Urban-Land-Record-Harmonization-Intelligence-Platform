import pandas as pd

from services.spatial_matcher import (
    calculate_distance
)


def calculate_confidence(row):

    score = 0

    # =========================================
    # Parcel ID match
    # Maximum: 30 points
    # =========================================

    if row["_merge"] == "both":
        score += 30

    else:
        return 0


    # =========================================
    # Owner match
    # Maximum: 25 points
    # =========================================

    owner_cadastral = row.get(
        "owner_normalized_cadastral",
        ""
    )

    owner_municipal = row.get(
        "owner_normalized_municipal",
        ""
    )

    if owner_cadastral == owner_municipal:
        score += 25


    # =========================================
    # Area match
    # Maximum: 20 points
    # =========================================

    area_cadastral = row.get(
        "area_cadastral"
    )

    area_municipal = row.get(
        "area_municipal"
    )

    if (
        pd.notna(area_cadastral)
        and pd.notna(area_municipal)
    ):

        difference = abs(
            float(area_cadastral)
            - float(area_municipal)
        )

        if difference <= 1:
            score += 20

        elif difference <= 50:
            score += 10


    # =========================================
    # Location match
    # Maximum: 25 points
    # =========================================

    lat_c = row.get(
        "latitude_cadastral"
    )

    lat_m = row.get(
        "latitude_municipal"
    )

    lon_c = row.get(
        "longitude_cadastral"
    )

    lon_m = row.get(
        "longitude_municipal"
    )

    if (
        pd.notna(lat_c)
        and pd.notna(lat_m)
        and pd.notna(lon_c)
        and pd.notna(lon_m)
    ):

        distance = calculate_distance(
            lat_c,
            lon_c,
            lat_m,
            lon_m
        )

        if distance <= 20:
            score += 25

        elif distance <= 50:
            score += 15

        elif distance <= 100:
            score += 5


    # =========================================
    # Final confidence score
    # Maximum: 100
    # =========================================

    return score
