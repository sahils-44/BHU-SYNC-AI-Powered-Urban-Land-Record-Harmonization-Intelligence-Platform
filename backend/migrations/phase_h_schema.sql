-- ====================================================================
-- BHU-SYNC Phase H: SIH Demo Mode & Security Hardening Additive Schema
-- ====================================================================

-- Add is_demo flag for clean environment isolation
ALTER TABLE IF EXISTS public.datasets
  ADD COLUMN IF NOT EXISTS is_demo BOOLEAN DEFAULT FALSE;

ALTER TABLE IF EXISTS public.canonical_parcels
  ADD COLUMN IF NOT EXISTS is_demo BOOLEAN DEFAULT FALSE;

ALTER TABLE IF EXISTS public.workflow_cases
  ADD COLUMN IF NOT EXISTS is_demo BOOLEAN DEFAULT FALSE;

CREATE INDEX IF NOT EXISTS idx_canonical_parcels_demo ON public.canonical_parcels(is_demo);
CREATE INDEX IF NOT EXISTS idx_workflow_cases_demo ON public.workflow_cases(is_demo);
