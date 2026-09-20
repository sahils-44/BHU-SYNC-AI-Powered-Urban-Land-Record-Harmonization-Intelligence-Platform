import pandas as pd


def normalize_owner_name(name):

    if pd.isna(name):
        return ""

    name = str(name).lower().strip()

    # Remove extra spaces
    name = " ".join(name.split())

    return name


def harmonize(cadastral, municipal):

    cadastral = cadastral.copy()
    municipal = municipal.copy()

    # Normalize owner names
    cadastral["owner_normalized"] = (
        cadastral["owner_name"]
        .apply(normalize_owner_name)
    )

    municipal["owner_normalized"] = (
        municipal["owner_name"]
        .apply(normalize_owner_name)
    )

    # Match using parcel ID
    merged = cadastral.merge(
        municipal,
        on="parcel_id",
        how="outer",
        suffixes=("_cadastral", "_municipal"),
        indicator=True
    )

    return merged