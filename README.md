# BHU-SYNC

## AI-Powered Urban Land Record Harmonization & Intelligence Platform

> **One Plot. One Truth. Multiple Sources, Intelligently Synced.**

**Smart India Hackathon Prototype**  
**Team: TechX Titan**

---

## 💡 Proposed Solution

BHU-SYNC creates a parcel-centric intelligence layer over multiple sources.

```text
Multiple Source Datasets
        ↓
Data Ingestion
        ↓
Dataset Versioning
        ↓
Source Records
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

⭐ Core Capabilities
1. Multi-Source Data Platform

BHU-SYNC provides a persistent data ingestion and versioning foundation.

Supported source categories:

Cadastral
Municipal
Registry
Property Tax
Survey
GIS
Mutation
Building Footprint
Zoning
Satellite

Capabilities:

CSV ingestion
XLSX ingestion
Source-specific field normalization
Dataset versioning
Persistent source records
Raw-data preservation
Duplicate detection
Data-quality validation
Source provenance
2. Canonical Parcel Model

BHU-SYNC separates the concept of a source record from the physical parcel identity.

Cadastral Record
       \
Municipal Record
        \
Registry Record -----> Canonical Parcel
        /
Survey Record
       /
GIS Record

Multiple source records can therefore be associated with one canonical parcel.

This provides a common parcel-centric view while preserving source-level information.

🔗 Multi-Source Harmonization

The harmonization engine uses multiple signals to determine whether records correspond to the same parcel.

Matching signals include:

Exact parcel identifier
Normalized parcel identifier
Owner-name similarity
Area similarity
Coordinate information
Address similarity
Spatial evidence

The resulting decision is deterministic and explainable.

Example:

MATCHED

Evidence:
• Parcel identifiers match
• Owner names are highly similar
• Area difference is within configured tolerance
• Spatial overlap is high

Possible classifications:

MATCHED
POTENTIAL_MATCH
UNMATCHED
CONFLICT
⚠️ Conflict Detection

BHU-SYNC identifies discrepancies across source records.

Examples:

Owner mismatch
Area mismatch
Identifier mismatch
Location mismatch
Missing source
Duplicate record
Geometry mismatch
Spatial overlap
Invalid geometry
Potential identity conflict

Each conflict remains linked to:

Parcel
Source record
Source type
Analysis run
Relevant measurements
Detection reason
🗺️ Advanced GIS & Spatial Intelligence

BHU-SYNC treats GIS as an analytical component rather than only a map.

Capabilities include:

Parcel visualization
Polygon support
MultiPolygon support
GeoJSON
Geometry validation
CRS handling
Spatial intersection
Overlap analysis
Containment analysis
Distance/proximity analysis
Spatial matching
Spatial conflict detection
Building-footprint relationships
Zoning relationships
Bounding-box filtering
Parcel Map Semantics

🟢 GREEN — Harmonized

🟡 YELLOW — Conflict / Review Required

🔴 RED — Low Harmonization Score

The visualization is derived from live analysis results rather than hardcoded parcel IDs.

🤖 AI Copilot 2.0

BHU-SYNC provides a natural-language AI interface over the platform.

Users can ask questions such as:

Why is this parcel flagged?

Compare all sources for MH-KPG-1004.

What changed for this parcel?

Which parcels have area conflicts?

Which parcels are missing Registry data?

Show spatial conflicts near this parcel.

How many parcels require review?
Grounded AI Architecture
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

The Copilot is designed to explain information retrieved from BHU-SYNC rather than inventing parcel facts.

It does not independently determine legal ownership, legally binding boundaries, or other legal outcomes.

🕒 Temporal / Change Intelligence

BHU-SYNC preserves dataset and analysis history so changes can be identified over time.

The system can detect:

Owner-field changes
Area changes
Identifier changes
Source additions
Source removals
Harmonization score changes
Status changes
Conflict creation
Conflict condition no longer detected
Geometry changes
Data-quality changes

Example:

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

Previous analysis runs remain historically distinguishable from newer runs.

👤 Authentication & Government Roles

BHU-SYNC includes an authentication and role-based access foundation.

Roles include:

Platform Admin
Department Admin
Officer
Viewer

The platform uses:

Authentication
Role-based permissions
Organization-aware access
Backend authorization
Row Level Security

Security decisions are not delegated only to frontend visibility.

🔄 Human Review Workflow

Automated analysis identifies issues.

Authorized users can investigate those issues through a controlled workflow.

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

BHU-SYNC keeps a clear distinction between:

System Finding

and

Human Review Decision

The workflow does not replace the underlying analytical result.

📚 Evidence & Audit Trail

Workflow activity can be associated with evidence and auditable events.

Examples:

Case creation
Assignment
Reassignment
Status change
Comment
Evidence addition
Escalation
Resolution
Case closure
Role changes

Audit records can preserve:

Actor
Action
Entity
Timestamp
Relevant metadata

The audit architecture uses append-oriented integrity controls.

🏗️ System Architecture
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
🧩 Technology Stack
Frontend
React
TypeScript
Vite
Tailwind CSS
MapLibre GL JS
Recharts
i18n support
Backend
Python
FastAPI
Pandas
GeoPandas
Shapely
PyProj
OpenPyXL
Database
Supabase
PostgreSQL
PostGIS
Row Level Security
AI
Grounded AI Copilot
Structured data retrieval
Tool-based retrieval
Provider abstraction
Evidence/provenance-aware responses

Then continue with the remaining sections from the version I gave you earlier: **End-to-End Data Flow → Example Parcel Intelligence → Security → Testing → Project Phases → SIH Demo → Repository Structure → Local Setup → Environment Variables → Database → Limitations → Documentation → YouTube → GitHub → Team TechX Titan**.

### One important correction to your current version

Instead of:

```text
📊 Project Status
A — Data Platform ✅
...
H — SIH Demo + Security ✅

I'd use:

## 📊 Project Status

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

> **Prototype note:** BHU-SYNC is intended for demonstration and evaluation. Real government deployment would require environment-specific infrastructure, security, data-governance, and operational validation.