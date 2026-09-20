import pandas as pd

from services.cleaner import clean_dataset
from services.matcher import harmonize
from services.conflict_engine import detect_conflicts
from services.confidence import calculate_confidence
from services.spatial_matcher import calculate_distance


# =========================================
# 1. Read datasets
# =========================================

cadastral = pd.read_csv(
    "data/cadastral.csv"
)

municipal = pd.read_csv(
    "data/municipal.csv"
)


# =========================================
# 2. Clean datasets
# =========================================

cadastral = clean_dataset(cadastral)

municipal = clean_dataset(municipal)


# =========================================
# 3. Harmonize
# =========================================

merged = harmonize(
    cadastral,
    municipal
)


# =========================================
# 4. Calculate confidence
# =========================================

merged["confidence_score"] = (
    merged.apply(
        calculate_confidence,
        axis=1
    )
)


# =========================================
# 5. Calculate spatial distance
# =========================================

def get_distance(row):

    if (
        pd.notna(row.get("latitude_cadastral"))
        and pd.notna(row.get("latitude_municipal"))
        and pd.notna(row.get("longitude_cadastral"))
        and pd.notna(row.get("longitude_municipal"))
    ):

        return calculate_distance(
            row["latitude_cadastral"],
            row["longitude_cadastral"],
            row["latitude_municipal"],
            row["longitude_municipal"]
        )

    return None


merged["spatial_distance_m"] = (
    merged.apply(
        get_distance,
        axis=1
    )
)


# =========================================
# 6. Detect conflicts
# =========================================

conflicts = detect_conflicts(
    merged
)


# =========================================
# 7. Display results
# =========================================

print("\n================================")
print("BHU-SYNC HARMONIZATION RESULTS")
print("================================")

print(
    merged[
        [
            "parcel_id",
            "_merge",
            "spatial_distance_m",
            "confidence_score"
        ]
    ]
)


print("\n================================")
print("CONFLICTS")
print("================================")

for conflict in conflicts:

    print(
        f"\nParcel: {conflict['parcel_id']}"
    )

    print(
        f"Type: {conflict['conflict_type']}"
    )

    print(
        f"Severity: {conflict['severity']}"
    )

    print(
        f"Description: {conflict['description']}"
    )
