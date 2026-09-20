import pandas as pd


def clean_dataset(df: pd.DataFrame) -> pd.DataFrame:

    df = df.copy()

    # Remove completely empty rows
    df = df.dropna(how="all")

    # Remove duplicate rows
    df = df.drop_duplicates()

    # Clean column names
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )

    # Map common alternate column names to canonical names
    column_aliases = {
        "property_owner": "owner_name",
        "owner": "owner_name",
        "area_sqm": "area",
        "built_area_sqm": "area",
        "plot_area": "area",
        "centroid_lat": "latitude",
        "lat": "latitude",
        "centroid_lng": "longitude",
        "lng": "longitude",
        "long": "longitude",
        "lon": "longitude",
    }
    for alias, target in column_aliases.items():
        if alias in df.columns and target not in df.columns:
            df[target] = df[alias]

    # Clean owner names
    if "owner_name" in df.columns:
        df["owner_name"] = (
            df["owner_name"]
            .astype(str)
            .str.strip()
        )

    # Convert area to number
    if "area" in df.columns:
        df["area"] = pd.to_numeric(
            df["area"],
            errors="coerce"
        )

    # Convert ward to number
    if "ward" in df.columns:
        df["ward"] = pd.to_numeric(
            df["ward"],
            errors="coerce"
        )

    # Convert latitude
    if "latitude" in df.columns:
        df["latitude"] = pd.to_numeric(
            df["latitude"],
            errors="coerce"
        )

    # Convert longitude
    if "longitude" in df.columns:
        df["longitude"] = pd.to_numeric(
            df["longitude"],
            errors="coerce"
        )

    return df