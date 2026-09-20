-- ====================================================================
-- BHU-SYNC Phase F: Temporal & Change Intelligence Additive Schema
-- ====================================================================

CREATE TABLE IF NOT EXISTS public.parcel_timeline_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parcel_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    actor_id UUID,
    description TEXT,
    before_state JSONB DEFAULT NULL,
    after_state JSONB DEFAULT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_timeline_parcel ON public.parcel_timeline_events(parcel_id);
CREATE INDEX IF NOT EXISTS idx_timeline_type ON public.parcel_timeline_events(event_type);
