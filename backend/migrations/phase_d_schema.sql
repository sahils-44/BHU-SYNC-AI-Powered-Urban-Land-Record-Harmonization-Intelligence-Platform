-- ====================================================================
-- BHU-SYNC Phase D: Advanced GIS & Spatial Additive Schema
-- ====================================================================

-- Add polygon geometry and spatial attributes
ALTER TABLE IF EXISTS public.canonical_parcels
  ADD COLUMN IF NOT EXISTS geometry JSONB DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS srid INTEGER DEFAULT 4326,
  ADD COLUMN IF NOT EXISTS planar_area_sqm NUMERIC(12,2) DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS zoning_zone TEXT DEFAULT 'RESIDENTIAL_R1';

-- Spatial index on geometry
CREATE INDEX IF NOT EXISTS idx_canonical_parcels_geom_jsonb ON public.canonical_parcels USING gin(geometry);
