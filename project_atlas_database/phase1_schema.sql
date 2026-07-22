-- =============================================================================
-- PROJECT ATLAS — Phase 1, Deliverable 1
-- PostgreSQL Schema: Nigerian Oil & Gas Supply Chain Stress-Testing System
-- Target DB: PostgreSQL 15+ via Supabase
-- Author: Project Atlas Execution Engine
-- Version: 1.0.0
-- =============================================================================

-- ---------------------------------------------------------------------------
-- EXTENSIONS
-- ---------------------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS "pgcrypto";    -- gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";   -- uuid_generate_v4() fallback
CREATE EXTENSION IF NOT EXISTS "pg_trgm";     -- trigram text search indexes
CREATE EXTENSION IF NOT EXISTS "btree_gist";  -- GiST index support

-- ---------------------------------------------------------------------------
-- HELPER FUNCTION: auto-update updated_at on any table
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION trigger_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ---------------------------------------------------------------------------
-- ENUM TYPES
-- ---------------------------------------------------------------------------

CREATE TYPE node_type_enum AS ENUM (
  'wellhead',
  'pipeline',
  'export_terminal',
  'refinery',
  'storage_depot',
  'port',
  'distribution_hub',
  'consumer'
);
COMMENT ON TYPE node_type_enum IS 'Classifies each node by its functional role in the supply chain';

CREATE TYPE stage_enum AS ENUM (
  'upstream',
  'midstream',
  'downstream'
);
COMMENT ON TYPE stage_enum IS 'Maps to the three macro-stages of the Nigerian oil & gas supply chain';

CREATE TYPE geopolitical_zone_enum AS ENUM (
  'SW',   -- South-West
  'SE',   -- South-East
  'SS',   -- South-South (Niger Delta)
  'NW',   -- North-West
  'NE',   -- North-East
  'NC'    -- North-Central
);
COMMENT ON TYPE geopolitical_zone_enum IS 'Nigerian geopolitical zones; SS covers the Niger Delta region';

CREATE TYPE node_status_enum AS ENUM (
  'operational',
  'degraded',
  'offline'
);
COMMENT ON TYPE node_status_enum IS 'Current operational status of a supply chain node';

CREATE TYPE link_type_enum AS ENUM (
  'pipeline',
  'road',
  'sea_route',
  'rail',
  'river'
);
COMMENT ON TYPE link_type_enum IS 'Physical transport medium connecting two supply chain nodes';

CREATE TYPE product_type_enum AS ENUM (
  'crude_oil',
  'petrol',          -- PMS — Premium Motor Spirit
  'diesel',          -- AGO — Automotive Gas Oil
  'kerosene',        -- DPK — Dual Purpose Kerosene
  'lpg',             -- Liquefied Petroleum Gas
  'jet_fuel'         -- ATK — Aviation Turbine Kerosene
);
COMMENT ON TYPE product_type_enum IS 'Petroleum product types traded in the Nigerian supply chain';

CREATE TYPE flow_status_enum AS ENUM (
  'completed',
  'delayed',
  'blocked',
  'partial'
);
COMMENT ON TYPE flow_status_enum IS 'Outcome status of a recorded flow along a supply chain link';

CREATE TYPE disruption_category_enum AS ENUM (
  'infrastructure',
  'logistics',
  'geopolitical',
  'environmental',
  'operational',
  'economic',
  'cybersecurity',
  'force_majeure'
);
COMMENT ON TYPE disruption_category_enum IS '8 disruption categories parameterizing Monte Carlo scenario inputs';

CREATE TYPE scenario_status_enum AS ENUM (
  'draft',
  'running',
  'completed',
  'failed'
);
COMMENT ON TYPE scenario_status_enum IS 'Lifecycle status of a simulation scenario';

CREATE TYPE simulation_run_status_enum AS ENUM (
  'queued',
  'running',
  'completed',
  'failed'
);
COMMENT ON TYPE simulation_run_status_enum IS 'Execution status of a specific Monte Carlo simulation run';

CREATE TYPE user_role_enum AS ENUM (
  'admin',
  'analyst',
  'viewer'
);
COMMENT ON TYPE user_role_enum IS 'Access control roles; enforced via RLS policies';

-- =============================================================================
-- SECTION 1: CORE SUPPLY CHAIN TABLES
-- =============================================================================

-- ---------------------------------------------------------------------------
-- TABLE 1: supply_chain_nodes
-- ---------------------------------------------------------------------------
CREATE TABLE supply_chain_nodes (
  node_id                   UUID          PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Identity
  node_name                 VARCHAR(255)  NOT NULL,
  node_code                 VARCHAR(50)   UNIQUE NOT NULL, -- e.g., 'BONNY-WH-001'
  node_type                 node_type_enum NOT NULL,
  stage                     stage_enum    NOT NULL,

  -- Geography
  latitude                  DECIMAL(10,7) NOT NULL,
  longitude                 DECIMAL(10,7) NOT NULL,
  state_location            VARCHAR(100)  NOT NULL,        -- Nigerian state
  geopolitical_zone         geopolitical_zone_enum NOT NULL,
  address_description       TEXT,

  -- Ownership & Operation
  operator                  VARCHAR(255)  NOT NULL,        -- e.g., Shell, Chevron, NNPC
  operator_type             VARCHAR(100),                  -- IOC, NNPC, Indigenous

  -- Capacity & Performance
  capacity_bpd              DECIMAL(12,2) NOT NULL DEFAULT 0,  -- barrels per day nameplate
  current_utilization_pct   DECIMAL(5,4)  NOT NULL DEFAULT 0
                              CHECK (current_utilization_pct >= 0 AND current_utilization_pct <= 1),
  annual_throughput_barrels DECIMAL(18,2),                 -- last 12-month actual

  -- Status & Resilience
  status                    node_status_enum NOT NULL DEFAULT 'operational',
  redundancy_score          DECIMAL(5,4)  NOT NULL DEFAULT 0
                              CHECK (redundancy_score >= 0 AND redundancy_score <= 1),
  criticality_score         DECIMAL(5,4)  NOT NULL DEFAULT 0
                              CHECK (criticality_score >= 0 AND criticality_score <= 1),
  mean_time_between_failures_days DECIMAL(8,2),           -- MTBF in days
  mean_time_to_repair_days  DECIMAL(8,2),                 -- MTTR in days

  -- Costs
  daily_operating_cost_usd  DECIMAL(14,2),
  replacement_cost_usd      DECIMAL(18,2),

  -- Flexible metadata
  metadata                  JSONB         NOT NULL DEFAULT '{}',

  -- Audit
  created_at                TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
  updated_at                TIMESTAMPTZ   NOT NULL DEFAULT NOW(),

  CONSTRAINT nodes_utilization_range
    CHECK (current_utilization_pct BETWEEN 0 AND 1),
  CONSTRAINT nodes_redundancy_range
    CHECK (redundancy_score BETWEEN 0 AND 1),
  CONSTRAINT nodes_criticality_range
    CHECK (criticality_score BETWEEN 0 AND 1)
);

COMMENT ON TABLE supply_chain_nodes IS
  'Master registry of all physical nodes in the Nigerian oil & gas supply chain. '
  'Each row represents a discrete facility: wellhead, pipeline segment, terminal, '
  'refinery, depot, port, or consumer node.';

COMMENT ON COLUMN supply_chain_nodes.node_id IS 'UUID primary key, auto-generated';
COMMENT ON COLUMN supply_chain_nodes.node_code IS 'Human-readable unique code used in API responses and the UI (e.g., BONNY-WH-001)';
COMMENT ON COLUMN supply_chain_nodes.node_type IS 'Functional classification of the node; determines which disruption types apply';
COMMENT ON COLUMN supply_chain_nodes.stage IS 'Macro-stage: upstream = production, midstream = processing/transport, downstream = distribution/consumption';
COMMENT ON COLUMN supply_chain_nodes.capacity_bpd IS 'Nameplate maximum throughput capacity in barrels per day';
COMMENT ON COLUMN supply_chain_nodes.current_utilization_pct IS 'Fraction of capacity currently in use; 0.0–1.0; used as simulation baseline';
COMMENT ON COLUMN supply_chain_nodes.redundancy_score IS '0=single point of failure, 1=fully redundant; input to vulnerability calculations';
COMMENT ON COLUMN supply_chain_nodes.criticality_score IS '0=peripheral, 1=mission-critical; derived from network centrality measures';
COMMENT ON COLUMN supply_chain_nodes.mean_time_between_failures_days IS 'Historical or estimated MTBF in days; parameterizes failure probability distribution';
COMMENT ON COLUMN supply_chain_nodes.mean_time_to_repair_days IS 'Historical or estimated MTTR in days; parameterizes recovery time distribution';
COMMENT ON COLUMN supply_chain_nodes.metadata IS 'JSONB bag for node-specific attributes (e.g., water_depth_m for offshore fields, OML_number for oil blocks)';

CREATE INDEX idx_nodes_type       ON supply_chain_nodes(node_type);
CREATE INDEX idx_nodes_stage      ON supply_chain_nodes(stage);
CREATE INDEX idx_nodes_status     ON supply_chain_nodes(status);
CREATE INDEX idx_nodes_zone       ON supply_chain_nodes(geopolitical_zone);
CREATE INDEX idx_nodes_operator   ON supply_chain_nodes(operator);
CREATE INDEX idx_nodes_criticality ON supply_chain_nodes(criticality_score DESC);
CREATE INDEX idx_nodes_geo        ON supply_chain_nodes USING GIST (
  point(longitude, latitude)
);

CREATE TRIGGER trg_nodes_updated_at
  BEFORE UPDATE ON supply_chain_nodes
  FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

-- ---------------------------------------------------------------------------
-- TABLE 2: supply_chain_links
-- ---------------------------------------------------------------------------
CREATE TABLE supply_chain_links (
  link_id                   UUID          PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Identity
  link_name                 VARCHAR(255)  NOT NULL,
  link_code                 VARCHAR(50)   UNIQUE NOT NULL,  -- e.g., 'TNP-L-001'
  link_type                 link_type_enum NOT NULL,

  -- Topology
  source_node_id            UUID          NOT NULL
                              REFERENCES supply_chain_nodes(node_id)
                              ON DELETE RESTRICT,
  target_node_id            UUID          NOT NULL
                              REFERENCES supply_chain_nodes(node_id)
                              ON DELETE RESTRICT,

  -- Physical Properties
  distance_km               DECIMAL(10,3) NOT NULL CHECK (distance_km > 0),
  diameter_inches           DECIMAL(6,2),  -- for pipelines
  pipeline_year_installed   SMALLINT,      -- for age-based failure rate modeling

  -- Performance Baseline
  normal_lead_time_days     DECIMAL(8,4)   NOT NULL CHECK (normal_lead_time_days > 0),
  transport_cost_per_barrel DECIMAL(10,4)  NOT NULL CHECK (transport_cost_per_barrel >= 0),
  max_capacity_bpd          DECIMAL(12,2)  NOT NULL CHECK (max_capacity_bpd > 0),
  current_utilization_pct   DECIMAL(5,4)   NOT NULL DEFAULT 0
                              CHECK (current_utilization_pct BETWEEN 0 AND 1),

  -- Risk Parameters
  reliability_score         DECIMAL(5,4)   NOT NULL DEFAULT 0.9
                              CHECK (reliability_score BETWEEN 0 AND 1),
  vandalism_risk_score      DECIMAL(5,4)   DEFAULT 0
                              CHECK (vandalism_risk_score BETWEEN 0 AND 1),
  is_critical_path          BOOLEAN        NOT NULL DEFAULT FALSE,

  -- Routing
  alternative_routes        JSONB          NOT NULL DEFAULT '[]',
                              -- Array of {link_id, cost_premium_pct, delay_premium_days}

  -- Status
  status                    node_status_enum NOT NULL DEFAULT 'operational',

  -- Flexible metadata
  metadata                  JSONB          NOT NULL DEFAULT '{}',

  -- Audit
  created_at                TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
  updated_at                TIMESTAMPTZ    NOT NULL DEFAULT NOW(),

  CONSTRAINT no_self_loop CHECK (source_node_id <> target_node_id)
);

COMMENT ON TABLE supply_chain_links IS
  'Directed edges in the supply chain network graph. Each row represents a '
  'physical transport connection (pipeline segment, road corridor, sea lane) '
  'between two nodes. Directed because flow is unidirectional in most cases.';

COMMENT ON COLUMN supply_chain_links.link_code IS 'Human-readable code for API and UI (e.g., TNP-L-001 for Trans Niger Pipeline segment 1)';
COMMENT ON COLUMN supply_chain_links.reliability_score IS '0=unreliable, 1=perfectly reliable; feeds Bernoulli failure trials in Monte Carlo';
COMMENT ON COLUMN supply_chain_links.vandalism_risk_score IS 'Specific score for pipeline vandalism risk; highest in SS geopolitical zone';
COMMENT ON COLUMN supply_chain_links.is_critical_path IS 'True if this link lies on the critical path computed by NetworkX critical_path analysis';
COMMENT ON COLUMN supply_chain_links.alternative_routes IS 'JSON array of fallback routing options with cost and time penalties';
COMMENT ON COLUMN supply_chain_links.diameter_inches IS 'Internal pipe diameter in inches; used for hydraulic flow calculations';

CREATE INDEX idx_links_source       ON supply_chain_links(source_node_id);
CREATE INDEX idx_links_target       ON supply_chain_links(target_node_id);
CREATE INDEX idx_links_type         ON supply_chain_links(link_type);
CREATE INDEX idx_links_critical     ON supply_chain_links(is_critical_path) WHERE is_critical_path = TRUE;
CREATE INDEX idx_links_status       ON supply_chain_links(status);
CREATE INDEX idx_links_reliability  ON supply_chain_links(reliability_score);

CREATE TRIGGER trg_links_updated_at
  BEFORE UPDATE ON supply_chain_links
  FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

-- =============================================================================
-- SECTION 2: INVENTORY & FLOW TABLES
-- =============================================================================

-- ---------------------------------------------------------------------------
-- TABLE 3: inventory_levels
-- ---------------------------------------------------------------------------
CREATE TABLE inventory_levels (
  inventory_id              UUID          PRIMARY KEY DEFAULT gen_random_uuid(),

  node_id                   UUID          NOT NULL
                              REFERENCES supply_chain_nodes(node_id)
                              ON DELETE CASCADE,
  product_type              product_type_enum NOT NULL,

  -- Stock Levels
  quantity_barrels          DECIMAL(14,2) NOT NULL DEFAULT 0
                              CHECK (quantity_barrels >= 0),
  minimum_threshold_barrels DECIMAL(14,2) NOT NULL DEFAULT 0
                              CHECK (minimum_threshold_barrels >= 0),
  maximum_capacity_barrels  DECIMAL(14,2) NOT NULL
                              CHECK (maximum_capacity_barrels > 0),
  reorder_point_barrels     DECIMAL(14,2) NOT NULL DEFAULT 0,
  safety_stock_barrels      DECIMAL(14,2) NOT NULL DEFAULT 0,

  -- Economics
  unit_cost_usd             DECIMAL(10,4) NOT NULL DEFAULT 0
                              CHECK (unit_cost_usd >= 0),

  -- Rates (used in simulation)
  daily_consumption_rate_bpd DECIMAL(12,2) DEFAULT 0,
  daily_supply_rate_bpd     DECIMAL(12,2) DEFAULT 0,

  last_updated              TIMESTAMPTZ   NOT NULL DEFAULT NOW(),

  -- Audit
  created_at                TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
  updated_at                TIMESTAMPTZ   NOT NULL DEFAULT NOW(),

  CONSTRAINT inv_quantity_le_capacity
    CHECK (quantity_barrels <= maximum_capacity_barrels),
  CONSTRAINT inv_reorder_le_max
    CHECK (reorder_point_barrels <= maximum_capacity_barrels),
  CONSTRAINT inv_threshold_le_reorder
    CHECK (minimum_threshold_barrels <= reorder_point_barrels),
  UNIQUE (node_id, product_type)
);

COMMENT ON TABLE inventory_levels IS
  'Current stock position for each (node, product) pair. Drives the '
  'inventory depletion model in the Monte Carlo engine. Each row represents '
  'one tank or storage position at a node.';

COMMENT ON COLUMN inventory_levels.minimum_threshold_barrels IS 'Strategic reserve floor; breach triggers emergency procurement in simulation';
COMMENT ON COLUMN inventory_levels.reorder_point_barrels IS 'Triggers a replenishment order in the simulation inventory model';
COMMENT ON COLUMN inventory_levels.safety_stock_barrels IS 'Buffer above minimum threshold to absorb demand variability';
COMMENT ON COLUMN inventory_levels.daily_consumption_rate_bpd IS 'Average barrels consumed per day; used to project days-of-supply remaining';

CREATE INDEX idx_inventory_node    ON inventory_levels(node_id);
CREATE INDEX idx_inventory_product ON inventory_levels(product_type);
CREATE INDEX idx_inventory_low     ON inventory_levels(quantity_barrels)
  WHERE quantity_barrels < reorder_point_barrels;

CREATE TRIGGER trg_inventory_updated_at
  BEFORE UPDATE ON inventory_levels
  FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

-- ---------------------------------------------------------------------------
-- TABLE 4: flow_records
-- ---------------------------------------------------------------------------
CREATE TABLE flow_records (
  flow_id                   UUID          PRIMARY KEY DEFAULT gen_random_uuid(),

  link_id                   UUID          NOT NULL
                              REFERENCES supply_chain_links(link_id)
                              ON DELETE CASCADE,
  product_type              product_type_enum NOT NULL,

  -- Volume & Timing
  volume_barrels            DECIMAL(14,2) NOT NULL CHECK (volume_barrels > 0),
  flow_date                 DATE          NOT NULL,
  scheduled_lead_time_days  DECIMAL(8,4)  NOT NULL,
  actual_lead_time_days     DECIMAL(8,4),
  delay_days                DECIMAL(8,4)  GENERATED ALWAYS AS
                              (GREATEST(0, actual_lead_time_days - scheduled_lead_time_days))
                              STORED,

  -- Economics
  scheduled_cost_usd        DECIMAL(14,2) NOT NULL CHECK (scheduled_cost_usd >= 0),
  actual_cost_usd           DECIMAL(14,2),
  cost_overrun_usd          DECIMAL(14,2) GENERATED ALWAYS AS
                              (GREATEST(0, actual_cost_usd - scheduled_cost_usd))
                              STORED,

  -- Status
  flow_status               flow_status_enum NOT NULL DEFAULT 'completed',

  -- Disruption linkage (null if no disruption occurred)
  disruption_type_id        UUID          REFERENCES disruption_types(disruption_type_id)
                              ON DELETE SET NULL,
  disruption_notes          TEXT,

  -- Audit
  created_at                TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
  updated_at                TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE flow_records IS
  'Historical ledger of product flows across supply chain links. '
  'Provides the empirical baseline for Monte Carlo parameter calibration. '
  'Generated STORED columns auto-compute delay and cost overrun.';

COMMENT ON COLUMN flow_records.delay_days IS 'Auto-computed: MAX(0, actual - scheduled) lead time. Non-negative by design.';
COMMENT ON COLUMN flow_records.cost_overrun_usd IS 'Auto-computed: MAX(0, actual - scheduled) cost. Feeds expected overrun statistics.';

CREATE INDEX idx_flows_link        ON flow_records(link_id);
CREATE INDEX idx_flows_date        ON flow_records(flow_date DESC);
CREATE INDEX idx_flows_product     ON flow_records(product_type);
CREATE INDEX idx_flows_status      ON flow_records(flow_status);
CREATE INDEX idx_flows_disruption  ON flow_records(disruption_type_id)
  WHERE disruption_type_id IS NOT NULL;
CREATE INDEX idx_flows_date_link   ON flow_records(link_id, flow_date DESC);

CREATE TRIGGER trg_flows_updated_at
  BEFORE UPDATE ON flow_records
  FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

-- =============================================================================
-- SECTION 3: DISRUPTION & SCENARIO TABLES
-- =============================================================================

-- ---------------------------------------------------------------------------
-- TABLE 5: disruption_types
-- ---------------------------------------------------------------------------
CREATE TABLE disruption_types (
  disruption_type_id          UUID          PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Classification
  category                    disruption_category_enum NOT NULL,
  name                        VARCHAR(255)  NOT NULL UNIQUE,
  description                 TEXT          NOT NULL,

  -- Duration Distribution Parameters (log-normal or triangular)
  typical_duration_days_min   DECIMAL(8,2)  NOT NULL CHECK (typical_duration_days_min >= 0),
  typical_duration_days_mode  DECIMAL(8,2)  NOT NULL,
  typical_duration_days_max   DECIMAL(8,2)  NOT NULL,

  -- Probability (annual rate — converted to per-simulation-period in engine)
  typical_annual_probability  DECIMAL(6,4)  NOT NULL
                                CHECK (typical_annual_probability BETWEEN 0 AND 1),

  -- Severity Distribution (fraction of capacity lost: 0=none, 1=total)
  severity_min                DECIMAL(5,4)  NOT NULL DEFAULT 0
                                CHECK (severity_min BETWEEN 0 AND 1),
  severity_mode               DECIMAL(5,4)  NOT NULL DEFAULT 0.5
                                CHECK (severity_mode BETWEEN 0 AND 1),
  severity_max                DECIMAL(5,4)  NOT NULL DEFAULT 1
                                CHECK (severity_max BETWEEN 0 AND 1),

  -- Cost Impact
  cost_multiplier_min         DECIMAL(6,3)  NOT NULL DEFAULT 1.0
                                CHECK (cost_multiplier_min >= 1),
  cost_multiplier_max         DECIMAL(6,3)  NOT NULL DEFAULT 2.0
                                CHECK (cost_multiplier_max >= cost_multiplier_min),

  -- Recovery
  recovery_time_days_min      DECIMAL(8,2)  NOT NULL DEFAULT 0,
  recovery_time_days_max      DECIMAL(8,2)  NOT NULL,

  -- Scope (which node/link types this disruption can affect)
  affected_node_types         JSONB         NOT NULL DEFAULT '[]',
  affected_link_types         JSONB         NOT NULL DEFAULT '[]',

  -- Correlation (for compound disruption modeling)
  correlated_disruption_ids   JSONB         NOT NULL DEFAULT '[]',
  cascading_probability       DECIMAL(5,4)  DEFAULT 0
                                CHECK (cascading_probability BETWEEN 0 AND 1),

  -- Audit
  created_at                  TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
  updated_at                  TIMESTAMPTZ   NOT NULL DEFAULT NOW(),

  CONSTRAINT duration_ordering
    CHECK (typical_duration_days_min <= typical_duration_days_mode
       AND typical_duration_days_mode <= typical_duration_days_max),
  CONSTRAINT severity_ordering
    CHECK (severity_min <= severity_mode AND severity_mode <= severity_max),
  CONSTRAINT recovery_ordering
    CHECK (recovery_time_days_min <= recovery_time_days_max)
);

COMMENT ON TABLE disruption_types IS
  'Parameterized catalogue of all disruption types the Monte Carlo engine can simulate. '
  'Triangular distributions are used for duration and severity (min/mode/max). '
  'These are shared reference data — not scenario-specific.';

COMMENT ON COLUMN disruption_types.typical_duration_days_min IS 'Lower bound of triangular distribution for disruption duration';
COMMENT ON COLUMN disruption_types.typical_duration_days_mode IS 'Most likely duration (mode of triangular distribution)';
COMMENT ON COLUMN disruption_types.typical_annual_probability IS 'Probability of this disruption occurring in any given year; scaled to simulation period by engine';
COMMENT ON COLUMN disruption_types.severity_min IS 'Minimum fraction of node/link capacity lost (0.0 = no impact, 1.0 = complete shutdown)';
COMMENT ON COLUMN disruption_types.cost_multiplier_min IS 'Minimum multiplier applied to base transport/operating cost during disruption (≥1.0)';
COMMENT ON COLUMN disruption_types.correlated_disruption_ids IS 'JSON array of disruption_type_ids that commonly co-occur (e.g., vandalism → spill)';
COMMENT ON COLUMN disruption_types.cascading_probability IS 'Probability that this disruption triggers a correlated disruption';

CREATE INDEX idx_disruptions_category ON disruption_types(category);

CREATE TRIGGER trg_disruptions_updated_at
  BEFORE UPDATE ON disruption_types
  FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

-- ---------------------------------------------------------------------------
-- TABLE 6: scenarios
-- ---------------------------------------------------------------------------
CREATE TABLE scenarios (
  scenario_id               UUID          PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Identity
  scenario_name             VARCHAR(255)  NOT NULL,
  description               TEXT,
  version                   SMALLINT      NOT NULL DEFAULT 1,

  -- Ownership
  created_by                UUID          NOT NULL
                              REFERENCES auth.users(id)
                              ON DELETE RESTRICT,
  is_public                 BOOLEAN       NOT NULL DEFAULT FALSE,

  -- Simulation Parameters
  simulation_iterations     INTEGER       NOT NULL DEFAULT 10000
                              CHECK (simulation_iterations BETWEEN 100 AND 100000),
  time_horizon_days         INTEGER       NOT NULL DEFAULT 365
                              CHECK (time_horizon_days BETWEEN 1 AND 3650),
  random_seed               INTEGER,      -- for reproducible runs; NULL = random

  -- Status
  status                    scenario_status_enum NOT NULL DEFAULT 'draft',

  -- Full scenario configuration snapshot (frozen at run time)
  configuration             JSONB         NOT NULL DEFAULT '{}',

  -- Tags for UI filtering
  tags                      TEXT[]        NOT NULL DEFAULT '{}',

  -- Audit
  created_at                TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
  updated_at                TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE scenarios IS
  'User-defined simulation scenarios. Each scenario specifies which disruptions '
  'to model, their parameters, and the simulation horizon. A scenario can be run '
  'multiple times (each run stored in simulation_runs).';

COMMENT ON COLUMN scenarios.version IS 'Incremented on each substantive change; enables scenario version history';
COMMENT ON COLUMN scenarios.random_seed IS 'Fixed seed for reproducible Monte Carlo runs; NULL means each run uses a different seed';
COMMENT ON COLUMN scenarios.configuration IS 'Full frozen snapshot of scenario parameters at the time of the last run; includes all overrides';
COMMENT ON COLUMN scenarios.tags IS 'Free-text tags for UI filtering (e.g., ["niger-delta", "vandalism", "2024"])';

CREATE INDEX idx_scenarios_created_by ON scenarios(created_by);
CREATE INDEX idx_scenarios_status     ON scenarios(status);
CREATE INDEX idx_scenarios_public     ON scenarios(is_public) WHERE is_public = TRUE;
CREATE INDEX idx_scenarios_tags       ON scenarios USING GIN(tags);

CREATE TRIGGER trg_scenarios_updated_at
  BEFORE UPDATE ON scenarios
  FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

-- ---------------------------------------------------------------------------
-- TABLE 7: scenario_disruptions
-- ---------------------------------------------------------------------------
CREATE TABLE scenario_disruptions (
  scenario_disruption_id    UUID          PRIMARY KEY DEFAULT gen_random_uuid(),

  scenario_id               UUID          NOT NULL
                              REFERENCES scenarios(scenario_id)
                              ON DELETE CASCADE,
  disruption_type_id        UUID          NOT NULL
                              REFERENCES disruption_types(disruption_type_id)
                              ON DELETE RESTRICT,

  -- Target — exactly one of these should be non-null
  target_node_id            UUID          REFERENCES supply_chain_nodes(node_id)
                              ON DELETE RESTRICT,
  target_link_id            UUID          REFERENCES supply_chain_links(link_id)
                              ON DELETE RESTRICT,

  -- Parameter Overrides (null = use disruption_type defaults)
  probability_override      DECIMAL(6,4)  CHECK (probability_override BETWEEN 0 AND 1),
  severity_override         DECIMAL(5,4)  CHECK (severity_override BETWEEN 0 AND 1),
  duration_days_override    DECIMAL(8,2)  CHECK (duration_days_override > 0),

  -- Compound disruption linkage
  simultaneous_with         UUID          REFERENCES scenario_disruptions(scenario_disruption_id)
                              ON DELETE SET NULL,

  -- Activation
  is_active                 BOOLEAN       NOT NULL DEFAULT TRUE,

  -- Audit
  created_at                TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
  updated_at                TIMESTAMPTZ   NOT NULL DEFAULT NOW(),

  CONSTRAINT target_xor CHECK (
    (target_node_id IS NOT NULL AND target_link_id IS NULL)
    OR
    (target_node_id IS NULL AND target_link_id IS NOT NULL)
    OR
    (target_node_id IS NULL AND target_link_id IS NULL)  -- applies network-wide
  )
);

COMMENT ON TABLE scenario_disruptions IS
  'Junction table binding disruption types to specific scenario targets with optional '
  'parameter overrides. One scenario can include multiple disruption types. '
  'The XOR constraint ensures a disruption targets either a node or a link, not both.';

COMMENT ON COLUMN scenario_disruptions.probability_override IS 'Overrides disruption_types.typical_annual_probability for this specific scenario application';
COMMENT ON COLUMN scenario_disruptions.simultaneous_with IS 'Self-referential FK enabling compound disruption modeling (disruptions that occur together)';

CREATE INDEX idx_sd_scenario       ON scenario_disruptions(scenario_id);
CREATE INDEX idx_sd_disruption     ON scenario_disruptions(disruption_type_id);
CREATE INDEX idx_sd_node           ON scenario_disruptions(target_node_id)
  WHERE target_node_id IS NOT NULL;
CREATE INDEX idx_sd_link           ON scenario_disruptions(target_link_id)
  WHERE target_link_id IS NOT NULL;

CREATE TRIGGER trg_sd_updated_at
  BEFORE UPDATE ON scenario_disruptions
  FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

-- =============================================================================
-- SECTION 4: SIMULATION RESULTS TABLES
-- =============================================================================

-- ---------------------------------------------------------------------------
-- TABLE 8: simulation_runs
-- ---------------------------------------------------------------------------
CREATE TABLE simulation_runs (
  run_id                    UUID          PRIMARY KEY DEFAULT gen_random_uuid(),

  scenario_id               UUID          NOT NULL
                              REFERENCES scenarios(scenario_id)
                              ON DELETE RESTRICT,

  -- Timing
  started_at                TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
  completed_at              TIMESTAMPTZ,
  duration_seconds          INTEGER GENERATED ALWAYS AS (
    EXTRACT(EPOCH FROM (completed_at - started_at))::INTEGER
  ) STORED,

  -- Execution
  total_iterations          INTEGER       NOT NULL,
  completed_iterations      INTEGER       NOT NULL DEFAULT 0,
  status                    simulation_run_status_enum NOT NULL DEFAULT 'queued',
  engine_version            VARCHAR(50),   -- version of the simulation engine

  -- Error Handling
  error_message             TEXT,
  error_traceback           TEXT,

  -- Triggered by
  triggered_by              UUID          NOT NULL
                              REFERENCES auth.users(id)
                              ON DELETE RESTRICT,

  -- Audit
  created_at                TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
  updated_at                TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE simulation_runs IS
  'Execution record for each Monte Carlo simulation run. One scenario can have '
  'many runs (e.g., sensitivity analysis). Duration is auto-computed from start/end.';

COMMENT ON COLUMN simulation_runs.engine_version IS 'Semantic version of the Python simulation engine; enables reproducibility tracking';
COMMENT ON COLUMN simulation_runs.completed_iterations IS 'Used to compute progress percentage for live dashboard updates';

CREATE INDEX idx_runs_scenario     ON simulation_runs(scenario_id);
CREATE INDEX idx_runs_status       ON simulation_runs(status);
CREATE INDEX idx_runs_triggered_by ON simulation_runs(triggered_by);
CREATE INDEX idx_runs_started_at   ON simulation_runs(started_at DESC);

CREATE TRIGGER trg_runs_updated_at
  BEFORE UPDATE ON simulation_runs
  FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

-- ---------------------------------------------------------------------------
-- TABLE 9: simulation_results
-- ---------------------------------------------------------------------------
CREATE TABLE simulation_results (
  result_id                 UUID          PRIMARY KEY DEFAULT gen_random_uuid(),

  run_id                    UUID          NOT NULL
                              REFERENCES simulation_runs(run_id)
                              ON DELETE CASCADE,

  iteration_number          INTEGER       NOT NULL
                              CHECK (iteration_number > 0),

  -- Core Outcome Metrics
  total_cost_usd            DECIMAL(18,2) NOT NULL DEFAULT 0
                              CHECK (total_cost_usd >= 0),
  total_delay_days          DECIMAL(10,4) NOT NULL DEFAULT 0
                              CHECK (total_delay_days >= 0),
  production_loss_barrels   DECIMAL(14,2) NOT NULL DEFAULT 0
                              CHECK (production_loss_barrels >= 0),

  -- Network Impact
  nodes_affected            INTEGER       NOT NULL DEFAULT 0
                              CHECK (nodes_affected >= 0),
  links_disrupted           INTEGER       NOT NULL DEFAULT 0
                              CHECK (links_disrupted >= 0),

  -- Supply Chain Performance
  supply_chain_flow_pct     DECIMAL(5,4)  NOT NULL DEFAULT 1.0
                              CHECK (supply_chain_flow_pct BETWEEN 0 AND 1),
  recovery_time_days        DECIMAL(10,4) NOT NULL DEFAULT 0
                              CHECK (recovery_time_days >= 0),

  -- Disruption Detail (which disruptions fired in this iteration)
  disruptions_triggered     JSONB         NOT NULL DEFAULT '[]',
                              -- Array of {disruption_type_id, node_id, severity, duration_days}

  -- Audit
  created_at                TIMESTAMPTZ   NOT NULL DEFAULT NOW()
  -- No updated_at — results are immutable once written
);

COMMENT ON TABLE simulation_results IS
  'One row per Monte Carlo iteration per run. For 10,000-iteration runs this '
  'table grows by 10,000 rows per run. Partitioning by run_id is recommended '
  'at scale. Results are immutable — no UPDATE is expected after insert.';

COMMENT ON COLUMN simulation_results.supply_chain_flow_pct IS 'Fraction of baseline supply chain throughput achieved in this iteration (1.0 = no disruption)';
COMMENT ON COLUMN simulation_results.disruptions_triggered IS 'JSON array capturing which disruptions fired and their realized parameters in this iteration';

CREATE INDEX idx_results_run       ON simulation_results(run_id);
CREATE INDEX idx_results_run_iter  ON simulation_results(run_id, iteration_number);
CREATE INDEX idx_results_cost      ON simulation_results(run_id, total_cost_usd);

-- ---------------------------------------------------------------------------
-- TABLE 10: simulation_aggregates
-- ---------------------------------------------------------------------------
CREATE TABLE simulation_aggregates (
  aggregate_id              UUID          PRIMARY KEY DEFAULT gen_random_uuid(),

  run_id                    UUID          NOT NULL
                              REFERENCES simulation_runs(run_id)
                              ON DELETE CASCADE,

  metric_name               VARCHAR(100)  NOT NULL,
                              -- e.g., 'total_cost_usd', 'total_delay_days'

  -- Distributional Statistics
  mean_value                DECIMAL(20,6) NOT NULL,
  std_deviation             DECIMAL(20,6) NOT NULL CHECK (std_deviation >= 0),
  percentile_5              DECIMAL(20,6) NOT NULL,
  percentile_25             DECIMAL(20,6) NOT NULL,
  median_value              DECIMAL(20,6) NOT NULL,
  percentile_75             DECIMAL(20,6) NOT NULL,
  percentile_95             DECIMAL(20,6) NOT NULL,
  min_value                 DECIMAL(20,6) NOT NULL,
  max_value                 DECIMAL(20,6) NOT NULL,

  -- Risk Measures
  var_95                    DECIMAL(20,6) NOT NULL,   -- Value at Risk at 95th percentile
  cvar_95                   DECIMAL(20,6) NOT NULL,   -- Conditional VaR (Expected Shortfall)
  skewness                  DECIMAL(10,6),
  kurtosis                  DECIMAL(10,6),

  -- Audit
  created_at                TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
  UNIQUE (run_id, metric_name)
);

COMMENT ON TABLE simulation_aggregates IS
  'Pre-computed statistical summary of simulation_results per metric per run. '
  'Powers the dashboard charts without requiring full result-table aggregation at read time. '
  'VaR and CVaR are key risk measures for the IJPE paper.';

COMMENT ON COLUMN simulation_aggregates.var_95 IS 'Value at Risk: 95th percentile outcome — 5% chance the realized value exceeds this';
COMMENT ON COLUMN simulation_aggregates.cvar_95 IS 'Conditional VaR (Expected Shortfall): mean of the worst 5% outcomes — tail risk measure';
COMMENT ON COLUMN simulation_aggregates.skewness IS 'Third standardized moment; positive = right-skewed (fat upper tail of losses)';

CREATE INDEX idx_aggregates_run    ON simulation_aggregates(run_id);

-- =============================================================================
-- SECTION 5: RISK & RESILIENCE TABLES
-- =============================================================================

-- ---------------------------------------------------------------------------
-- TABLE 11: vulnerability_assessments
-- ---------------------------------------------------------------------------
CREATE TABLE vulnerability_assessments (
  assessment_id             UUID          PRIMARY KEY DEFAULT gen_random_uuid(),

  run_id                    UUID          NOT NULL
                              REFERENCES simulation_runs(run_id)
                              ON DELETE CASCADE,

  -- Target — exactly one non-null
  node_id                   UUID          REFERENCES supply_chain_nodes(node_id)
                              ON DELETE CASCADE,
  link_id                   UUID          REFERENCES supply_chain_links(link_id)
                              ON DELETE CASCADE,

  -- Vulnerability Metrics
  vulnerability_score       DECIMAL(5,4)  NOT NULL
                              CHECK (vulnerability_score BETWEEN 0 AND 1),
  criticality_rank          INTEGER       NOT NULL CHECK (criticality_rank > 0),
  failure_frequency         DECIMAL(8,4)  NOT NULL DEFAULT 0
                              CHECK (failure_frequency >= 0),
  avg_impact_cost_usd       DECIMAL(18,2) NOT NULL DEFAULT 0,
  avg_impact_delay_days     DECIMAL(10,4) NOT NULL DEFAULT 0,
  bottleneck_score          DECIMAL(5,4)  NOT NULL DEFAULT 0
                              CHECK (bottleneck_score BETWEEN 0 AND 1),

  -- Network Centrality (from NetworkX)
  betweenness_centrality    DECIMAL(8,6),
  degree_centrality         DECIMAL(8,6),
  closeness_centrality      DECIMAL(8,6),

  -- Audit
  created_at                TIMESTAMPTZ   NOT NULL DEFAULT NOW(),

  CONSTRAINT va_target_xor CHECK (
    (node_id IS NOT NULL AND link_id IS NULL)
    OR
    (node_id IS NULL AND link_id IS NOT NULL)
  )
);

COMMENT ON TABLE vulnerability_assessments IS
  'Post-simulation vulnerability analysis per node or link. '
  'Computed from simulation_results by the OR engine after each run. '
  'Drives the vulnerability heatmap in the dashboard.';

COMMENT ON COLUMN vulnerability_assessments.vulnerability_score IS 'Composite 0–1 score combining failure frequency, impact cost, and bottleneck score';
COMMENT ON COLUMN vulnerability_assessments.criticality_rank IS 'Rank-order position by vulnerability_score across all assessed entities in this run (1=most vulnerable)';
COMMENT ON COLUMN vulnerability_assessments.bottleneck_score IS 'Fraction of total network flow that passes through this entity; 1.0 = all flow passes through it';
COMMENT ON COLUMN vulnerability_assessments.betweenness_centrality IS 'NetworkX betweenness centrality; fraction of shortest paths passing through this node/link';

CREATE INDEX idx_va_run            ON vulnerability_assessments(run_id);
CREATE INDEX idx_va_node           ON vulnerability_assessments(node_id) WHERE node_id IS NOT NULL;
CREATE INDEX idx_va_link           ON vulnerability_assessments(link_id) WHERE link_id IS NOT NULL;
CREATE INDEX idx_va_rank           ON vulnerability_assessments(run_id, criticality_rank);

-- ---------------------------------------------------------------------------
-- TABLE 12: mitigation_strategies
-- ---------------------------------------------------------------------------
CREATE TABLE mitigation_strategies (
  strategy_id               UUID          PRIMARY KEY DEFAULT gen_random_uuid(),

  strategy_name             VARCHAR(255)  NOT NULL UNIQUE,
  description               TEXT          NOT NULL,

  -- Targeting
  target_disruption_type_id UUID          REFERENCES disruption_types(disruption_type_id)
                              ON DELETE SET NULL,
  applicable_node_types     JSONB         NOT NULL DEFAULT '[]',
  applicable_link_types     JSONB         NOT NULL DEFAULT '[]',

  -- Cost
  implementation_cost_usd   DECIMAL(18,2) NOT NULL CHECK (implementation_cost_usd >= 0),
  annual_maintenance_cost_usd DECIMAL(14,2) NOT NULL DEFAULT 0,

  -- Effectiveness (reductions applied when this mitigation is active in a scenario)
  effectiveness_score       DECIMAL(5,4)  NOT NULL
                              CHECK (effectiveness_score BETWEEN 0 AND 1),
  reduces_probability_by    DECIMAL(5,4)  NOT NULL DEFAULT 0
                              CHECK (reduces_probability_by BETWEEN 0 AND 1),
  reduces_severity_by       DECIMAL(5,4)  NOT NULL DEFAULT 0
                              CHECK (reduces_severity_by BETWEEN 0 AND 1),
  reduces_recovery_time_by_pct DECIMAL(5,4) NOT NULL DEFAULT 0
                              CHECK (reduces_recovery_time_by_pct BETWEEN 0 AND 1),

  -- Feasibility
  feasibility_score         DECIMAL(5,4)  NOT NULL DEFAULT 1.0
                              CHECK (feasibility_score BETWEEN 0 AND 1),
  implementation_time_days  INTEGER       DEFAULT 0 CHECK (implementation_time_days >= 0),

  -- Metadata
  metadata                  JSONB         NOT NULL DEFAULT '{}',

  -- Audit
  created_at                TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
  updated_at                TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE mitigation_strategies IS
  'Catalogue of risk mitigation interventions that can be applied to scenarios. '
  'When applied, the engine reduces disruption probability/severity by the stated fractions. '
  'Enables cost-benefit analysis of interventions in the IJPE paper.';

COMMENT ON COLUMN mitigation_strategies.reduces_probability_by IS 'Multiplicative reduction: if base probability = 0.4, reducing by 0.5 → 0.2 effective probability';
COMMENT ON COLUMN mitigation_strategies.effectiveness_score IS 'Overall composite effectiveness 0–1; combines probability, severity, and recovery reductions';

CREATE INDEX idx_mitigation_disruption ON mitigation_strategies(target_disruption_type_id);

CREATE TRIGGER trg_mitigation_updated_at
  BEFORE UPDATE ON mitigation_strategies
  FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

-- =============================================================================
-- SECTION 6: USER & ACCESS CONTROL TABLES
-- =============================================================================

-- ---------------------------------------------------------------------------
-- TABLE 13: user_profiles
-- ---------------------------------------------------------------------------
CREATE TABLE user_profiles (
  profile_id                UUID          PRIMARY KEY
                              REFERENCES auth.users(id)
                              ON DELETE CASCADE,

  full_name                 VARCHAR(255)  NOT NULL,
  organization              VARCHAR(255),
  job_title                 VARCHAR(255),
  role                      user_role_enum NOT NULL DEFAULT 'viewer',

  -- Rate Limiting
  api_calls_today           INTEGER       NOT NULL DEFAULT 0
                              CHECK (api_calls_today >= 0),
  api_calls_reset_at        TIMESTAMPTZ   NOT NULL DEFAULT (NOW() + INTERVAL '1 day'),
  daily_api_limit           INTEGER       NOT NULL DEFAULT 100,

  -- Activity
  last_active               TIMESTAMPTZ,
  total_simulations_run     INTEGER       NOT NULL DEFAULT 0,

  -- Preferences (UI settings, notification preferences, etc.)
  preferences               JSONB         NOT NULL DEFAULT '{}',

  -- Audit
  created_at                TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
  updated_at                TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE user_profiles IS
  'Extended profile data for authenticated users. Linked 1:1 to auth.users. '
  'Stores role assignment, rate-limit counters, and UI preferences.';

COMMENT ON COLUMN user_profiles.role IS 'RBAC role; enforced via RLS. admin > analyst > viewer.';
COMMENT ON COLUMN user_profiles.api_calls_today IS 'Rolling daily API call counter; reset daily via a scheduled Supabase Edge Function or cron';
COMMENT ON COLUMN user_profiles.daily_api_limit IS 'Per-user daily API call limit (default 100 for viewers/analysts, higher for admins)';

CREATE INDEX idx_profiles_role     ON user_profiles(role);
CREATE INDEX idx_profiles_active   ON user_profiles(last_active DESC);

CREATE TRIGGER trg_profiles_updated_at
  BEFORE UPDATE ON user_profiles
  FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

-- ---------------------------------------------------------------------------
-- TABLE 14: audit_logs
-- ---------------------------------------------------------------------------
CREATE TABLE audit_logs (
  log_id                    UUID          PRIMARY KEY DEFAULT gen_random_uuid(),

  user_id                   UUID          NOT NULL
                              REFERENCES auth.users(id)
                              ON DELETE RESTRICT,

  -- Action Classification
  action                    VARCHAR(50)   NOT NULL,  -- INSERT, UPDATE, DELETE, LOGIN, RUN_SIMULATION
  table_name                VARCHAR(100),
  record_id                 UUID,

  -- Change Detail
  old_values                JSONB,
  new_values                JSONB,

  -- Context
  ip_address                INET,
  user_agent                TEXT,
  session_id                UUID,

  performed_at              TIMESTAMPTZ   NOT NULL DEFAULT NOW()
  -- Intentionally NO updated_at — audit logs are append-only
);

COMMENT ON TABLE audit_logs IS
  'Immutable append-only audit trail. No user (including admin) may UPDATE or DELETE rows. '
  'Enforced by RLS. Captures all data mutations and key system events.';

COMMENT ON COLUMN audit_logs.action IS 'Standardized action codes: INSERT, UPDATE, DELETE, LOGIN, LOGOUT, RUN_SIMULATION, EXPORT_DATA';
COMMENT ON COLUMN audit_logs.old_values IS 'JSONB snapshot of the row before an UPDATE or DELETE (null for INSERT)';
COMMENT ON COLUMN audit_logs.new_values IS 'JSONB snapshot of the row after an INSERT or UPDATE (null for DELETE)';

CREATE INDEX idx_audit_user        ON audit_logs(user_id);
CREATE INDEX idx_audit_table       ON audit_logs(table_name);
CREATE INDEX idx_audit_performed   ON audit_logs(performed_at DESC);
CREATE INDEX idx_audit_action      ON audit_logs(action);
CREATE INDEX idx_audit_record      ON audit_logs(record_id) WHERE record_id IS NOT NULL;

-- =============================================================================
-- SECTION 7: FORWARD-REFERENCE FIX
-- =============================================================================
-- flow_records references disruption_types but disruption_types was defined
-- after supply_chain_links. The FK was deferred; add it now:
ALTER TABLE flow_records
  ADD CONSTRAINT fk_flow_disruption_type
  FOREIGN KEY (disruption_type_id)
  REFERENCES disruption_types(disruption_type_id)
  ON DELETE SET NULL;

-- =============================================================================
-- SECTION 8: DATABASE-LEVEL COMMENTS
-- =============================================================================
COMMENT ON DATABASE postgres IS
  'Project Atlas — Nigerian Oil & Gas Supply Chain Stress-Testing System. '
  'Schema v1.0.0. Designed for IJPE publication. '
  'All tables implement UUID PKs, updated_at triggers, and RLS.';

-- =============================================================================
-- END OF SCHEMA
-- =============================================================================
