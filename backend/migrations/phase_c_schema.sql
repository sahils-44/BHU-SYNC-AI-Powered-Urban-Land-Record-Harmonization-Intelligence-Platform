-- ====================================================================
-- BHU-SYNC Phase C: Multi-Source Harmonization Additive Schema
-- ====================================================================

-- Add source record provenance and source category columns if not present
ALTER TABLE IF EXISTS public.source_records
  ADD COLUMN IF NOT EXISTS source_category TEXT DEFAULT 'REVENUE',
  ADD COLUMN IF NOT EXISTS authority_weight NUMERIC(3,2) DEFAULT 0.50,
  ADD COLUMN IF NOT EXISTS normalized_data JSONB DEFAULT '{}'::jsonb;

-- Add provenance tracking to harmonized records
ALTER TABLE IF EXISTS public.harmonized_records
  ADD COLUMN IF NOT EXISTS source_provenance JSONB DEFAULT '{}'::jsonb,
  ADD COLUMN IF NOT EXISTS consensus_metrics JSONB DEFAULT '{}'::jsonb;

-- Add index on source_category
CREATE INDEX IF NOT EXISTS idx_source_records_category ON public.source_records(source_category);
