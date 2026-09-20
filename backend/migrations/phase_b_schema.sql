-- ==============================================================================
-- BHU-SYNC PHASE B: AUTHENTICATION + GOVERNMENT ROLES SCHEMA
-- Migration: phase_b_schema.sql
-- Description: Non-destructive migration for Government RBAC and Profiles
-- ==============================================================================

-- 1. ORGANIZATIONS TABLE
CREATE TABLE IF NOT EXISTS public.organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    code TEXT NOT NULL UNIQUE,
    organization_type TEXT NOT NULL, -- 'MUNICIPAL', 'REVENUE', 'SURVEY', 'LAND_RECORDS'
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by UUID,
    updated_by UUID
);

-- Index for organization code lookups
CREATE INDEX IF NOT EXISTS idx_organizations_code ON public.organizations(code);
CREATE INDEX IF NOT EXISTS idx_organizations_is_active ON public.organizations(is_active);

-- 2. ROLES TABLE
CREATE TABLE IF NOT EXISTS public.roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE, -- 'PLATFORM_ADMIN', 'DEPARTMENT_ADMIN', 'OFFICER', 'VIEWER'
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Index for role name lookups
CREATE INDEX IF NOT EXISTS idx_roles_name ON public.roles(name);

-- 3. PERMISSIONS TABLE
CREATE TABLE IF NOT EXISTS public.permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT,
    module TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Index for permission code lookups
CREATE INDEX IF NOT EXISTS idx_permissions_code ON public.permissions(code);
CREATE INDEX IF NOT EXISTS idx_permissions_module ON public.permissions(module);

-- 4. ROLE_PERMISSIONS JUNCTION TABLE
CREATE TABLE IF NOT EXISTS public.role_permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role_id UUID NOT NULL REFERENCES public.roles(id) ON DELETE CASCADE,
    permission_id UUID NOT NULL REFERENCES public.permissions(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_role_permission UNIQUE (role_id, permission_id)
);

-- Indexes for role_permissions lookups
CREATE INDEX IF NOT EXISTS idx_role_permissions_role ON public.role_permissions(role_id);
CREATE INDEX IF NOT EXISTS idx_role_permissions_perm ON public.role_permissions(permission_id);

-- 5. USER PROFILES TABLE (Associated with auth.users)
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    organization_id UUID REFERENCES public.organizations(id) ON DELETE SET NULL,
    role_id UUID REFERENCES public.roles(id) ON DELETE SET NULL,
    department TEXT,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by UUID,
    updated_by UUID
);

CREATE INDEX IF NOT EXISTS idx_profiles_organization_id ON public.profiles(organization_id);
CREATE INDEX IF NOT EXISTS idx_profiles_role_id ON public.profiles(role_id);
CREATE INDEX IF NOT EXISTS idx_profiles_email ON public.profiles(email);
CREATE INDEX IF NOT EXISTS idx_profiles_is_active ON public.profiles(is_active);

-- ==============================================================================
-- SEED DATA: ORGANIZATIONS, ROLES, PERMISSIONS, ROLE_PERMISSIONS
-- ==============================================================================

-- Seed Organizations
INSERT INTO public.organizations (id, name, code, organization_type, is_active)
VALUES
    ('00000000-0000-0000-0000-000000000001', 'Municipal Corporation', 'MUNICIPAL_CORP', 'MUNICIPAL', true),
    ('00000000-0000-0000-0000-000000000002', 'Revenue Department', 'REVENUE_DEPT', 'REVENUE', true),
    ('00000000-0000-0000-0000-000000000003', 'Survey and Settlement Department', 'SURVEY_DEPT', 'SURVEY', true),
    ('00000000-0000-0000-0000-000000000004', 'Land Records Directorate', 'LAND_RECORDS_DEPT', 'LAND_RECORDS', true)
ON CONFLICT (code) DO UPDATE
SET name = EXCLUDED.name, organization_type = EXCLUDED.organization_type, is_active = EXCLUDED.is_active;

-- Seed Roles
INSERT INTO public.roles (id, name, description, is_active)
VALUES
    ('10000000-0000-0000-0000-000000000001', 'PLATFORM_ADMIN', 'Platform-level administrator with complete system access', true),
    ('10000000-0000-0000-0000-000000000002', 'DEPARTMENT_ADMIN', 'Department administrator managing organization members and operations', true),
    ('10000000-0000-0000-0000-000000000003', 'OFFICER', 'Operational officer executing ingestion, analysis, and reviews', true),
    ('10000000-0000-0000-0000-000000000004', 'VIEWER', 'Read-only viewer accessing dashboards, GIS, and reports', true)
ON CONFLICT (name) DO UPDATE
SET description = EXCLUDED.description, is_active = EXCLUDED.is_active;

-- Seed Permissions (15 Standard Permissions)
INSERT INTO public.permissions (id, code, name, description, module)
VALUES
    ('20000000-0000-0000-0000-000000000001', 'dashboard.view', 'View Dashboard', 'Access KPI metrics and telemetry', 'dashboard'),
    ('20000000-0000-0000-0000-000000000002', 'datasets.view', 'View Datasets', 'List and view uploaded datasets and versions', 'datasets'),
    ('20000000-0000-0000-0000-000000000003', 'datasets.upload', 'Upload Datasets', 'Upload Cadastral and Municipal data files', 'datasets'),
    ('20000000-0000-0000-0000-000000000004', 'analysis.view', 'View Analysis', 'Inspect analysis runs and change telemetry', 'analysis'),
    ('20000000-0000-0000-0000-000000000005', 'analysis.run', 'Execute Analysis', 'Trigger harmonization and conflict analysis', 'analysis'),
    ('20000000-0000-0000-0000-000000000006', 'conflicts.view', 'View Conflicts', 'Inspect identified parcel discrepancies', 'conflicts'),
    ('20000000-0000-0000-0000-000000000007', 'conflicts.update', 'Update Conflicts', 'Update conflict status and resolutions', 'conflicts'),
    ('20000000-0000-0000-0000-000000000008', 'harmonization.view', 'View Harmonization', 'Inspect unified canonical records', 'harmonization'),
    ('20000000-0000-0000-0000-000000000009', 'harmonization.run', 'Run Harmonization', 'Trigger harmonization pipeline execution', 'harmonization'),
    ('20000000-0000-0000-0000-000000000010', 'gis.view', 'View GIS Map', 'Inspect spatial parcels on interactive map', 'gis'),
    ('20000000-0000-0000-0000-000000000011', 'source_comparison.view', 'View Source Comparison', 'Compare raw source records with canonical parcel', 'analysis'),
    ('20000000-0000-0000-0000-000000000012', 'users.view', 'View Users', 'View organization user profiles and roles', 'admin'),
    ('20000000-0000-0000-0000-000000000013', 'users.manage', 'Manage Users', 'Activate, deactivate, or assign department users', 'admin'),
    ('20000000-0000-0000-0000-000000000014', 'organization.manage', 'Manage Organizations', 'Configure department and administrative units', 'admin'),
    ('20000000-0000-0000-0000-000000000015', 'roles.manage', 'Manage Roles', 'Manage RBAC role assignments and permissions', 'admin')
ON CONFLICT (code) DO UPDATE
SET name = EXCLUDED.name, description = EXCLUDED.description, module = EXCLUDED.module;

-- Seed Role Permissions: PLATFORM_ADMIN (All 15 permissions)
INSERT INTO public.role_permissions (role_id, permission_id)
SELECT '10000000-0000-0000-0000-000000000001', id FROM public.permissions
ON CONFLICT (role_id, permission_id) DO NOTHING;

-- Seed Role Permissions: DEPARTMENT_ADMIN (13 permissions)
INSERT INTO public.role_permissions (role_id, permission_id)
SELECT '10000000-0000-0000-0000-000000000002', id FROM public.permissions
WHERE code IN (
    'dashboard.view', 'datasets.view', 'datasets.upload',
    'analysis.view', 'analysis.run', 'conflicts.view', 'conflicts.update',
    'harmonization.view', 'harmonization.run', 'gis.view',
    'source_comparison.view', 'users.view', 'users.manage', 'organization.manage'
)
ON CONFLICT (role_id, permission_id) DO NOTHING;

-- Seed Role Permissions: OFFICER (11 operational permissions)
INSERT INTO public.role_permissions (role_id, permission_id)
SELECT '10000000-0000-0000-0000-000000000003', id FROM public.permissions
WHERE code IN (
    'dashboard.view', 'datasets.view', 'datasets.upload',
    'analysis.view', 'analysis.run', 'conflicts.view', 'conflicts.update',
    'harmonization.view', 'harmonization.run', 'gis.view',
    'source_comparison.view'
)
ON CONFLICT (role_id, permission_id) DO NOTHING;

-- Seed Role Permissions: VIEWER (7 read-only permissions)
INSERT INTO public.role_permissions (role_id, permission_id)
SELECT '10000000-0000-0000-0000-000000000004', id FROM public.permissions
WHERE code IN (
    'dashboard.view', 'datasets.view', 'analysis.view',
    'conflicts.view', 'harmonization.view', 'gis.view',
    'source_comparison.view'
)
ON CONFLICT (role_id, permission_id) DO NOTHING;

-- ==============================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- ==============================================================================

ALTER TABLE public.organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.permissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.role_permissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- Helper function to get current user profile in RLS
CREATE OR REPLACE FUNCTION public.get_current_profile()
RETURNS TABLE (
    id UUID,
    organization_id UUID,
    role_name TEXT,
    is_active BOOLEAN
) SECURITY DEFINER STABLE AS $$
BEGIN
    RETURN QUERY
    SELECT p.id, p.organization_id, r.name AS role_name, p.is_active
    FROM public.profiles p
    LEFT JOIN public.roles r ON p.role_id = r.id
    WHERE p.id = auth.uid();
END;
$$ LANGUAGE plpgsql;

-- Organizations RLS
DROP POLICY IF EXISTS "Active users can view organizations" ON public.organizations;
CREATE POLICY "Active users can view organizations"
    ON public.organizations FOR SELECT
    TO authenticated
    USING (is_active = true);

-- Roles and Permissions RLS
DROP POLICY IF EXISTS "Authenticated users can view roles" ON public.roles;
CREATE POLICY "Authenticated users can view roles"
    ON public.roles FOR SELECT
    TO authenticated
    USING (is_active = true);

DROP POLICY IF EXISTS "Authenticated users can view permissions" ON public.permissions;
CREATE POLICY "Authenticated users can view permissions"
    ON public.permissions FOR SELECT
    TO authenticated
    USING (true);

DROP POLICY IF EXISTS "Authenticated users can view role permissions" ON public.role_permissions;
CREATE POLICY "Authenticated users can view role permissions"
    ON public.role_permissions FOR SELECT
    TO authenticated
    USING (true);

-- Profiles RLS:
DROP POLICY IF EXISTS "Profiles visibility policy" ON public.profiles;
CREATE POLICY "Profiles visibility policy"
    ON public.profiles FOR SELECT
    TO authenticated
    USING (
        id = auth.uid() OR
        EXISTS (
            SELECT 1 FROM public.get_current_profile() cp
            WHERE (cp.role_name = 'PLATFORM_ADMIN' OR
                  (cp.role_name = 'DEPARTMENT_ADMIN' AND cp.organization_id = profiles.organization_id))
              AND cp.is_active = true
        )
    );

DROP POLICY IF EXISTS "Profiles update policy" ON public.profiles;
CREATE POLICY "Profiles update policy"
    ON public.profiles FOR UPDATE
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.get_current_profile() cp
            WHERE (cp.role_name = 'PLATFORM_ADMIN' OR
                  (cp.role_name = 'DEPARTMENT_ADMIN' AND cp.organization_id = profiles.organization_id))
              AND cp.is_active = true
        )
    );
