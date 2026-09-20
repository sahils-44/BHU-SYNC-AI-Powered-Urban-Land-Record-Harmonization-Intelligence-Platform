# BHU-SYNC

## AI-Powered Urban Land Record Harmonization & Intelligence Platform

> **One Plot. One Truth. Multiple Sources, Intelligently Synced.**

**Smart India Hackathon Prototype**  
**Team: TechX Titan**

---

## 📌 Overview

**BHU-SYNC** is an AI-powered urban land-record harmonization and intelligence platform designed to bring together information from multiple heterogeneous land and civic data sources into a unified, traceable, spatially intelligent system.

A single physical parcel may be represented differently across:

- Cadastral records
- Municipal records
- Registration records
- Property tax records
- Survey information
- GIS datasets
- Mutation records
- Building footprints
- Zoning information
- Satellite-derived spatial information

Differences can occur in:

- Parcel identifiers
- Owner-name formats
- Recorded area
- Coordinates
- Parcel geometries
- Source availability
- Dataset versions
- Duplicate records
- Historical values

BHU-SYNC connects these representations to a common parcel-centric intelligence layer, identifies discrepancies, provides spatial analysis, explains findings through a grounded AI Copilot, tracks changes over time, and supports controlled human review with an auditable workflow.

---

# 🎯 Problem Statement

Urban land information is often distributed across multiple departments and systems.

Because these systems are maintained independently, the same physical parcel may contain different information in different sources.

For example:

```text
Cadastral
Parcel: MH-KPG-1004
Owner: Rajesh More
Area: 1250 sqm

Municipal
Parcel: MH-KPG-1004
Owner: Rajesh M. More
Area: 1290 sqm

Registry
Parcel: MH-KPG-1004
Owner: Rajesh More
Area: 1251 sqm
```

This creates challenges in:

- Identifying the same physical parcel across systems
- Detecting source discrepancies
- Understanding why records differ
- Tracking changes between versions
- Reviewing conflicting information
- Maintaining source provenance
- Supporting spatial analysis

### Core Question

> **How can multiple representations of the same parcel be intelligently connected, compared, explained, tracked over time, and reviewed without losing the original source information?**

---

# 💡 Proposed Solution

BHU-SYNC creates a **parcel-centric intelligence layer** over multiple land and civic information sources.

```text
Multiple Source Datasets
        ↓
Data Ingestion
        ↓
Dataset Versioning
        ↓
Persistent Source Records
        ↓
Normalization
        ↓
Canonical Parcel Identity
        ↓
Multi-Source Matching
        ↓
Harmonization
        ↓
Conflict Detection
        ↓
Advanced GIS
        ↓
AI Copilot
        ↓
Temporal Intelligence
        ↓
Human Review Workflow
        ↓
Audit Trail
```

The platform preserves original source information while creating a unified analytical representation.

---

# ⭐ Core Capabilities

## 1. Multi-Source Data Platform

BHU-SYNC provides a persistent data ingestion and versioning foundation.

### Supported Source Categories

- Cadastral
- Municipal
- Registry
- Property Tax
- Survey
- GIS
- Mutation
- Building Footprint
- Zoning
- Satellite

### Capabilities

- CSV ingestion
- XLSX ingestion
- Source-specific field normalization
- Dataset versioning
- Persistent source records
- Raw-data preservation
- Duplicate detection
- Data-quality validation
- Source provenance
- Dataset lineage

---

# 2. Canonical Parcel Model

BHU-SYNC separates the concept of a **source record** from the **physical parcel identity**.

```text
Cadastral Record
       \
Municipal Record
        \
Registry Record -----> Canonical Parcel
        /
Survey Record
       /
GIS Record
```

Multiple source records can therefore be associated with one canonical parcel.

This enables BHU-SYNC to provide:

- A common parcel-centric view
- Source-level traceability
- Cross-source comparison
- Consistent parcel identity
- Historical lineage

---

# 3. Multi-Source Harmonization

The harmonization engine uses multiple signals to determine whether records correspond to the same parcel.

### Matching Signals

- Exact parcel identifier
- Normalized parcel identifier
- Owner-name similarity
- Area similarity
- Coordinate information
- Address similarity
- Spatial evidence

### Match Classification

```text
MATCHED
POTENTIAL_MATCH
UNMATCHED
CONFLICT
```

### Example

```text
MATCHED

Evidence:
• Parcel identifiers match
• Owner names are highly similar
• Area difference is within configured tolerance
• Spatial overlap is high
```

The matching process is deterministic and designed to remain explainable.

---

# 4. Conflict Detection

BHU-SYNC identifies discrepancies across different source representations.

### Example Conflict Types

- Owner mismatch
- Area mismatch
- Identifier mismatch
- Location mismatch
- Missing source
- Duplicate record
- Geometry mismatch
- Spatial overlap
- Invalid geometry
- Potential identity conflict

Each detected conflict can remain associated with:

- Canonical parcel
- Source record
- Source type
- Analysis run
- Relevant measurements
- Detection reason

This maintains traceability from a detected issue back to the underlying evidence.

---

# 5. 🗺️ Advanced GIS & Spatial Intelligence

BHU-SYNC treats GIS as an analytical component rather than only a visualization layer.

### Spatial Capabilities

- Parcel visualization
- Polygon support
- MultiPolygon support
- GeoJSON
- Geometry validation
- CRS handling
- Spatial intersection
- Overlap analysis
- Containment analysis
- Distance/proximity analysis
- Spatial matching
- Spatial conflict detection
- Building-footprint relationships
- Zoning relationships
- Bounding-box filtering

### Parcel Map Semantics

```text
🟢 GREEN
Harmonized

🟡 YELLOW
Conflict / Review Required

🔴 RED
Low Harmonization Score
```

These classifications are derived from the application's analytical results rather than hardcoded parcel IDs.

---

# 6. 🤖 AI Copilot 2.0

BHU-SYNC provides a natural-language AI interface over the platform.

Users can ask questions such as:

```text
Why is this parcel flagged?

Compare all sources for MH-KPG-1004.

What changed for this parcel?

Which parcels have area conflicts?

Which parcels are missing Registry data?

Show spatial conflicts near this parcel.

How many parcels require review?
```

## Grounded AI Architecture

```text
User Question
      ↓
Intent / Tool Selection
      ↓
BHU-SYNC Data Retrieval
      ↓
Grounded Context
      ↓
AI Response
      ↓
Evidence / Provenance
```

The Copilot is designed to explain information retrieved from BHU-SYNC rather than inventing parcel facts.

### AI Design Principles

- Retrieval before factual answers
- Structured database queries for exact values
- Safe predefined tools
- Evidence-aware responses
- Organization-aware access
- Permission-aware retrieval
- Hallucination controls
- Prompt-injection protections
- No arbitrary SQL
- No arbitrary code execution

The Copilot does **not** independently determine legal ownership, legally binding boundaries, or other legal outcomes.

---

# 7. 🕒 Temporal / Change Intelligence

BHU-SYNC preserves dataset and analysis history so changes can be identified over time.

### Detectable Changes

- Owner-field changes
- Area changes
- Identifier changes
- Source additions
- Source removals
- Harmonization score changes
- Status changes
- Conflict creation
- Conflict condition no longer detected
- Geometry changes
- Data-quality changes

### Example

```text
BEFORE

Area: 1250 sqm
Score: 72
Sources: 2

        ↓

AFTER

Area: 1290 sqm
Score: 84
Sources: 3

        ↓

DETECTED CHANGES

Area: +40 sqm
Score: +12
Source added: Registry
```

Previous analysis runs remain historically distinguishable from newer analysis runs.

Historical information is not intended to be overwritten simply because a newer dataset or analysis result exists.

---

# 8. 👤 Authentication & Government Roles

BHU-SYNC includes authentication and role-based access control.

### Roles

- Platform Admin
- Department Admin
- Officer
- Viewer

### Security Model

- Authentication
- Role-based permissions
- Organization-aware access
- Backend authorization
- Row Level Security
- Protected APIs

Security decisions are not delegated only to frontend visibility.

---

# 9. 🔄 Human Review Workflow

Automated analysis identifies issues.

Authorized users can investigate those issues through a controlled review workflow.

```text
Conflict Detected
       ↓
Create Review Case
       ↓
Assign Reviewer
       ↓
Investigation
       ↓
Comments / Evidence
       ↓
Decision
       ↓
Resolved
       ↓
Closed
```

BHU-SYNC maintains a distinction between:

**System Finding**

and

**Human Review Decision**

This prevents an analytical result from being silently rewritten into a human decision.

---

# 10. 📚 Evidence & Audit Trail

Workflow activity can be associated with evidence and auditable events.

### Example Workflow Events

- Case creation
- Assignment
- Reassignment
- Status change
- Comment
- Evidence addition
- Escalation
- Resolution
- Case closure
- Role changes

### Audit Information

Audit records can preserve:

- Actor
- Action
- Entity
- Timestamp
- Relevant metadata

The audit architecture uses append-oriented integrity controls.

---

# 🏗️ System Architecture

```text
                         BHU-SYNC
                            │
              ┌─────────────┴─────────────┐
              │                           │
        React Frontend              FastAPI Backend
              │                           │
              └─────────────┬─────────────┘
                            │
                   Authentication
                         + RBAC
                            │
                            ▼
                 Application Services
                            │
      ┌─────────────────────┼─────────────────────┐
      │                     │                     │
      ▼                     ▼                     ▼
 Data Platform       Harmonization            GIS
      │                     │                     │
      └─────────────────────┼─────────────────────┘
                            │
                            ▼
                       AI Copilot
                            │
                            ▼
                  Temporal Intelligence
                            │
                            ▼
                       Workflow
                            │
                            ▼
                         Audit
                            │
                            ▼
                 Supabase / PostgreSQL
                     + PostGIS
```

---

# 🧩 Technology Stack

## Frontend

- React
- TypeScript
- Vite
- Tailwind CSS
- MapLibre GL JS
- Recharts
- i18n support

## Backend

- Python
- FastAPI
- Pandas
- GeoPandas
- Shapely
- PyProj
- OpenPyXL

## Database

- Supabase
- PostgreSQL
- PostGIS
- Row Level Security

## AI

- Grounded AI Copilot
- Structured data retrieval
- Tool-based retrieval
- Provider abstraction
- Evidence/provenance-aware responses

---

# 🔄 End-to-End Data Flow

```text
                    SOURCE DATA
                         │
                         ▼
                  DATA INGESTION
                         │
                         ▼
               DATASET VERSIONING
                         │
                         ▼
                  SOURCE RECORDS
                         │
                         ▼
                NORMALIZATION
                         │
                         ▼
              CANONICAL PARCEL
                         │
                         ▼
             MULTI-SOURCE MATCHING
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
         HARMONIZATION          CONFLICTS
              │                     │
              └──────────┬──────────┘
                         ▼
                    ADVANCED GIS
                         │
                         ▼
                    AI COPILOT
                         │
                         ▼
             TEMPORAL INTELLIGENCE
                         │
                         ▼
                  HUMAN WORKFLOW
                         │
                         ▼
                       AUDIT
```

---

# 🔍 Example: Parcel Intelligence

For a parcel such as:

```text
MH-KPG-1004
```

BHU-SYNC can provide a unified intelligence view containing:

```text
Source Coverage
├── Cadastral
├── Municipal
├── Registry
├── Property Tax
└── GIS

Harmonization
├── Match Status
├── Score
└── Contributing Factors

Conflicts
├── Owner
├── Area
└── Spatial

Temporal
├── Previous State
├── Current State
└── Detected Changes

Workflow
├── Case
├── Reviewer
├── Evidence
└── Decision

Audit
└── Activity History
```

This creates a parcel-centric intelligence view without losing the underlying source records.

---

# 🔐 Security Principles

BHU-SYNC is designed around:

- Authentication
- Role-based authorization
- Organization isolation
- Row Level Security
- Backend permission enforcement
- Input validation
- Secure file processing
- Protected audit records
- AI tool restrictions
- Backend-only private credentials
- No arbitrary SQL through Copilot
- No arbitrary code execution through Copilot

Private credentials such as service-role keys, database passwords, and private AI API keys must never be exposed through the frontend.

---

# 🧪 Testing & Verification

The current verification process covers the Phase A–H roadmap.

### Reported Automated Verification

| Phase | Capability | Tests |
|---|---|---:|
| Phase A | Data Platform | 9 |
| Phase B | Authentication & RBAC | 11 |
| Phase C | Multi-Source Harmonization | 25 |
| Phase D | Advanced GIS | 30 |
| Phase E | AI Copilot 2.0 | 25 |
| Phase F | Temporal Intelligence | 34 |
| Phase G | Workflow & Audit | 36 |
| Phase H | Security & SIH Demo | 37 |
| **Total** | **A–H Roadmap** | **207** |

### Reported Results

```text
207 / 207 automated tests passed

Backend compilation:
PASS

Frontend production build:
PASS

Authentication:
VERIFIED

RLS:
VERIFIED

GIS:
VERIFIED

AI Copilot:
VERIFIED

Temporal Intelligence:
VERIFIED

Workflow:
VERIFIED

Audit:
VERIFIED

SIH Demo:
VERIFIED
```

Detailed verification is documented in:

`FULL_BHU_SYNC_VERIFICATION_REPORT.md`

---

# 📊 Project Status

| Phase | Capability | Status |
|---|---|---|
| A | Data Platform Foundation | ✅ Verified |
| B | Authentication + Government Roles | ✅ Verified |
| C | Multi-Source Harmonization | ✅ Verified |
| D | Advanced GIS + Spatial Intelligence | ✅ Verified |
| E | AI Copilot 2.0 | ✅ Verified |
| F | Temporal / Change Intelligence | ✅ Verified |
| G | Workflow + Audit | ✅ Verified |
| H | SIH Demo + Security | ✅ Verified |

> **Prototype note:** BHU-SYNC is intended for demonstration and evaluation. Real government deployment would require environment-specific infrastructure, security, data-governance, integration, and operational validation.

---

# 🎬 Recommended SIH Demonstration Flow

```text
1. Login
      ↓
2. Dashboard
      ↓
3. Data Hub
      ↓
4. Multi-Source Dataset
      ↓
5. Run Harmonization
      ↓
6. Conflict Detection
      ↓
7. Open Parcel in GIS
      ↓
8. Compare Source Records
      ↓
9. Ask AI Copilot
      ↓
10. View Temporal History
      ↓
11. Create Review Case
      ↓
12. Add Evidence
      ↓
13. Resolve Case
      ↓
14. View Audit Trail
```

This demonstrates how the major BHU-SYNC capabilities connect into one end-to-end workflow.

---

# 📁 Repository Structure

```text
BHU-SYNC/
│
├── backend/
│   ├── main.py
│   ├── routers/
│   ├── services/
│   ├── migrations/
│   ├── data/
│   └── test_*.py
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── i18n/
│   │   └── ...
│   ├── public/
│   └── package.json
│
├── demo_data/
│
├── PHASE_A_IMPLEMENTATION_REPORT.md
├── PHASE_B_IMPLEMENTATION_REPORT.md
├── PHASE_C_IMPLEMENTATION_REPORT.md
├── PHASE_D_IMPLEMENTATION_REPORT.md
├── PHASE_E_IMPLEMENTATION_REPORT.md
├── PHASE_F_IMPLEMENTATION_REPORT.md
├── PHASE_G_IMPLEMENTATION_REPORT.md
├── PHASE_H_IMPLEMENTATION_REPORT.md
├── FULL_BHU_SYNC_VERIFICATION_REPORT.md
├── SIH_DEMO_WALKTHROUGH.md
├── LOCAL_SETUP.md
└── README.md
```

---

# ⚙️ Local Setup

## Prerequisites

- Python 3.13+
- Node.js
- npm
- Supabase project/configuration

## Backend

From the repository root:

```powershell
cd backend
python -m uvicorn main:app --reload
```

Backend:

```text
http://127.0.0.1:8000
```

## Frontend

Open another terminal:

```powershell
cd frontend
npm run dev
```

Frontend:

```text
http://localhost:5173
```

---

# 🔑 Environment Configuration

The frontend uses Vite environment variables.

Example:

```env
VITE_SUPABASE_URL=https://YOUR_PROJECT_ID.supabase.co
VITE_SUPABASE_ANON_KEY=YOUR_PUBLIC_ANON_KEY
```

### Never commit

```text
.env
.env.local
database passwords
service-role keys
private AI API keys
private access tokens
```

Use `.env.example` for placeholders and documentation.

---

# 🗃️ Database Architecture

Core data concepts include:

```text
datasets
dataset_versions
source_records
canonical_parcels
parcel_source_links
analysis_runs
analysis_changes
conflicts
harmonized_records

profiles
organizations
roles
permissions

workflow_cases
workflow_case_comments
workflow_case_evidence
workflow_case_events

audit_logs
```

The spatial layer uses PostgreSQL/PostGIS where enabled.

---

# 🧠 Design Principles

## Preserve Source Truth

Original source values remain traceable.

## Explainability

Matching and conflict results expose supporting evidence.

## Non-Destructive Analysis

Previous analysis runs remain historically distinguishable.

## Parcel-Centric Intelligence

Multiple source records can be associated with one canonical parcel.

## Human-in-the-Loop

System findings support authorized human review rather than replacing human decisions.

## Security by Design

Authentication, authorization, organization isolation and database security are considered throughout the architecture.

## Spatial Intelligence

GIS is used for analytical comparison rather than only visualization.

---

# 📦 Synthetic Demo Dataset

The repository may contain synthetic datasets for demonstration and testing.

Example sources include:

- Cadastral
- Municipal
- Registry
- Property Tax
- Survey
- GIS
- Mutation
- Building Footprint
- Zoning

The demo dataset is designed to demonstrate:

- Source reconciliation
- Matching
- Conflicts
- Missing data
- Spatial differences
- Temporal changes
- AI explanations
- Workflow review
- Auditability

> **Important:** Demonstration datasets are synthetic and are not official government land records.

---

# ⚠️ Domain & Prototype Limitations

BHU-SYNC is an intelligence and harmonization platform.

It does **not** independently determine:

- Legal ownership
- Legal title
- Legally binding boundaries
- Court decisions
- Government approval
- Final legal status of a parcel

The platform identifies discrepancies and provides evidence for authorized human review.

Real-world government deployment would require:

- Data-governance validation
- Security assessment
- Department-specific access policies
- Integration validation
- Production infrastructure
- Operational monitoring
- Legal and regulatory review
- Real-data validation

---

# 📚 Project Documentation

Additional documentation is available in the repository:

- `PHASE_A_IMPLEMENTATION_REPORT.md`
- `PHASE_B_IMPLEMENTATION_REPORT.md`
- `PHASE_C_IMPLEMENTATION_REPORT.md`
- `PHASE_D_IMPLEMENTATION_REPORT.md`
- `PHASE_E_IMPLEMENTATION_REPORT.md`
- `PHASE_F_IMPLEMENTATION_REPORT.md`
- `PHASE_G_IMPLEMENTATION_REPORT.md`
- `PHASE_H_IMPLEMENTATION_REPORT.md`
- `FULL_BHU_SYNC_VERIFICATION_REPORT.md`
- `SIH_DEMO_WALKTHROUGH.md`
- `LOCAL_SETUP.md`

For a complete verification overview, start with:

`FULL_BHU_SYNC_VERIFICATION_REPORT.md`

For demonstration flow, see:

`SIH_DEMO_WALKTHROUGH.md`

---

# 🎥 Prototype Demonstration

## YouTube Demo

Add the final prototype demonstration URL below:

```text
YOUTUBE_VIDEO_LINK
```

Example:

```markdown
[▶️ Watch BHU-SYNC Prototype Demo](https://youtu.be/rpeMOIMkdyo)
```

---

# 🔗 GitHub Repository

**Repository:**

https://github.com/sahils-44/BHU-SYNC-AI-Powered-Urban-Land-Record-Harmonization-Intelligence-Platform

---

# 🏆 Smart India Hackathon

## Team TechX Titan

**Project:**

### BHU-SYNC — AI-Powered Urban Land Record Harmonization & Intelligence Platform

BHU-SYNC combines:

```text
Data Engineering
+
Multi-Source Harmonization
+
GIS
+
Artificial Intelligence
+
Temporal Intelligence
+
Human Review
+
Auditability
+
Security
```

into a unified parcel-centric intelligence platform.

---

# 👥 Team

## TechX Titan

**Smart India Hackathon Prototype Team**

**Project:** BHU-SYNC

> **One Plot. One Truth. Multiple Sources, Intelligently Synced.**

---

# 🌐 Repository & Prototype Links

| Resource | Link |
|---|---|
| GitHub Repository | https://github.com/sahils-44/BHU-SYNC-AI-Powered-Urban-Land-Record-Harmonization-Intelligence-Platform |
| YouTube Prototype Demo | Add your final YouTube link |
| Live Prototype | Add deployment URL if available |

---

# 🚀 Project Vision

BHU-SYNC aims to provide a unified intelligence layer for heterogeneous land and civic information.

Instead of treating every dataset independently, the platform connects multiple representations of a parcel and provides:

```text
One Parcel
    ↓
Multiple Sources
    ↓
One Connected Intelligence View
```

The long-term vision is to help authorized users understand:

- What data exists?
- Which records refer to the same parcel?
- Where do sources disagree?
- What spatial inconsistencies exist?
- What changed over time?
- Why was a parcel flagged?
- What evidence supports the finding?
- What human review has taken place?
- What actions were recorded?

---

# 🔬 Why BHU-SYNC?

BHU-SYNC is designed around a core principle:

> **Different systems may describe the same parcel differently. The platform should connect those representations, identify discrepancies, explain the evidence, preserve history, and support human review.**

Rather than building only:

- a standalone GIS viewer
- a standalone chatbot
- a standalone database

BHU-SYNC combines:

```text
Data Platform
       +
Multi-Source Harmonization
       +
GIS
       +
AI
       +
Temporal Intelligence
       +
Workflow
       +
Auditability
       +
Security
```

into a unified parcel-centric intelligence platform.

---

# 📌 Project Status

```text
Phase A  ✅ Data Platform Foundation
Phase B  ✅ Authentication + Government Roles
Phase C  ✅ Multi-Source Harmonization
Phase D  ✅ Advanced GIS + Spatial Intelligence
Phase E  ✅ AI Copilot 2.0
Phase F  ✅ Temporal / Change Intelligence
Phase G  ✅ Workflow + Audit
Phase H  ✅ SIH Demo + Security
```

### Verification

```text
207 reported automated tests
Backend compilation: PASS
Frontend production build: PASS
```

The repository contains the detailed implementation and verification reports for each phase.

---

# 📄 License

Add the license appropriate for the team's intended distribution and Smart India Hackathon submission requirements.

---

# 🙌 Acknowledgement

Developed by **Team TechX Titan** as a Smart India Hackathon-oriented prototype demonstrating:

- AI-assisted land-record intelligence
- Multi-source data harmonization
- GIS-based spatial analysis
- Temporal change intelligence
- Controlled human review
- Traceable auditability
- Security-aware architecture

---

<p align="center">

# BHU-SYNC

### One Plot. One Truth. Multiple Sources, Intelligently Synced.

**Developed by Team TechX Titan**

**Smart India Hackathon Prototype**

</p>