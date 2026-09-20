-- ==============================================================================
-- BHU-SYNC: Phase A Master Schema Reference & Migration Definition
-- AI-Powered Urban Land Record Harmonization & Intelligence Platform
-- ==============================================================================
-- Note: These tables constitute the non-destructive Phase-A data architecture foundation.
-- All operations use IF NOT EXISTS / ADD COLUMN IF NOT EXISTS to guarantee safety.

-- 1. DATASETS
CREATE TABLE IF NOT EXISTS public.datasets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    source_type TEXT NOT NULL DEFAULT 'CADASTRAL',
    file_name TEXT,
    file_path TEXT,
    record_count INTEGER DEFAULT 0,
    quality_score NUMERIC(5, 2) DEFAULT 0.0,
    status TEXT DEFAULT 'processed',
    uploaded_by TEXT,
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_datasets_name ON public.datasets(name);
CREATE INDEX IF NOT EXISTS idx_datasets_source_type ON public.datasets(source_type);

-- 2. DATASET VERSIONS
CREATE TABLE IF NOT EXISTS public.dataset_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_id UUID REFERENCES public.datasets(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL DEFAULT 1,
    record_count INTEGER DEFAULT 0,
    quality_score NUMERIC(5, 2) DEFAULT 0.0,
    status TEXT DEFAULT 'processed',
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL,
    CONSTRAINT uq_dataset_version UNIQUE(dataset_id, version_number)
);

CREATE INDEX IF NOT EXISTS idx_dataset_versions_dataset_id ON public.dataset_versions(dataset_id);

-- 3. SOURCE RECORDS (Raw & Normalized Records Ingested from Datasets)
CREATE TABLE IF NOT EXISTS public.source_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_id UUID REFERENCES public.datasets(id) ON DELETE CASCADE,
    version_id UUID REFERENCES public.dataset_versions(id) ON DELETE CASCADE,
    source_type TEXT NOT NULL,
    parcel_id TEXT NOT NULL,
    owner_name TEXT,
    area NUMERIC(12, 2),
    ward INTEGER,
    latitude NUMERIC(10, 6),
    longitude NUMERIC(10, 6),
    raw_data JSONB,
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_source_records_parcel_id ON public.source_records(parcel_id);
CREATE INDEX IF NOT EXISTS idx_source_records_version_id ON public.source_records(version_id);
CREATE INDEX IF NOT EXISTS idx_source_records_dataset_id ON public.source_records(dataset_id);
CREATE INDEX IF NOT EXISTS idx_source_records_source_type ON public.source_records(source_type);

-- 4. ANALYSIS RUNS (Telemetry and History for Pipeline Executions)
CREATE TABLE IF NOT EXISTS public.analysis_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cadastral_dataset_id UUID REFERENCES public.datasets(id),
    cadastral_version_id UUID REFERENCES public.dataset_versions(id),
    municipal_dataset_id UUID REFERENCES public.datasets(id),
    municipal_version_id UUID REFERENCES public.dataset_versions(id),
    status TEXT DEFAULT 'completed',
    records_compared INTEGER DEFAULT 0,
    conflicts_detected INTEGER DEFAULT 0,
    harmonized_records_count INTEGER DEFAULT 0,
    started_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL,
    completed_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_analysis_runs_started_at ON public.analysis_runs(started_at DESC);

-- 5. CANONICAL PARCELS (Consensus Truth Layer)
CREATE TABLE IF NOT EXISTS public.canonical_parcels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parcel_id TEXT NOT NULL UNIQUE,
    owner_name TEXT,
    area NUMERIC(12, 2),
    ward INTEGER,
    latitude NUMERIC(10, 6),
    longitude NUMERIC(10, 6),
    harmonization_score NUMERIC(5, 2) DEFAULT 0.0,
    status TEXT DEFAULT 'Harmonized',
    source_count INTEGER DEFAULT 1,
    matching_sources INTEGER DEFAULT 1,
    conflict_count INTEGER DEFAULT 0,
    explanation TEXT,
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_canonical_parcels_parcel_id ON public.canonical_parcels(parcel_id);
CREATE INDEX IF NOT EXISTS idx_canonical_parcels_status ON public.canonical_parcels(status);

-- 6. PARCEL SOURCE LINKS (Audit Linkage from Canonical Parcels to Raw Ingested Source Records)
CREATE TABLE IF NOT EXISTS public.parcel_source_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    canonical_parcel_id UUID REFERENCES public.canonical_parcels(id) ON DELETE CASCADE,
    source_record_id UUID REFERENCES public.source_records(id) ON DELETE CASCADE,
    match_method TEXT DEFAULT 'EXACT_PARCEL_ID',
    match_score NUMERIC(5, 2) DEFAULT 100.0,
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_parcel_source_links_canonical ON public.parcel_source_links(canonical_parcel_id);
CREATE INDEX IF NOT EXISTS idx_parcel_source_links_source ON public.parcel_source_links(source_record_id);

-- 7. HARMONIZED RECORDS (Run-scoped historical results)
-- Ensure analysis_run_id column exists
ALTER TABLE IF EXISTS public.harmonized_records 
    ADD COLUMN IF NOT EXISTS analysis_run_id UUID REFERENCES public.analysis_runs(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_harmonized_records_run_id ON public.harmonized_records(analysis_run_id);
CREATE INDEX IF NOT EXISTS idx_harmonized_records_parcel_id ON public.harmonized_records(parcel_id);

-- 8. CONFLICTS (Run-scoped historical discrepancies)
-- Ensure analysis_run_id column exists
ALTER TABLE IF EXISTS public.conflicts 
    ADD COLUMN IF NOT EXISTS analysis_run_id UUID REFERENCES public.analysis_runs(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_conflicts_run_id ON public.conflicts(analysis_run_id);
CREATE INDEX IF NOT EXISTS idx_conflicts_parcel_id ON public.conflicts(parcel_id);
CREATE INDEX IF NOT EXISTS idx_conflicts_status ON public.conflicts(status);

-- 9. ANALYSIS CHANGES (Run-to-Run Delta and Anomaly Tracking)
CREATE TABLE IF NOT EXISTS public.analysis_changes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    from_run_id UUID REFERENCES public.analysis_runs(id) ON DELETE CASCADE,
    to_run_id UUID REFERENCES public.analysis_runs(id) ON DELETE CASCADE,
    parcel_id TEXT NOT NULL,
    change_type TEXT NOT NULL, -- NEW_PARCEL, REMOVED_PARCEL, OWNER_CHANGED, AREA_CHANGED, WARD_CHANGED, SCORE_CHANGED, NEW_CONFLICT, RESOLVED_CONFLICT
    field_name TEXT,
    old_value TEXT,
    new_value TEXT,
    difference NUMERIC(12, 2),
    description TEXT,
    severity TEXT DEFAULT 'MEDIUM',
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_analysis_changes_runs ON public.analysis_changes(from_run_id, to_run_id);
CREATE INDEX IF NOT EXISTS idx_analysis_changes_parcel ON public.analysis_changes(parcel_id);
