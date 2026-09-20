# BHU-SYNC: Smart India Hackathon (SIH) 10-Minute Demo Walkthrough
**"One Plot. One Truth. Multiple Sources, Intelligently Synced."**

---

## Executive Summary for Judges & Jury
Urban land governance in Indian cities suffers from institutional fragmentation: Revenue Cadastres (7/12 extracts), Municipal Property Tax records, Sub-Registrar Deeds, Town Planning permissions, and Utility databases maintain divergent records for the exact same physical parcel of land.

**BHU-SYNC** solves this multi-billion dollar challenge through an automated, AI-powered spatial harmonization platform that ingests, cleans, matches, resolves, and tracks urban land parcels across up to 10 government sources with cryptographic auditability and zero data destruction.

---

## 8-Part Presentation Flow (10-Minute Pitch & Demonstration)

### Part 1: The Urban Land Challenge (Minute 0:00 - 1:15)
* **Goal**: Ground the audience in the core problem of fragmented land records.
* **Demonstration**:
  1. Open the **BHU-SYNC Command Center** (`/`).
  2. Point to the live telemetry: **Total Parcels**, **Harmonization Score**, **Active Discrepancies**.
  3. Explain: *"In Shivaji Nagar (Ward 4 & 5), Plot MH-KPG-1004 has an area of 1,250 sqm in Revenue records, but 1,400 sqm in Municipal property tax assessments, alongside a 55-meter centroid shift."*
* **Key Soundbite**: *"Fragmented records cause urban disputes, revenue leakages, and delayed infrastructure projects. BHU-SYNC unifies them into a single authoritative record."*

---

### Part 2: Multi-Source Ingestion & Data Quality (Minute 1:15 - 2:30)
* **Goal**: Show automated data ingestion across 10 government sources.
* **Demonstration**:
  1. Navigate to **Data Hub** (`/datasets`).
  2. Showcase supported sources: `CADASTRAL`, `MUNICIPAL`, `REGISTRY`, `SURVEY OF INDIA`, `UTILITY WATER`, `UTILITY ELECTRICITY`, `BUILDING PERMIT`, `BANK MORTGAGE`, `TAX ASSESSMENT`, `SATELLITE IMAGERY`.
  3. Upload sample dataset (drag-and-drop CSV/GeoJSON).
  4. Point out the **Security Perimeter**: Automatic path-traversal sanitization, 10MB payload size enforcement, and filetype whitelisting.
  5. Inspect the computed **Data Quality Score** (Completeness, Uniqueness, Validity, Coordinate Consistency).
* **Key Soundbite**: *"Every ingested dataset is immutably versioned without overwriting historical source records."*

---

### Part 3: Identity Resolution & Harmonization Scoring (Minute 2:30 - 3:45)
* **Goal**: Demonstrate how BHU-SYNC matches records using the 7-level hierarchy.
* **Demonstration**:
  1. Navigate to **Harmonization** (`/harmonization`).
  2. Walk through the 7-level matching engine:
     * Level 1: Exact ULPIN / Parcel ID Match
     * Level 2: Owner Name Exact Match + Village
     * Level 3: Phonetic Soundex + Levenshtein Similarity (`Suresh Patil` vs `Suresh P`)
     * Level 4: Centroid Proximity Tolerance
     * Level 5: Polygon Intersection-over-Union (IoU)
     * Level 6: Survey / Khasra Hierarchy
     * Level 7: Utility Consumer ID Cross-reference
  3. Explain the **Harmonization Score (0-100)**:
     * $\ge 80$: **Harmonized (Green)** — Unanimous multi-source agreement.
     * $50 - 79$: **Review Required (Yellow)** — Minor owner abbreviation or spelling difference.
     * $< 50$: **Critical Conflict (Red)** — Area variance $>5\%$, centroid shift, or missing link.
* **Key Soundbite**: *"Zero hardcoding. Scores and colors are calculated dynamically by database-backed reconciliation algorithms."*

---

### Part 4: Advanced GIS & Spatial Intelligence (Minute 3:45 - 5:15)
* **Goal**: Visualize spatial discrepancies and geometric validation on the interactive map.
* **Demonstration**:
  1. Navigate to **GIS Map** (`/gis`).
  2. Inspect the **Dynamic Color Classification**:
     * Green polygon: `DEMO-KPG-1001` (Harmonized, score 96.0).
     * Yellow polygon: `DEMO-KPG-1002` (Owner variation, score 68.0).
     * Red polygon: `DEMO-KPG-1004` (Area mismatch + centroid shift, score 45.0).
     * Red polygon: `DEMO-KPG-1005` (Missing municipal tax record, score 32.0).
  3. Toggle **Layer Overlays**:
     * `Building Footprints`: Point out building `BLD-401` perfectly contained within `DEMO-KPG-1001`.
     * `Encroachments`: Highlight the 45.2 sqm protrusion on `DEMO-KPG-1004`.
     * `Master Plan Zoning`: Verify Residential R1 zoning compliance.
  4. Showcase Millimeter Precision: Explain projected CRS `EPSG:32643 (UTM Zone 43N)` planar area computation.
* **Key Soundbite**: *"We don't just display points on a map — our Shapely engine computes exact polygon IoU, detects encroachments, and validates master plan zoning."*

---

### Part 5: Grounded AI Copilot 2.0 (Minute 5:15 - 6:45)
* **Goal**: Prove that the AI Copilot is 100% grounded, strictly read-only, and interactive.
* **Demonstration**:
  1. Open **AI Copilot** (`/copilot`).
  2. Show the **"100% Grounded in Database"** badge.
  3. Ask: *"Why is MH-KPG-1004 flagged?"*
  4. Highlight the Response:
     * Detailed analysis: Area discrepancy (1,250 vs 1,290 sqm) and centroid difference.
     * **Official Citations**: Direct references to Cadastral and Municipal source records.
     * **Interactive Map Action**: Button to immediately focus parcel `MH-KPG-1004` on the GIS map.
  5. Security Proof: Try asking *"DROP TABLE canonical_parcels;"*.
     * Show immediate HTTP 400 rejection: *"Direct SQL execution is strictly prohibited. AI Copilot operates solely via authenticated read-only analytical tools."*
* **Key Soundbite**: *"Our Copilot cannot hallucinate and cannot execute SQL injection. It cites official records and drives the map interface."*

---

### Part 6: Temporal / Change Intelligence (Minute 6:45 - 7:45)
* **Goal**: Demonstrate how land evolves over time across 17 change events.
* **Demonstration**:
  1. Query `GET /temporal/parcel/DEMO-KPG-1004/history`.
  2. Inspect the chronological timeline:
     * `PARCEL_CREATED`: Initial cadastral survey mapping at 1,250 sqm.
     * `AREA_EXPANDED`: Municipal tax assessment updated area to 1,400 sqm.
     * `CONFLICT_DETECTED`: BHU-SYNC engine flagged 150 sqm discrepancy.
  3. Show **Before and After Snapshots**: Zero destructive overwrites.
* **Key Soundbite**: *"Every mutation preserves historical before/after snapshots across 17 standardized event types."*

---

### Part 7: Government Workflow & Investigation Case Management (Minute 7:45 - 8:45)
* **Goal**: Show government case lifecycle driven by a Finite State Machine (FSM).
* **Demonstration**:
  1. Open active dispute case `CASE-2024-001` (`DEMO-KPG-1004`).
  2. Show current state: `UNDER_INVESTIGATION`, assigned to Revenue Officer.
  3. Inspect **Investigation Notes**: Officer field notes describing boundary fence extension.
  4. Inspect **Linked Evidence**: Digital survey map `DOC-PUNE-REV-8891`.
  5. Attempt invalid transition (e.g. attempting to jump straight to `CLOSED`): Show strict FSM rejection.
  6. Transition to `PENDING_REVIEW` with documented audit reason.
* **Key Soundbite**: *"Disputes don't stay unresolved. Officers follow strict Finite State Machine lifecycles with linked physical evidence."*

---

### Part 8: Tamper-Evident SHA-256 Audit Trail (Minute 8:45 - 10:00)
* **Goal**: Demonstrate enterprise-grade anti-corruption and cryptographic integrity.
* **Demonstration**:
  1. Open Audit Logs view (`GET /audit/logs`).
  2. Explain the cryptographic chain:
     $$Hash_i = SHA256(Hash_{i-1} + Timestamp + ActorID + Action + ResourceID + Payload)$$
  3. Click **"Verify Cryptographic Integrity"** (`GET /audit/verify-chain`).
  4. Show verified status: *"Successfully verified cryptographic chain across all entries from Genesis block."*
  5. Security Proof: Point out that **zero PUT/PATCH/DELETE endpoints exist** on audit logs.
* **Key Soundbite**: *"Land records cannot be silently manipulated in BHU-SYNC. Any tampering breaks the cryptographic hash chain immediately."*

---

## SIH Demo Parcels Reference Card

| Parcel ID | Owner Consensus | Harmonization Score | GIS Color | Status | Key Feature Demonstrated |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **DEMO-KPG-1001** | Rajesh Sharma | **96.0** | **Green (#22c55e)** | Harmonized | 3-source unanimous match; building contained |
| **DEMO-KPG-1002** | Suresh Patil vs Suresh P | **68.0** | **Yellow (#eab308)** | Review Required | Phonetic soundex & fuzzy abbreviation match |
| **DEMO-KPG-1003** | Sunita Verma | **92.0** | **Green (#22c55e)** | Harmonized | Multi-source alignment with building footprint |
| **DEMO-KPG-1004** | Amit Deshmukh | **45.0** | **Red (#ef4444)** | Critical Conflict | Area mismatch + 55m centroid shift + FSM case |
| **DEMO-KPG-1005** | Pooja Nair | **32.0** | **Red (#ef4444)** | Critical Conflict | Missing municipal tax assessment |
| **DEMO-KPG-1006** | Vijay Shinde | **94.0** | **Green (#22c55e)** | Harmonized | Case resolved by officer with sale deed evidence |
