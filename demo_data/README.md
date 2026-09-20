# BHU-SYNC Synthetic Demo Dataset

These files contain SYNTHETIC development/demo records. They are not official government records.

Files:
- cadastral_demo.csv: 153 rows (150 unique parcel IDs plus a few intentional duplicates)
- municipal_demo.csv: 147 rows (includes some missing-source and municipal-only parcels)
- demo_parcels.geojson: 150 point features for direct GIS/map testing

Design:
- Coordinates are clustered into a compact local-style area so a map view is populated.
- Most records match across sources.
- Controlled owner-name, area, coordinate, missing-value, duplicate, and source-coverage differences are included so BHU-SYNC can demonstrate harmonization and review cases.
- The records use Maharashtra-style parcel IDs and ward numbers but are synthetic.

Suggested demo:
1. Upload Cadastral.
2. Upload Municipal.
3. Run harmonization.
4. Inspect green/harmonized, yellow/review, and red/low-score parcels.
5. Open a parcel and compare source records.
6. Use GIS/map view with the coordinates or GeoJSON.
