-- ====================================================================
-- BHU-SYNC Phase G: Workflow & SHA-256 Audit Additive Schema
-- ====================================================================

CREATE TABLE IF NOT EXISTS public.workflow_cases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id TEXT UNIQUE NOT NULL,
    parcel_id TEXT NOT NULL,
    title TEXT NOT NULL,
    priority TEXT DEFAULT 'MEDIUM',
    status TEXT DEFAULT 'NEW',
    assigned_to TEXT,
    organization_id TEXT,
    notes JSONB DEFAULT '[]'::jsonb,
    evidence JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_id TEXT NOT NULL,
    action TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    resource_id TEXT NOT NULL,
    payload JSONB DEFAULT '{}'::jsonb,
    previous_hash TEXT NOT NULL,
    hash TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_workflow_status ON public.workflow_cases(status);
CREATE INDEX IF NOT EXISTS idx_workflow_parcel ON public.workflow_cases(parcel_id);
CREATE INDEX IF NOT EXISTS idx_audit_resource ON public.audit_logs(resource_type, resource_id);
