-- =============================================================================
-- PROJECT ATLAS — Phase 1, Deliverable 3
-- Row-Level Security (RLS) Policies
-- PostgreSQL 15+ / Supabase
-- =============================================================================
-- ROLE MATRIX:
--   admin    → Full CRUD on all tables
--   analyst  → Create/read/update scenarios, simulation_runs; read-only on nodes/links
--   viewer   → Read-only on all tables except own user_profile (can update)
--   anon     → Read-only on scenarios WHERE is_public = TRUE only
--   audit    → NO user can UPDATE or DELETE audit_logs (append-only enforced)
-- =============================================================================

BEGIN;

-- ---------------------------------------------------------------------------
-- HELPER: a stable function to fetch the calling user's role from user_profiles
-- This avoids repeated subqueries and is inlined by the planner.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION auth.user_role()
RETURNS user_role_enum
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT role
  FROM public.user_profiles
  WHERE profile_id = auth.uid()
$$;

-- ---------------------------------------------------------------------------
-- HELPER: check if the calling user is an admin
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION auth.is_admin()
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT EXISTS (
    SELECT 1 FROM public.user_profiles
    WHERE profile_id = auth.uid()
      AND role = 'admin'
  )
$$;

-- ---------------------------------------------------------------------------
-- HELPER: check if the calling user is an analyst or admin
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION auth.is_analyst_or_admin()
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT EXISTS (
    SELECT 1 FROM public.user_profiles
    WHERE profile_id = auth.uid()
      AND role IN ('analyst', 'admin')
  )
$$;

-- =============================================================================
-- ENABLE RLS ON ALL TABLES
-- =============================================================================

ALTER TABLE public.supply_chain_nodes      ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.supply_chain_links      ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.inventory_levels        ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.flow_records            ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.disruption_types        ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.scenarios               ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.scenario_disruptions    ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.simulation_runs         ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.simulation_results      ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.simulation_aggregates   ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.vulnerability_assessments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.mitigation_strategies   ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_profiles           ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_logs              ENABLE ROW LEVEL SECURITY;

-- Force RLS even for table owners (critical for Supabase service role bypass safety)
ALTER TABLE public.supply_chain_nodes      FORCE ROW LEVEL SECURITY;
ALTER TABLE public.supply_chain_links      FORCE ROW LEVEL SECURITY;
ALTER TABLE public.inventory_levels        FORCE ROW LEVEL SECURITY;
ALTER TABLE public.flow_records            FORCE ROW LEVEL SECURITY;
ALTER TABLE public.disruption_types        FORCE ROW LEVEL SECURITY;
ALTER TABLE public.scenarios               FORCE ROW LEVEL SECURITY;
ALTER TABLE public.scenario_disruptions    FORCE ROW LEVEL SECURITY;
ALTER TABLE public.simulation_runs         FORCE ROW LEVEL SECURITY;
ALTER TABLE public.simulation_results      FORCE ROW LEVEL SECURITY;
ALTER TABLE public.simulation_aggregates   FORCE ROW LEVEL SECURITY;
ALTER TABLE public.vulnerability_assessments FORCE ROW LEVEL SECURITY;
ALTER TABLE public.mitigation_strategies   FORCE ROW LEVEL SECURITY;
ALTER TABLE public.user_profiles           FORCE ROW LEVEL SECURITY;
ALTER TABLE public.audit_logs              FORCE ROW LEVEL SECURITY;

-- =============================================================================
-- TABLE: supply_chain_nodes
-- Rules: All authenticated users read; only admins write
-- =============================================================================

-- SELECT: all authenticated users can read all nodes
CREATE POLICY "nodes_select_authenticated"
  ON public.supply_chain_nodes
  FOR SELECT
  TO authenticated
  USING (TRUE);

-- SELECT: anonymous users cannot read nodes (sensitive infrastructure data)
-- (No anon policy = anon gets nothing by default)

-- INSERT: admins only
CREATE POLICY "nodes_insert_admin"
  ON public.supply_chain_nodes
  FOR INSERT
  TO authenticated
  WITH CHECK (auth.is_admin());

-- UPDATE: admins only
CREATE POLICY "nodes_update_admin"
  ON public.supply_chain_nodes
  FOR UPDATE
  TO authenticated
  USING (auth.is_admin())
  WITH CHECK (auth.is_admin());

-- DELETE: admins only
CREATE POLICY "nodes_delete_admin"
  ON public.supply_chain_nodes
  FOR DELETE
  TO authenticated
  USING (auth.is_admin());

-- =============================================================================
-- TABLE: supply_chain_links
-- Rules: All authenticated users read; only admins write
-- =============================================================================

CREATE POLICY "links_select_authenticated"
  ON public.supply_chain_links
  FOR SELECT
  TO authenticated
  USING (TRUE);

CREATE POLICY "links_insert_admin"
  ON public.supply_chain_links
  FOR INSERT
  TO authenticated
  WITH CHECK (auth.is_admin());

CREATE POLICY "links_update_admin"
  ON public.supply_chain_links
  FOR UPDATE
  TO authenticated
  USING (auth.is_admin())
  WITH CHECK (auth.is_admin());

CREATE POLICY "links_delete_admin"
  ON public.supply_chain_links
  FOR DELETE
  TO authenticated
  USING (auth.is_admin());

-- =============================================================================
-- TABLE: inventory_levels
-- Rules: All authenticated users read; only admins write
-- =============================================================================

CREATE POLICY "inventory_select_authenticated"
  ON public.inventory_levels
  FOR SELECT
  TO authenticated
  USING (TRUE);

CREATE POLICY "inventory_insert_admin"
  ON public.inventory_levels
  FOR INSERT
  TO authenticated
  WITH CHECK (auth.is_admin());

CREATE POLICY "inventory_update_admin"
  ON public.inventory_levels
  FOR UPDATE
  TO authenticated
  USING (auth.is_admin())
  WITH CHECK (auth.is_admin());

CREATE POLICY "inventory_delete_admin"
  ON public.inventory_levels
  FOR DELETE
  TO authenticated
  USING (auth.is_admin());

-- =============================================================================
-- TABLE: flow_records
-- Rules: All authenticated users read; admins and analysts can insert
--        (simulation engine writes flow records); only admins delete
-- =============================================================================

CREATE POLICY "flows_select_authenticated"
  ON public.flow_records
  FOR SELECT
  TO authenticated
  USING (TRUE);

CREATE POLICY "flows_insert_analyst_or_admin"
  ON public.flow_records
  FOR INSERT
  TO authenticated
  WITH CHECK (auth.is_analyst_or_admin());

CREATE POLICY "flows_update_admin"
  ON public.flow_records
  FOR UPDATE
  TO authenticated
  USING (auth.is_admin())
  WITH CHECK (auth.is_admin());

CREATE POLICY "flows_delete_admin"
  ON public.flow_records
  FOR DELETE
  TO authenticated
  USING (auth.is_admin());

-- =============================================================================
-- TABLE: disruption_types
-- Rules: All authenticated users read; only admins write
--        Anonymous users can read (public reference data — no sensitive values)
-- =============================================================================

CREATE POLICY "disruptions_select_anon"
  ON public.disruption_types
  FOR SELECT
  TO anon
  USING (TRUE);

CREATE POLICY "disruptions_select_authenticated"
  ON public.disruption_types
  FOR SELECT
  TO authenticated
  USING (TRUE);

CREATE POLICY "disruptions_insert_admin"
  ON public.disruption_types
  FOR INSERT
  TO authenticated
  WITH CHECK (auth.is_admin());

CREATE POLICY "disruptions_update_admin"
  ON public.disruption_types
  FOR UPDATE
  TO authenticated
  USING (auth.is_admin())
  WITH CHECK (auth.is_admin());

CREATE POLICY "disruptions_delete_admin"
  ON public.disruption_types
  FOR DELETE
  TO authenticated
  USING (auth.is_admin());

-- =============================================================================
-- TABLE: scenarios
-- Rules:
--   anon        → read WHERE is_public = TRUE
--   viewer      → read all public + own scenarios
--   analyst     → read all public + own; INSERT own; UPDATE own (not others')
--   admin       → full CRUD
-- =============================================================================

-- Anonymous: public scenarios only
CREATE POLICY "scenarios_select_anon_public"
  ON public.scenarios
  FOR SELECT
  TO anon
  USING (is_public = TRUE);

-- Viewers: public scenarios + own scenarios
CREATE POLICY "scenarios_select_viewer"
  ON public.scenarios
  FOR SELECT
  TO authenticated
  USING (
    is_public = TRUE
    OR created_by = auth.uid()
    OR auth.is_analyst_or_admin()
  );

-- Analysts and admins: INSERT own scenarios
CREATE POLICY "scenarios_insert_analyst_or_admin"
  ON public.scenarios
  FOR INSERT
  TO authenticated
  WITH CHECK (
    auth.is_analyst_or_admin()
    AND created_by = auth.uid()
  );

-- Analysts: UPDATE only their own scenarios; admins update any
CREATE POLICY "scenarios_update_own_or_admin"
  ON public.scenarios
  FOR UPDATE
  TO authenticated
  USING (
    (auth.user_role() = 'analyst' AND created_by = auth.uid())
    OR auth.is_admin()
  )
  WITH CHECK (
    (auth.user_role() = 'analyst' AND created_by = auth.uid())
    OR auth.is_admin()
  );

-- DELETE: admins only (analysts cannot delete scenarios)
CREATE POLICY "scenarios_delete_admin"
  ON public.scenarios
  FOR DELETE
  TO authenticated
  USING (auth.is_admin());

-- =============================================================================
-- TABLE: scenario_disruptions
-- Rules: Follows parent scenario access
--   read  → anyone who can read the parent scenario
--   write → owner of parent scenario (analyst) or admin
-- =============================================================================

CREATE POLICY "sd_select_authenticated"
  ON public.scenario_disruptions
  FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM public.scenarios s
      WHERE s.scenario_id = scenario_disruptions.scenario_id
        AND (
          s.is_public = TRUE
          OR s.created_by = auth.uid()
          OR auth.is_admin()
        )
    )
  );

CREATE POLICY "sd_select_anon_public"
  ON public.scenario_disruptions
  FOR SELECT
  TO anon
  USING (
    EXISTS (
      SELECT 1 FROM public.scenarios s
      WHERE s.scenario_id = scenario_disruptions.scenario_id
        AND s.is_public = TRUE
    )
  );

CREATE POLICY "sd_insert_analyst_or_admin"
  ON public.scenario_disruptions
  FOR INSERT
  TO authenticated
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.scenarios s
      WHERE s.scenario_id = scenario_disruptions.scenario_id
        AND (
          (auth.user_role() = 'analyst' AND s.created_by = auth.uid())
          OR auth.is_admin()
        )
    )
  );

CREATE POLICY "sd_update_analyst_or_admin"
  ON public.scenario_disruptions
  FOR UPDATE
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM public.scenarios s
      WHERE s.scenario_id = scenario_disruptions.scenario_id
        AND (
          (auth.user_role() = 'analyst' AND s.created_by = auth.uid())
          OR auth.is_admin()
        )
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.scenarios s
      WHERE s.scenario_id = scenario_disruptions.scenario_id
        AND (
          (auth.user_role() = 'analyst' AND s.created_by = auth.uid())
          OR auth.is_admin()
        )
    )
  );

CREATE POLICY "sd_delete_admin"
  ON public.scenario_disruptions
  FOR DELETE
  TO authenticated
  USING (auth.is_admin());

-- =============================================================================
-- TABLE: simulation_runs
-- Rules:
--   viewer  → read runs from public scenarios + own runs
--   analyst → read own + public; INSERT own runs; UPDATE own runs (status only)
--   admin   → full CRUD
-- =============================================================================

CREATE POLICY "runs_select_authenticated"
  ON public.simulation_runs
  FOR SELECT
  TO authenticated
  USING (
    triggered_by = auth.uid()
    OR auth.is_admin()
    OR EXISTS (
      SELECT 1 FROM public.scenarios s
      WHERE s.scenario_id = simulation_runs.scenario_id
        AND s.is_public = TRUE
    )
  );

CREATE POLICY "runs_insert_analyst_or_admin"
  ON public.simulation_runs
  FOR INSERT
  TO authenticated
  WITH CHECK (
    auth.is_analyst_or_admin()
    AND triggered_by = auth.uid()
  );

-- Analysts can update status of their own runs (e.g., cancel)
-- Admins can update any run
CREATE POLICY "runs_update_own_or_admin"
  ON public.simulation_runs
  FOR UPDATE
  TO authenticated
  USING (
    (auth.user_role() = 'analyst' AND triggered_by = auth.uid())
    OR auth.is_admin()
  )
  WITH CHECK (
    (auth.user_role() = 'analyst' AND triggered_by = auth.uid())
    OR auth.is_admin()
  );

CREATE POLICY "runs_delete_admin"
  ON public.simulation_runs
  FOR DELETE
  TO authenticated
  USING (auth.is_admin());

-- =============================================================================
-- TABLE: simulation_results
-- Rules: Users can only read results from their own runs; admins read all
--        Results are immutable — no UPDATE or DELETE for any non-admin user
-- =============================================================================

CREATE POLICY "results_select_own_or_admin"
  ON public.simulation_results
  FOR SELECT
  TO authenticated
  USING (
    auth.is_admin()
    OR EXISTS (
      SELECT 1 FROM public.simulation_runs r
      WHERE r.run_id = simulation_results.run_id
        AND (
          r.triggered_by = auth.uid()
          OR EXISTS (
            SELECT 1 FROM public.scenarios s
            WHERE s.scenario_id = r.scenario_id
              AND s.is_public = TRUE
          )
        )
    )
  );

-- INSERT: simulation engine (service role) writes results
-- Analysts can insert results for their own runs only
CREATE POLICY "results_insert_analyst_or_admin"
  ON public.simulation_results
  FOR INSERT
  TO authenticated
  WITH CHECK (
    auth.is_admin()
    OR EXISTS (
      SELECT 1 FROM public.simulation_runs r
      WHERE r.run_id = simulation_results.run_id
        AND r.triggered_by = auth.uid()
        AND auth.user_role() = 'analyst'
    )
  );

-- No UPDATE policy — results are immutable
-- DELETE: admins only (e.g., cleaning up failed runs)
CREATE POLICY "results_delete_admin"
  ON public.simulation_results
  FOR DELETE
  TO authenticated
  USING (auth.is_admin());

-- =============================================================================
-- TABLE: simulation_aggregates
-- Rules: Same as simulation_results — tied to run ownership
-- =============================================================================

CREATE POLICY "aggregates_select_own_or_admin"
  ON public.simulation_aggregates
  FOR SELECT
  TO authenticated
  USING (
    auth.is_admin()
    OR EXISTS (
      SELECT 1 FROM public.simulation_runs r
      WHERE r.run_id = simulation_aggregates.run_id
        AND (
          r.triggered_by = auth.uid()
          OR EXISTS (
            SELECT 1 FROM public.scenarios s
            WHERE s.scenario_id = r.scenario_id
              AND s.is_public = TRUE
          )
        )
    )
  );

-- Anonymous: can read aggregates for public scenarios
CREATE POLICY "aggregates_select_anon_public"
  ON public.simulation_aggregates
  FOR SELECT
  TO anon
  USING (
    EXISTS (
      SELECT 1 FROM public.simulation_runs r
      JOIN public.scenarios s ON s.scenario_id = r.scenario_id
      WHERE r.run_id = simulation_aggregates.run_id
        AND s.is_public = TRUE
    )
  );

CREATE POLICY "aggregates_insert_analyst_or_admin"
  ON public.simulation_aggregates
  FOR INSERT
  TO authenticated
  WITH CHECK (
    auth.is_admin()
    OR EXISTS (
      SELECT 1 FROM public.simulation_runs r
      WHERE r.run_id = simulation_aggregates.run_id
        AND r.triggered_by = auth.uid()
        AND auth.user_role() = 'analyst'
    )
  );

CREATE POLICY "aggregates_delete_admin"
  ON public.simulation_aggregates
  FOR DELETE
  TO authenticated
  USING (auth.is_admin());

-- =============================================================================
-- TABLE: vulnerability_assessments
-- Rules: Same as simulation_results — tied to run ownership
-- =============================================================================

CREATE POLICY "va_select_own_or_admin"
  ON public.vulnerability_assessments
  FOR SELECT
  TO authenticated
  USING (
    auth.is_admin()
    OR EXISTS (
      SELECT 1 FROM public.simulation_runs r
      WHERE r.run_id = vulnerability_assessments.run_id
        AND (
          r.triggered_by = auth.uid()
          OR EXISTS (
            SELECT 1 FROM public.scenarios s
            WHERE s.scenario_id = r.scenario_id
              AND s.is_public = TRUE
          )
        )
    )
  );

CREATE POLICY "va_select_anon_public"
  ON public.vulnerability_assessments
  FOR SELECT
  TO anon
  USING (
    EXISTS (
      SELECT 1 FROM public.simulation_runs r
      JOIN public.scenarios s ON s.scenario_id = r.scenario_id
      WHERE r.run_id = vulnerability_assessments.run_id
        AND s.is_public = TRUE
    )
  );

CREATE POLICY "va_insert_analyst_or_admin"
  ON public.vulnerability_assessments
  FOR INSERT
  TO authenticated
  WITH CHECK (
    auth.is_admin()
    OR EXISTS (
      SELECT 1 FROM public.simulation_runs r
      WHERE r.run_id = vulnerability_assessments.run_id
        AND r.triggered_by = auth.uid()
        AND auth.user_role() = 'analyst'
    )
  );

CREATE POLICY "va_delete_admin"
  ON public.vulnerability_assessments
  FOR DELETE
  TO authenticated
  USING (auth.is_admin());

-- =============================================================================
-- TABLE: mitigation_strategies
-- Rules: All authenticated users read; only admins write
-- =============================================================================

CREATE POLICY "mitigation_select_authenticated"
  ON public.mitigation_strategies
  FOR SELECT
  TO authenticated
  USING (TRUE);

-- Allow anonymous read (reference data useful for public consumers)
CREATE POLICY "mitigation_select_anon"
  ON public.mitigation_strategies
  FOR SELECT
  TO anon
  USING (TRUE);

CREATE POLICY "mitigation_insert_admin"
  ON public.mitigation_strategies
  FOR INSERT
  TO authenticated
  WITH CHECK (auth.is_admin());

CREATE POLICY "mitigation_update_admin"
  ON public.mitigation_strategies
  FOR UPDATE
  TO authenticated
  USING (auth.is_admin())
  WITH CHECK (auth.is_admin());

CREATE POLICY "mitigation_delete_admin"
  ON public.mitigation_strategies
  FOR DELETE
  TO authenticated
  USING (auth.is_admin());

-- =============================================================================
-- TABLE: user_profiles
-- Rules:
--   Every user can SELECT and UPDATE their own profile
--   Admins can SELECT and UPDATE all profiles
--   INSERT triggered automatically on auth.users creation (via DB trigger below)
--   DELETE: admins only
-- =============================================================================

-- Each user sees only their own row; admins see all
CREATE POLICY "profiles_select_own_or_admin"
  ON public.user_profiles
  FOR SELECT
  TO authenticated
  USING (
    profile_id = auth.uid()
    OR auth.is_admin()
  );

-- Each user can update their own non-sensitive fields
-- (role changes require admin — enforced by WITH CHECK)
CREATE POLICY "profiles_update_own"
  ON public.user_profiles
  FOR UPDATE
  TO authenticated
  USING (profile_id = auth.uid())
  WITH CHECK (
    profile_id = auth.uid()
    -- Prevent users from escalating their own role
    AND role = (SELECT role FROM public.user_profiles WHERE profile_id = auth.uid())
  );

-- Admins can update any profile including role assignments
CREATE POLICY "profiles_update_admin"
  ON public.user_profiles
  FOR UPDATE
  TO authenticated
  USING (auth.is_admin())
  WITH CHECK (auth.is_admin());

-- INSERT: only via service role (triggered by auth.users creation)
-- or admin (for manual user provisioning)
CREATE POLICY "profiles_insert_admin_or_service"
  ON public.user_profiles
  FOR INSERT
  TO authenticated
  WITH CHECK (auth.is_admin());

-- DELETE: admins only
CREATE POLICY "profiles_delete_admin"
  ON public.user_profiles
  FOR DELETE
  TO authenticated
  USING (auth.is_admin());

-- =============================================================================
-- TABLE: audit_logs
-- CRITICAL: Append-only. NO UPDATE. NO DELETE for ANY user including admin.
-- =============================================================================

-- All authenticated users can read all audit logs
-- (Security transparency — users can see actions on their own records)
CREATE POLICY "audit_select_own_or_admin"
  ON public.audit_logs
  FOR SELECT
  TO authenticated
  USING (
    user_id = auth.uid()
    OR auth.is_admin()
  );

-- INSERT: all authenticated users can insert (actions are logged by the app)
-- In practice, the backend service role writes these; this policy ensures
-- the app can also write through the JWT-authenticated client.
CREATE POLICY "audit_insert_authenticated"
  ON public.audit_logs
  FOR INSERT
  TO authenticated
  WITH CHECK (
    user_id = auth.uid()  -- Users can only log their own actions
    OR auth.is_admin()
  );

-- EXPLICITLY NO UPDATE POLICY — PostgreSQL denies by default when RLS is enabled
-- EXPLICITLY NO DELETE POLICY — same: no policy = no access

-- =============================================================================
-- AUTO-PROVISIONING TRIGGER: Create user_profile when auth.users row is created
-- =============================================================================

CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  INSERT INTO public.user_profiles (
    profile_id,
    full_name,
    organization,
    role,
    api_calls_today,
    api_calls_reset_at,
    daily_api_limit,
    last_active
  )
  VALUES (
    NEW.id,
    COALESCE(NEW.raw_user_meta_data->>'full_name', 'New User'),
    NEW.raw_user_meta_data->>'organization',
    'viewer',       -- default role; admin must explicitly elevate
    0,
    NOW() + INTERVAL '1 day',
    100,
    NOW()
  )
  ON CONFLICT (profile_id) DO NOTHING;  -- idempotent; safe for OAuth re-auth

  -- Log the registration event
  INSERT INTO public.audit_logs (
    user_id, action, table_name, record_id,
    new_values, performed_at
  )
  VALUES (
    NEW.id,
    'REGISTER',
    'auth.users',
    NEW.id,
    jsonb_build_object(
      'email', NEW.email,
      'provider', NEW.raw_app_meta_data->>'provider',
      'default_role', 'viewer'
    ),
    NOW()
  );

  RETURN NEW;
END;
$$;

-- Attach trigger to auth.users
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- =============================================================================
-- API RATE LIMIT ENFORCEMENT TRIGGER
-- Increments api_calls_today on each scenario run trigger; resets daily
-- =============================================================================

CREATE OR REPLACE FUNCTION public.enforce_api_rate_limit()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_calls_today  INTEGER;
  v_daily_limit  INTEGER;
  v_reset_at     TIMESTAMPTZ;
BEGIN
  SELECT api_calls_today, daily_api_limit, api_calls_reset_at
  INTO v_calls_today, v_daily_limit, v_reset_at
  FROM public.user_profiles
  WHERE profile_id = NEW.triggered_by;

  -- Reset counter if past reset time
  IF NOW() > v_reset_at THEN
    UPDATE public.user_profiles
    SET api_calls_today = 1,
        api_calls_reset_at = NOW() + INTERVAL '1 day'
    WHERE profile_id = NEW.triggered_by;
  ELSE
    IF v_calls_today >= v_daily_limit THEN
      RAISE EXCEPTION 'API rate limit exceeded. Daily limit: %. Resets at: %',
        v_daily_limit, v_reset_at
        USING ERRCODE = 'P0001';
    END IF;

    UPDATE public.user_profiles
    SET api_calls_today = api_calls_today + 1
    WHERE profile_id = NEW.triggered_by;
  END IF;

  RETURN NEW;
END;
$$;

CREATE TRIGGER trg_rate_limit_simulation_run
  BEFORE INSERT ON public.simulation_runs
  FOR EACH ROW EXECUTE FUNCTION public.enforce_api_rate_limit();

-- =============================================================================
-- AUDIT TRIGGER: Auto-log mutations on critical tables
-- =============================================================================

CREATE OR REPLACE FUNCTION public.log_table_mutation()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  INSERT INTO public.audit_logs (
    user_id,
    action,
    table_name,
    record_id,
    old_values,
    new_values,
    performed_at
  )
  VALUES (
    auth.uid(),
    TG_OP,                         -- 'INSERT', 'UPDATE', 'DELETE'
    TG_TABLE_NAME,
    CASE TG_OP
      WHEN 'DELETE' THEN (row_to_json(OLD)->>'node_id')::UUID  -- best-effort PK extraction
      ELSE (row_to_json(NEW)->>'node_id')::UUID
    END,
    CASE TG_OP WHEN 'INSERT' THEN NULL ELSE row_to_json(OLD)::JSONB END,
    CASE TG_OP WHEN 'DELETE' THEN NULL ELSE row_to_json(NEW)::JSONB END,
    NOW()
  );
  RETURN COALESCE(NEW, OLD);
END;
$$;

-- Apply audit trigger to the most sensitive tables
CREATE TRIGGER audit_supply_chain_nodes
  AFTER INSERT OR UPDATE OR DELETE ON public.supply_chain_nodes
  FOR EACH ROW EXECUTE FUNCTION public.log_table_mutation();

CREATE TRIGGER audit_supply_chain_links
  AFTER INSERT OR UPDATE OR DELETE ON public.supply_chain_links
  FOR EACH ROW EXECUTE FUNCTION public.log_table_mutation();

CREATE TRIGGER audit_scenarios
  AFTER INSERT OR UPDATE OR DELETE ON public.scenarios
  FOR EACH ROW EXECUTE FUNCTION public.log_table_mutation();

-- =============================================================================
-- GRANT STATEMENTS — Supabase Role Permissions
-- =============================================================================

-- anon role: minimal access (enforced by RLS above; this grants table-level access)
GRANT SELECT ON public.disruption_types      TO anon;
GRANT SELECT ON public.scenarios             TO anon;
GRANT SELECT ON public.scenario_disruptions  TO anon;
GRANT SELECT ON public.simulation_aggregates TO anon;
GRANT SELECT ON public.vulnerability_assessments TO anon;
GRANT SELECT ON public.mitigation_strategies TO anon;

-- authenticated role: general access (RLS policies further restrict)
GRANT SELECT, INSERT, UPDATE, DELETE ON public.supply_chain_nodes       TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.supply_chain_links       TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.inventory_levels         TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.flow_records             TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.disruption_types         TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.scenarios                TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.scenario_disruptions     TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.simulation_runs          TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.simulation_results       TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.simulation_aggregates    TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.vulnerability_assessments TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.mitigation_strategies    TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.user_profiles            TO authenticated;
GRANT SELECT, INSERT                  ON public.audit_logs              TO authenticated;
-- NOTE: No UPDATE or DELETE granted on audit_logs to ANY role

-- service_role: bypasses RLS by default in Supabase (used by FastAPI backend)
-- No additional grants needed — service_role has superuser-equivalent access

COMMIT;

-- =============================================================================
-- RLS VERIFICATION QUERIES
-- Run as different roles to confirm policy enforcement
-- =============================================================================

-- Test 1: Confirm RLS is enabled on all tables
SELECT
  schemaname,
  tablename,
  rowsecurity AS rls_enabled,
  forcerowsecurity AS rls_forced
FROM pg_tables
WHERE schemaname = 'public'
  AND tablename IN (
    'supply_chain_nodes', 'supply_chain_links', 'inventory_levels',
    'flow_records', 'disruption_types', 'scenarios', 'scenario_disruptions',
    'simulation_runs', 'simulation_results', 'simulation_aggregates',
    'vulnerability_assessments', 'mitigation_strategies',
    'user_profiles', 'audit_logs'
  )
ORDER BY tablename;

-- Test 2: List all policies
SELECT
  schemaname,
  tablename,
  policyname,
  permissive,
  roles,
  cmd,
  qual,
  with_check
FROM pg_policies
WHERE schemaname = 'public'
ORDER BY tablename, policyname;

-- Test 3: Confirm audit_logs has NO UPDATE or DELETE policies
SELECT policyname, cmd
FROM pg_policies
WHERE schemaname = 'public'
  AND tablename = 'audit_logs'
  AND cmd IN ('UPDATE', 'DELETE');
-- Expected: 0 rows returned

-- Test 4: Confirm helper functions exist
SELECT
  routine_name,
  routine_type,
  security_type
FROM information_schema.routines
WHERE routine_schema = 'auth'
  AND routine_name IN ('user_role', 'is_admin', 'is_analyst_or_admin')
ORDER BY routine_name;
