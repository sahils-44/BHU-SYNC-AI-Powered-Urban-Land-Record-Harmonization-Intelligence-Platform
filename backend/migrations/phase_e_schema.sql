-- ====================================================================
-- BHU-SYNC Phase E: AI Copilot 2.0 Additive Schema
-- ====================================================================

CREATE TABLE IF NOT EXISTS public.copilot_queries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_id UUID REFERENCES public.profiles(id),
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    grounding_status TEXT DEFAULT 'GROUNDED_100_PERCENT',
    citations JSONB DEFAULT '[]'::jsonb,
    map_actions JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_copilot_queries_actor ON public.copilot_queries(actor_id);
