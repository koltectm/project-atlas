"""
app/db/models.py
================
SQLAlchemy 2.0 ORM models mirroring the Phase 1 PostgreSQL schema exactly.

Design rules:
- Use mapped_column() syntax (SQLAlchemy 2.0 Mapped API) — not Column()
- All ENUMs defined as Python Enum classes matching PostgreSQL ENUM names exactly
- All relationships use back_populates for bidirectional navigation
- GENERATED ALWAYS STORED columns (delay_days, cost_overrun_usd, duration_seconds)
  are declared with server_default=FetchedValue() and init=False
- auth.users is referenced by string FK "auth.users.id" (Supabase schema)
- __repr__ on every model for debuggability
"""

from __future__ import annotations

import enum
import uuid
from datetime import date, datetime
from typing import Any, Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    FetchedValue,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import (
    ARRAY,
    INET,
    JSONB,
    UUID as PG_UUID,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# ─── Base ─────────────────────────────────────────────────────────────────────

class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""

    # PostgreSQL type annotation map
    type_annotation_map = {
        dict: JSONB,
        list: ARRAY(String),
    }


# ─── Python Enum classes (must match PostgreSQL ENUM values exactly) ──────────

class NodeTypeEnum(str, enum.Enum):
    wellhead         = "wellhead"
    pipeline         = "pipeline"
    export_terminal  = "export_terminal"
    refinery         = "refinery"
    storage_depot    = "storage_depot"
    port             = "port"
    distribution_hub = "distribution_hub"
    consumer         = "consumer"


class StageEnum(str, enum.Enum):
    upstream   = "upstream"
    midstream  = "midstream"
    downstream = "downstream"


class GeopoliticalZoneEnum(str, enum.Enum):
    SW = "SW"
    SE = "SE"
    SS = "SS"
    NW = "NW"
    NE = "NE"
    NC = "NC"


class NodeStatusEnum(str, enum.Enum):
    operational = "operational"
    degraded    = "degraded"
    offline     = "offline"


class LinkTypeEnum(str, enum.Enum):
    pipeline  = "pipeline"
    road      = "road"
    sea_route = "sea_route"
    rail      = "rail"
    river     = "river"


class ProductTypeEnum(str, enum.Enum):
    crude_oil = "crude_oil"
    petrol    = "petrol"
    diesel    = "diesel"
    kerosene  = "kerosene"
    lpg       = "lpg"
    jet_fuel  = "jet_fuel"


class FlowStatusEnum(str, enum.Enum):
    completed = "completed"
    delayed   = "delayed"
    blocked   = "blocked"
    partial   = "partial"


class DisruptionCategoryEnum(str, enum.Enum):
    infrastructure = "infrastructure"
    logistics      = "logistics"
    geopolitical   = "geopolitical"
    environmental  = "environmental"
    operational    = "operational"
    economic       = "economic"
    cybersecurity  = "cybersecurity"
    force_majeure  = "force_majeure"


class ScenarioStatusEnum(str, enum.Enum):
    draft     = "draft"
    running   = "running"
    completed = "completed"
    failed    = "failed"


class SimulationRunStatusEnum(str, enum.Enum):
    queued    = "queued"
    running   = "running"
    completed = "completed"
    failed    = "failed"


class UserRoleEnum(str, enum.Enum):
    admin   = "admin"
    analyst = "analyst"
    viewer  = "viewer"


# ─── SQLAlchemy ENUM types (mapped to PostgreSQL ENUM types by name) ──────────
from sqlalchemy import Enum as SAEnum

SA_NodeTypeEnum          = SAEnum(NodeTypeEnum,          name="node_type_enum",           schema="public")
SA_StageEnum             = SAEnum(StageEnum,             name="stage_enum",               schema="public")
SA_GeopoliticalZoneEnum  = SAEnum(GeopoliticalZoneEnum,  name="geopolitical_zone_enum",   schema="public")
SA_NodeStatusEnum        = SAEnum(NodeStatusEnum,        name="node_status_enum",         schema="public")
SA_LinkTypeEnum          = SAEnum(LinkTypeEnum,          name="link_type_enum",           schema="public")
SA_ProductTypeEnum       = SAEnum(ProductTypeEnum,       name="product_type_enum",        schema="public")
SA_FlowStatusEnum        = SAEnum(FlowStatusEnum,        name="flow_status_enum",         schema="public")
SA_DisruptionCategoryEnum = SAEnum(DisruptionCategoryEnum, name="disruption_category_enum", schema="public")
SA_ScenarioStatusEnum    = SAEnum(ScenarioStatusEnum,    name="scenario_status_enum",     schema="public")
SA_SimRunStatusEnum      = SAEnum(SimulationRunStatusEnum, name="simulation_run_status_enum", schema="public")
SA_UserRoleEnum          = SAEnum(UserRoleEnum,          name="user_role_enum",           schema="public")


# ─── Model 1: supply_chain_nodes ──────────────────────────────────────────────

class SupplyChainNode(Base):
    """
    Master registry of all physical nodes in the Nigerian oil & gas supply chain.
    Maps to: public.supply_chain_nodes
    """
    __tablename__ = "supply_chain_nodes"
    __table_args__ = (
        CheckConstraint("current_utilization_pct BETWEEN 0 AND 1", name="nodes_utilization_range"),
        CheckConstraint("redundancy_score BETWEEN 0 AND 1",        name="nodes_redundancy_range"),
        CheckConstraint("criticality_score BETWEEN 0 AND 1",       name="nodes_criticality_range"),
        Index("idx_nodes_type",        "node_type"),
        Index("idx_nodes_stage",       "stage"),
        Index("idx_nodes_status",      "status"),
        Index("idx_nodes_zone",        "geopolitical_zone"),
        Index("idx_nodes_operator",    "operator"),
        Index("idx_nodes_criticality", "criticality_score"),
        {"schema": "public"},
    )

    node_id:                   Mapped[uuid.UUID]            = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=FetchedValue())
    node_name:                 Mapped[str]                  = mapped_column(String(255), nullable=False)
    node_code:                 Mapped[str]                  = mapped_column(String(50), nullable=False, unique=True)
    node_type:                 Mapped[NodeTypeEnum]         = mapped_column(SA_NodeTypeEnum, nullable=False)
    stage:                     Mapped[StageEnum]            = mapped_column(SA_StageEnum, nullable=False)
    latitude:                  Mapped[float]                = mapped_column(Numeric(10, 7), nullable=False)
    longitude:                 Mapped[float]                = mapped_column(Numeric(10, 7), nullable=False)
    state_location:            Mapped[str]                  = mapped_column(String(100), nullable=False)
    geopolitical_zone:         Mapped[GeopoliticalZoneEnum] = mapped_column(SA_GeopoliticalZoneEnum, nullable=False)
    address_description:       Mapped[Optional[str]]        = mapped_column(Text)
    operator:                  Mapped[str]                  = mapped_column(String(255), nullable=False)
    operator_type:             Mapped[Optional[str]]        = mapped_column(String(100))
    capacity_bpd:              Mapped[float]                = mapped_column(Numeric(12, 2), nullable=False, server_default="0")
    current_utilization_pct:   Mapped[float]                = mapped_column(Numeric(5, 4),  nullable=False, server_default="0")
    annual_throughput_barrels: Mapped[Optional[float]]      = mapped_column(Numeric(18, 2))
    status:                    Mapped[NodeStatusEnum]       = mapped_column(SA_NodeStatusEnum, nullable=False, server_default="operational")
    redundancy_score:          Mapped[float]                = mapped_column(Numeric(5, 4), nullable=False, server_default="0")
    criticality_score:         Mapped[float]                = mapped_column(Numeric(5, 4), nullable=False, server_default="0")
    mean_time_between_failures_days: Mapped[Optional[float]] = mapped_column(Numeric(8, 2))
    mean_time_to_repair_days:  Mapped[Optional[float]]      = mapped_column(Numeric(8, 2))
    daily_operating_cost_usd:  Mapped[Optional[float]]      = mapped_column(Numeric(14, 2))
    replacement_cost_usd:      Mapped[Optional[float]]      = mapped_column(Numeric(18, 2))
    metadata:                  Mapped[dict]                 = mapped_column(JSONB, nullable=False, server_default="{}")
    created_at:                Mapped[datetime]             = mapped_column(DateTime(timezone=True), nullable=False, server_default=FetchedValue())
    updated_at:                Mapped[datetime]             = mapped_column(DateTime(timezone=True), nullable=False, server_default=FetchedValue())

    # Relationships
    outgoing_links:      Mapped[list["SupplyChainLink"]]    = relationship("SupplyChainLink", foreign_keys="SupplyChainLink.source_node_id", back_populates="source_node")
    incoming_links:      Mapped[list["SupplyChainLink"]]    = relationship("SupplyChainLink", foreign_keys="SupplyChainLink.target_node_id", back_populates="target_node")
    inventory_levels:    Mapped[list["InventoryLevel"]]     = relationship("InventoryLevel",  back_populates="node",       cascade="all, delete-orphan")
    vulnerability_assessments: Mapped[list["VulnerabilityAssessment"]] = relationship("VulnerabilityAssessment", back_populates="node")

    def __repr__(self) -> str:
        return f"<SupplyChainNode {self.node_code!r} {self.node_type.value} [{self.status.value}]>"


# ─── Model 2: supply_chain_links ──────────────────────────────────────────────

class SupplyChainLink(Base):
    """
    Directed edge in the supply chain network graph.
    Maps to: public.supply_chain_links
    """
    __tablename__ = "supply_chain_links"
    __table_args__ = (
        CheckConstraint("source_node_id <> target_node_id",              name="no_self_loop"),
        CheckConstraint("current_utilization_pct BETWEEN 0 AND 1",       name="links_utilization_range"),
        CheckConstraint("reliability_score BETWEEN 0 AND 1",             name="links_reliability_range"),
        CheckConstraint("vandalism_risk_score BETWEEN 0 AND 1",          name="links_vandalism_range"),
        CheckConstraint("distance_km > 0",                               name="links_distance_positive"),
        CheckConstraint("normal_lead_time_days > 0",                     name="links_leadtime_positive"),
        CheckConstraint("transport_cost_per_barrel >= 0",                name="links_cost_nonneg"),
        CheckConstraint("max_capacity_bpd > 0",                         name="links_capacity_positive"),
        Index("idx_links_source",      "source_node_id"),
        Index("idx_links_target",      "target_node_id"),
        Index("idx_links_type",        "link_type"),
        Index("idx_links_status",      "status"),
        Index("idx_links_reliability", "reliability_score"),
        {"schema": "public"},
    )

    link_id:                  Mapped[uuid.UUID]         = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=FetchedValue())
    link_name:                Mapped[str]               = mapped_column(String(255), nullable=False)
    link_code:                Mapped[str]               = mapped_column(String(50), nullable=False, unique=True)
    link_type:                Mapped[LinkTypeEnum]      = mapped_column(SA_LinkTypeEnum, nullable=False)
    source_node_id:           Mapped[uuid.UUID]         = mapped_column(PG_UUID(as_uuid=True), ForeignKey("public.supply_chain_nodes.node_id", ondelete="RESTRICT"), nullable=False)
    target_node_id:           Mapped[uuid.UUID]         = mapped_column(PG_UUID(as_uuid=True), ForeignKey("public.supply_chain_nodes.node_id", ondelete="RESTRICT"), nullable=False)
    distance_km:              Mapped[float]             = mapped_column(Numeric(10, 3), nullable=False)
    diameter_inches:          Mapped[Optional[float]]   = mapped_column(Numeric(6, 2))
    pipeline_year_installed:  Mapped[Optional[int]]     = mapped_column(SmallInteger)
    normal_lead_time_days:    Mapped[float]             = mapped_column(Numeric(8, 4), nullable=False)
    transport_cost_per_barrel: Mapped[float]            = mapped_column(Numeric(10, 4), nullable=False)
    max_capacity_bpd:         Mapped[float]             = mapped_column(Numeric(12, 2), nullable=False)
    current_utilization_pct:  Mapped[float]             = mapped_column(Numeric(5, 4), nullable=False, server_default="0")
    reliability_score:        Mapped[float]             = mapped_column(Numeric(5, 4), nullable=False, server_default="0.9")
    vandalism_risk_score:     Mapped[Optional[float]]   = mapped_column(Numeric(5, 4), server_default="0")
    is_critical_path:         Mapped[bool]              = mapped_column(Boolean, nullable=False, server_default="false")
    alternative_routes:       Mapped[dict]              = mapped_column(JSONB, nullable=False, server_default="[]")
    status:                   Mapped[NodeStatusEnum]    = mapped_column(SA_NodeStatusEnum, nullable=False, server_default="operational")
    metadata:                 Mapped[dict]              = mapped_column(JSONB, nullable=False, server_default="{}")
    created_at:               Mapped[datetime]          = mapped_column(DateTime(timezone=True), nullable=False, server_default=FetchedValue())
    updated_at:               Mapped[datetime]          = mapped_column(DateTime(timezone=True), nullable=False, server_default=FetchedValue())

    # Relationships
    source_node: Mapped["SupplyChainNode"]        = relationship("SupplyChainNode", foreign_keys=[source_node_id], back_populates="outgoing_links")
    target_node: Mapped["SupplyChainNode"]        = relationship("SupplyChainNode", foreign_keys=[target_node_id], back_populates="incoming_links")
    flow_records: Mapped[list["FlowRecord"]]      = relationship("FlowRecord", back_populates="link", cascade="all, delete-orphan")
    vulnerability_assessments: Mapped[list["VulnerabilityAssessment"]] = relationship("VulnerabilityAssessment", back_populates="link")

    def __repr__(self) -> str:
        return f"<SupplyChainLink {self.link_code!r} {self.link_type.value} [{self.status.value}]>"


# ─── Model 3: inventory_levels ────────────────────────────────────────────────

class InventoryLevel(Base):
    """
    Current stock position for each (node, product) pair.
    Maps to: public.inventory_levels
    """
    __tablename__ = "inventory_levels"
    __table_args__ = (
        UniqueConstraint("node_id", "product_type", name="uq_inventory_node_product"),
        CheckConstraint("quantity_barrels >= 0",                          name="inv_qty_nonneg"),
        CheckConstraint("quantity_barrels <= maximum_capacity_barrels",   name="inv_quantity_le_capacity"),
        CheckConstraint("maximum_capacity_barrels > 0",                   name="inv_max_cap_positive"),
        Index("idx_inventory_node",    "node_id"),
        Index("idx_inventory_product", "product_type"),
        {"schema": "public"},
    )

    inventory_id:              Mapped[uuid.UUID]       = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=FetchedValue())
    node_id:                   Mapped[uuid.UUID]       = mapped_column(PG_UUID(as_uuid=True), ForeignKey("public.supply_chain_nodes.node_id", ondelete="CASCADE"), nullable=False)
    product_type:              Mapped[ProductTypeEnum] = mapped_column(SA_ProductTypeEnum, nullable=False)
    quantity_barrels:          Mapped[float]           = mapped_column(Numeric(14, 2), nullable=False, server_default="0")
    minimum_threshold_barrels: Mapped[float]           = mapped_column(Numeric(14, 2), nullable=False, server_default="0")
    maximum_capacity_barrels:  Mapped[float]           = mapped_column(Numeric(14, 2), nullable=False)
    reorder_point_barrels:     Mapped[float]           = mapped_column(Numeric(14, 2), nullable=False, server_default="0")
    safety_stock_barrels:      Mapped[float]           = mapped_column(Numeric(14, 2), nullable=False, server_default="0")
    unit_cost_usd:             Mapped[float]           = mapped_column(Numeric(10, 4), nullable=False, server_default="0")
    daily_consumption_rate_bpd: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), server_default="0")
    daily_supply_rate_bpd:     Mapped[Optional[float]] = mapped_column(Numeric(12, 2), server_default="0")
    last_updated:              Mapped[datetime]        = mapped_column(DateTime(timezone=True), nullable=False, server_default=FetchedValue())
    created_at:                Mapped[datetime]        = mapped_column(DateTime(timezone=True), nullable=False, server_default=FetchedValue())
    updated_at:                Mapped[datetime]        = mapped_column(DateTime(timezone=True), nullable=False, server_default=FetchedValue())

    # Relationships
    node: Mapped["SupplyChainNode"] = relationship("SupplyChainNode", back_populates="inventory_levels")

    def __repr__(self) -> str:
        return f"<InventoryLevel node={self.node_id} product={self.product_type.value} qty={self.quantity_barrels:,.0f}bbl>"


# ─── Model 4: flow_records ────────────────────────────────────────────────────

class FlowRecord(Base):
    """
    Historical ledger of product flows across supply chain links.
    Maps to: public.flow_records
    NOTE: delay_days and cost_overrun_usd are GENERATED ALWAYS STORED columns.
    """
    __tablename__ = "flow_records"
    __table_args__ = (
        CheckConstraint("volume_barrels > 0",           name="flow_volume_positive"),
        CheckConstraint("scheduled_cost_usd >= 0",      name="flow_sched_cost_nonneg"),
        Index("idx_flows_link",       "link_id"),
        Index("idx_flows_date",       "flow_date"),
        Index("idx_flows_product",    "product_type"),
        Index("idx_flows_status",     "flow_status"),
        Index("idx_flows_disruption", "disruption_type_id"),
        {"schema": "public"},
    )

    flow_id:                 Mapped[uuid.UUID]         = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=FetchedValue())
    link_id:                 Mapped[uuid.UUID]         = mapped_column(PG_UUID(as_uuid=True), ForeignKey("public.supply_chain_links.link_id", ondelete="CASCADE"), nullable=False)
    product_type:            Mapped[ProductTypeEnum]   = mapped_column(SA_ProductTypeEnum, nullable=False)
    volume_barrels:          Mapped[float]             = mapped_column(Numeric(14, 2), nullable=False)
    flow_date:               Mapped[date]              = mapped_column(Date, nullable=False)
    scheduled_lead_time_days: Mapped[float]            = mapped_column(Numeric(8, 4), nullable=False)
    actual_lead_time_days:   Mapped[Optional[float]]   = mapped_column(Numeric(8, 4))
    # GENERATED ALWAYS STORED — do NOT include in INSERT/UPDATE
    delay_days:              Mapped[Optional[float]]   = mapped_column(Numeric(8, 4), init=False, server_default=FetchedValue())
    scheduled_cost_usd:      Mapped[float]             = mapped_column(Numeric(14, 2), nullable=False)
    actual_cost_usd:         Mapped[Optional[float]]   = mapped_column(Numeric(14, 2))
    # GENERATED ALWAYS STORED
    cost_overrun_usd:        Mapped[Optional[float]]   = mapped_column(Numeric(14, 2), init=False, server_default=FetchedValue())
    flow_status:             Mapped[FlowStatusEnum]    = mapped_column(SA_FlowStatusEnum, nullable=False, server_default="completed")
    disruption_type_id:      Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("public.disruption_types.disruption_type_id", ondelete="SET NULL"))
    disruption_notes:        Mapped[Optional[str]]     = mapped_column(Text)
    created_at:              Mapped[datetime]          = mapped_column(DateTime(timezone=True), nullable=False, server_default=FetchedValue())
    updated_at:              Mapped[datetime]          = mapped_column(DateTime(timezone=True), nullable=False, server_default=FetchedValue())

    # Relationships
    link:             Mapped["SupplyChainLink"] = relationship("SupplyChainLink", back_populates="flow_records")
    disruption_type:  Mapped[Optional["DisruptionType"]] = relationship("DisruptionType", back_populates="flow_records")

    def __repr__(self) -> str:
        return f"<FlowRecord link={self.link_id} date={self.flow_date} vol={self.volume_barrels:,.0f}bbl [{self.flow_status.value}]>"


# ─── Model 5: disruption_types ────────────────────────────────────────────────

class DisruptionType(Base):
    """
    Parameterised catalogue of disruption types for Monte Carlo simulation.
    Maps to: public.disruption_types
    """
    __tablename__ = "disruption_types"
    __table_args__ = (
        UniqueConstraint("name", name="uq_disruption_name"),
        CheckConstraint("typical_duration_days_min <= typical_duration_days_mode AND typical_duration_days_mode <= typical_duration_days_max", name="duration_ordering"),
        CheckConstraint("severity_min <= severity_mode AND severity_mode <= severity_max", name="severity_ordering"),
        CheckConstraint("recovery_time_days_min <= recovery_time_days_max", name="recovery_ordering"),
        Index("idx_disruptions_category", "category"),
        {"schema": "public"},
    )

    disruption_type_id:          Mapped[uuid.UUID]              = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=FetchedValue())
    category:                    Mapped[DisruptionCategoryEnum]  = mapped_column(SA_DisruptionCategoryEnum, nullable=False)
    name:                        Mapped[str]                     = mapped_column(String(255), nullable=False)
    description:                 Mapped[str]                     = mapped_column(Text, nullable=False)
    typical_duration_days_min:   Mapped[float]                   = mapped_column(Numeric(8, 2), nullable=False)
    typical_duration_days_mode:  Mapped[float]                   = mapped_column(Numeric(8, 2), nullable=False)
    typical_duration_days_max:   Mapped[float]                   = mapped_column(Numeric(8, 2), nullable=False)
    typical_annual_probability:  Mapped[float]                   = mapped_column(Numeric(6, 4), nullable=False)
    severity_min:                Mapped[float]                   = mapped_column(Numeric(5, 4), nullable=False, server_default="0")
    severity_mode:               Mapped[float]                   = mapped_column(Numeric(5, 4), nullable=False, server_default="0.5")
    severity_max:                Mapped[float]                   = mapped_column(Numeric(5, 4), nullable=False, server_default="1")
    cost_multiplier_min:         Mapped[float]                   = mapped_column(Numeric(6, 3), nullable=False, server_default="1.0")
    cost_multiplier_max:         Mapped[float]                   = mapped_column(Numeric(6, 3), nullable=False, server_default="2.0")
    recovery_time_days_min:      Mapped[float]                   = mapped_column(Numeric(8, 2), nullable=False, server_default="0")
    recovery_time_days_max:      Mapped[float]                   = mapped_column(Numeric(8, 2), nullable=False)
    affected_node_types:         Mapped[dict]                    = mapped_column(JSONB, nullable=False, server_default="[]")
    affected_link_types:         Mapped[dict]                    = mapped_column(JSONB, nullable=False, server_default="[]")
    correlated_disruption_ids:   Mapped[dict]                    = mapped_column(JSONB, nullable=False, server_default="[]")
    cascading_probability:       Mapped[Optional[float]]         = mapped_column(Numeric(5, 4), server_default="0")
    created_at:                  Mapped[datetime]                = mapped_column(DateTime(timezone=True), nullable=False, server_default=FetchedValue())
    updated_at:                  Mapped[datetime]                = mapped_column(DateTime(timezone=True), nullable=False, server_default=FetchedValue())

    # Relationships
    flow_records:        Mapped[list["FlowRecord"]]            = relationship("FlowRecord", back_populates="disruption_type")
    scenario_disruptions: Mapped[list["ScenarioDisruption"]]  = relationship("ScenarioDisruption", back_populates="disruption_type")
    mitigation_strategies: Mapped[list["MitigationStrategy"]] = relationship("MitigationStrategy", back_populates="target_disruption_type")

    def __repr__(self) -> str:
        return f"<DisruptionType {self.name!r} [{self.category.value}] p={self.typical_annual_probability}>"


# ─── Model 6: scenarios ───────────────────────────────────────────────────────

class Scenario(Base):
    """
    User-defined simulation scenario.
    Maps to: public.scenarios
    """
    __tablename__ = "scenarios"
    __table_args__ = (
        CheckConstraint("simulation_iterations BETWEEN 100 AND 100000", name="sim_iter_range"),
        CheckConstraint("time_horizon_days BETWEEN 1 AND 3650",         name="time_horizon_range"),
        Index("idx_scenarios_created_by", "created_by"),
        Index("idx_scenarios_status",     "status"),
        Index("idx_scenarios_public",     "is_public"),
        {"schema": "public"},
    )

    scenario_id:           Mapped[uuid.UUID]           = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=FetchedValue())
    scenario_name:         Mapped[str]                 = mapped_column(String(255), nullable=False)
    description:           Mapped[Optional[str]]       = mapped_column(Text)
    version:               Mapped[int]                 = mapped_column(SmallInteger, nullable=False, server_default="1")
    created_by:            Mapped[uuid.UUID]           = mapped_column(PG_UUID(as_uuid=True), ForeignKey("auth.users.id", ondelete="RESTRICT"), nullable=False)
    is_public:             Mapped[bool]                = mapped_column(Boolean, nullable=False, server_default="false")
    simulation_iterations: Mapped[int]                 = mapped_column(Integer, nullable=False, server_default="10000")
    time_horizon_days:     Mapped[int]                 = mapped_column(Integer, nullable=False, server_default="365")
    random_seed:           Mapped[Optional[int]]       = mapped_column(Integer)
    status:                Mapped[ScenarioStatusEnum]  = mapped_column(SA_ScenarioStatusEnum, nullable=False, server_default="draft")
    configuration:         Mapped[dict]                = mapped_column(JSONB, nullable=False, server_default="{}")
    tags:                  Mapped[list]                = mapped_column(ARRAY(String), nullable=False, server_default="{}")
    created_at:            Mapped[datetime]            = mapped_column(DateTime(timezone=True), nullable=False, server_default=FetchedValue())
    updated_at:            Mapped[datetime]            = mapped_column(DateTime(timezone=True), nullable=False, server_default=FetchedValue())

    # Relationships
    disruptions:      Mapped[list["ScenarioDisruption"]]  = relationship("ScenarioDisruption", back_populates="scenario", cascade="all, delete-orphan")
    simulation_runs:  Mapped[list["SimulationRun"]]       = relationship("SimulationRun", back_populates="scenario")

    def __repr__(self) -> str:
        return f"<Scenario {self.scenario_name!r} [{self.status.value}] iter={self.simulation_iterations}>"


# ─── Model 7: scenario_disruptions ───────────────────────────────────────────

class ScenarioDisruption(Base):
    """
    Junction table binding disruption types to a scenario with optional overrides.
    Maps to: public.scenario_disruptions
    """
    __tablename__ = "scenario_disruptions"
    __table_args__ = (
        CheckConstraint(
            "(target_node_id IS NOT NULL AND target_link_id IS NULL) OR "
            "(target_node_id IS NULL AND target_link_id IS NOT NULL) OR "
            "(target_node_id IS NULL AND target_link_id IS NULL)",
            name="target_xor",
        ),
        Index("idx_sd_scenario",   "scenario_id"),
        Index("idx_sd_disruption", "disruption_type_id"),
        {"schema": "public"},
    )

    scenario_disruption_id: Mapped[uuid.UUID]        = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=FetchedValue())
    scenario_id:            Mapped[uuid.UUID]        = mapped_column(PG_UUID(as_uuid=True), ForeignKey("public.scenarios.scenario_id", ondelete="CASCADE"), nullable=False)
    disruption_type_id:     Mapped[uuid.UUID]        = mapped_column(PG_UUID(as_uuid=True), ForeignKey("public.disruption_types.disruption_type_id", ondelete="RESTRICT"), nullable=False)
    target_node_id:         Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("public.supply_chain_nodes.node_id", ondelete="RESTRICT"))
    target_link_id:         Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("public.supply_chain_links.link_id", ondelete="RESTRICT"))
    probability_override:   Mapped[Optional[float]]  = mapped_column(Numeric(6, 4))
    severity_override:      Mapped[Optional[float]]  = mapped_column(Numeric(5, 4))
    duration_days_override: Mapped[Optional[float]]  = mapped_column(Numeric(8, 2))
    simultaneous_with:      Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("public.scenario_disruptions.scenario_disruption_id", ondelete="SET NULL"))
    is_active:              Mapped[bool]             = mapped_column(Boolean, nullable=False, server_default="true")
    created_at:             Mapped[datetime]         = mapped_column(DateTime(timezone=True), nullable=False, server_default=FetchedValue())
    updated_at:             Mapped[datetime]         = mapped_column(DateTime(timezone=True), nullable=False, server_default=FetchedValue())

    # Relationships
    scenario:       Mapped["Scenario"]              = relationship("Scenario", back_populates="disruptions")
    disruption_type: Mapped["DisruptionType"]       = relationship("DisruptionType", back_populates="scenario_disruptions")
    target_node:    Mapped[Optional["SupplyChainNode"]] = relationship("SupplyChainNode", foreign_keys=[target_node_id])
    target_link:    Mapped[Optional["SupplyChainLink"]] = relationship("SupplyChainLink", foreign_keys=[target_link_id])

    def __repr__(self) -> str:
        target = f"node={self.target_node_id}" if self.target_node_id else f"link={self.target_link_id}"
        return f"<ScenarioDisruption scenario={self.scenario_id} {target} active={self.is_active}>"


# ─── Model 8: simulation_runs ─────────────────────────────────────────────────

class SimulationRun(Base):
    """
    Execution record for each Monte Carlo run.
    Maps to: public.simulation_runs
    NOTE: duration_seconds is GENERATED ALWAYS STORED.
    """
    __tablename__ = "simulation_runs"
    __table_args__ = (
        Index("idx_runs_scenario",     "scenario_id"),
        Index("idx_runs_status",       "status"),
        Index("idx_runs_triggered_by", "triggered_by"),
        Index("idx_runs_started_at",   "started_at"),
        {"schema": "public"},
    )

    run_id:               Mapped[uuid.UUID]               = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=FetchedValue())
    scenario_id:          Mapped[uuid.UUID]               = mapped_column(PG_UUID(as_uuid=True), ForeignKey("public.scenarios.scenario_id", ondelete="RESTRICT"), nullable=False)
    started_at:           Mapped[datetime]                = mapped_column(DateTime(timezone=True), nullable=False, server_default=FetchedValue())
    completed_at:         Mapped[Optional[datetime]]      = mapped_column(DateTime(timezone=True))
    # GENERATED ALWAYS STORED
    duration_seconds:     Mapped[Optional[int]]           = mapped_column(Integer, init=False, server_default=FetchedValue())
    total_iterations:     Mapped[int]                     = mapped_column(Integer, nullable=False)
    completed_iterations: Mapped[int]                     = mapped_column(Integer, nullable=False, server_default="0")
    status:               Mapped[SimulationRunStatusEnum] = mapped_column(SA_SimRunStatusEnum, nullable=False, server_default="queued")
    engine_version:       Mapped[Optional[str]]           = mapped_column(String(50))
    error_message:        Mapped[Optional[str]]           = mapped_column(Text)
    error_traceback:      Mapped[Optional[str]]           = mapped_column(Text)
    triggered_by:         Mapped[uuid.UUID]               = mapped_column(PG_UUID(as_uuid=True), ForeignKey("auth.users.id", ondelete="RESTRICT"), nullable=False)
    created_at:           Mapped[datetime]                = mapped_column(DateTime(timezone=True), nullable=False, server_default=FetchedValue())
    updated_at:           Mapped[datetime]                = mapped_column(DateTime(timezone=True), nullable=False, server_default=FetchedValue())

    # Relationships
    scenario:                Mapped["Scenario"]                    = relationship("Scenario", back_populates="simulation_runs")
    results:                 Mapped[list["SimulationResult"]]      = relationship("SimulationResult", back_populates="run", cascade="all, delete-orphan")
    aggregates:              Mapped[list["SimulationAggregate"]]   = relationship("SimulationAggregate", back_populates="run", cascade="all, delete-orphan")
    vulnerability_assessments: Mapped[list["VulnerabilityAssessment"]] = relationship("VulnerabilityAssessment", back_populates="run", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<SimulationRun {self.run_id} [{self.status.value}] iter={self.total_iterations}>"


# ─── Model 9: simulation_results ─────────────────────────────────────────────

class SimulationResult(Base):
    """
    One row per Monte Carlo iteration. Immutable after write (no updated_at).
    Maps to: public.simulation_results
    """
    __tablename__ = "simulation_results"
    __table_args__ = (
        CheckConstraint("iteration_number > 0",              name="iter_positive"),
        CheckConstraint("total_cost_usd >= 0",               name="cost_nonneg"),
        CheckConstraint("total_delay_days >= 0",             name="delay_nonneg"),
        CheckConstraint("production_loss_barrels >= 0",      name="loss_nonneg"),
        CheckConstraint("supply_chain_flow_pct BETWEEN 0 AND 1", name="flow_pct_range"),
        CheckConstraint("recovery_time_days >= 0",           name="recovery_nonneg"),
        Index("idx_results_run",      "run_id"),
        Index("idx_results_run_iter", "run_id", "iteration_number"),
        Index("idx_results_cost",     "run_id", "total_cost_usd"),
        {"schema": "public"},
    )

    result_id:               Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=FetchedValue())
    run_id:                  Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("public.simulation_runs.run_id", ondelete="CASCADE"), nullable=False)
    iteration_number:        Mapped[int]       = mapped_column(Integer, nullable=False)
    total_cost_usd:          Mapped[float]     = mapped_column(Numeric(18, 2), nullable=False, server_default="0")
    total_delay_days:        Mapped[float]     = mapped_column(Numeric(10, 4), nullable=False, server_default="0")
    production_loss_barrels: Mapped[float]     = mapped_column(Numeric(14, 2), nullable=False, server_default="0")
    nodes_affected:          Mapped[int]       = mapped_column(Integer, nullable=False, server_default="0")
    links_disrupted:         Mapped[int]       = mapped_column(Integer, nullable=False, server_default="0")
    supply_chain_flow_pct:   Mapped[float]     = mapped_column(Numeric(5, 4), nullable=False, server_default="1.0")
    recovery_time_days:      Mapped[float]     = mapped_column(Numeric(10, 4), nullable=False, server_default="0")
    disruptions_triggered:   Mapped[dict]      = mapped_column(JSONB, nullable=False, server_default="[]")
    created_at:              Mapped[datetime]  = mapped_column(DateTime(timezone=True), nullable=False, server_default=FetchedValue())
    # No updated_at — immutable

    # Relationships
    run: Mapped["SimulationRun"] = relationship("SimulationRun", back_populates="results")

    def __repr__(self) -> str:
        return f"<SimulationResult run={self.run_id} iter={self.iteration_number} cost=${self.total_cost_usd:,.0f}>"


# ─── Model 10: simulation_aggregates ─────────────────────────────────────────

class SimulationAggregate(Base):
    """
    Pre-computed statistical summary per metric per run. Immutable after write.
    Maps to: public.simulation_aggregates
    """
    __tablename__ = "simulation_aggregates"
    __table_args__ = (
        UniqueConstraint("run_id", "metric_name", name="uq_aggregate_run_metric"),
        Index("idx_aggregates_run", "run_id"),
        {"schema": "public"},
    )

    aggregate_id:  Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=FetchedValue())
    run_id:        Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("public.simulation_runs.run_id", ondelete="CASCADE"), nullable=False)
    metric_name:   Mapped[str]       = mapped_column(String(100), nullable=False)
    mean_value:    Mapped[float]     = mapped_column(Numeric(20, 6), nullable=False)
    std_deviation: Mapped[float]     = mapped_column(Numeric(20, 6), nullable=False)
    percentile_5:  Mapped[float]     = mapped_column(Numeric(20, 6), nullable=False)
    percentile_25: Mapped[float]     = mapped_column(Numeric(20, 6), nullable=False)
    median_value:  Mapped[float]     = mapped_column(Numeric(20, 6), nullable=False)
    percentile_75: Mapped[float]     = mapped_column(Numeric(20, 6), nullable=False)
    percentile_95: Mapped[float]     = mapped_column(Numeric(20, 6), nullable=False)
    min_value:     Mapped[float]     = mapped_column(Numeric(20, 6), nullable=False)
    max_value:     Mapped[float]     = mapped_column(Numeric(20, 6), nullable=False)
    var_95:        Mapped[float]     = mapped_column(Numeric(20, 6), nullable=False)
    cvar_95:       Mapped[float]     = mapped_column(Numeric(20, 6), nullable=False)
    skewness:      Mapped[Optional[float]] = mapped_column(Numeric(10, 6))
    kurtosis:      Mapped[Optional[float]] = mapped_column(Numeric(10, 6))
    created_at:    Mapped[datetime]  = mapped_column(DateTime(timezone=True), nullable=False, server_default=FetchedValue())
    # No updated_at — immutable

    # Relationships
    run: Mapped["SimulationRun"] = relationship("SimulationRun", back_populates="aggregates")

    def __repr__(self) -> str:
        return f"<SimulationAggregate run={self.run_id} metric={self.metric_name!r} mean={self.mean_value:.2f}>"


# ─── Model 11: vulnerability_assessments ─────────────────────────────────────

class VulnerabilityAssessment(Base):
    """
    Post-simulation vulnerability score per node or link. Immutable after write.
    Maps to: public.vulnerability_assessments
    """
    __tablename__ = "vulnerability_assessments"
    __table_args__ = (
        CheckConstraint(
            "(node_id IS NOT NULL AND link_id IS NULL) OR (node_id IS NULL AND link_id IS NOT NULL)",
            name="va_target_xor",
        ),
        CheckConstraint("vulnerability_score BETWEEN 0 AND 1", name="va_score_range"),
        CheckConstraint("criticality_rank > 0",                name="va_rank_positive"),
        CheckConstraint("bottleneck_score BETWEEN 0 AND 1",    name="va_bottleneck_range"),
        Index("idx_va_run",  "run_id"),
        Index("idx_va_node", "node_id"),
        Index("idx_va_link", "link_id"),
        Index("idx_va_rank", "run_id", "criticality_rank"),
        {"schema": "public"},
    )

    assessment_id:          Mapped[uuid.UUID]        = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=FetchedValue())
    run_id:                 Mapped[uuid.UUID]        = mapped_column(PG_UUID(as_uuid=True), ForeignKey("public.simulation_runs.run_id", ondelete="CASCADE"), nullable=False)
    node_id:                Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("public.supply_chain_nodes.node_id", ondelete="CASCADE"))
    link_id:                Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("public.supply_chain_links.link_id", ondelete="CASCADE"))
    vulnerability_score:    Mapped[float]            = mapped_column(Numeric(5, 4), nullable=False)
    criticality_rank:       Mapped[int]              = mapped_column(Integer, nullable=False)
    failure_frequency:      Mapped[float]            = mapped_column(Numeric(8, 4), nullable=False, server_default="0")
    avg_impact_cost_usd:    Mapped[float]            = mapped_column(Numeric(18, 2), nullable=False, server_default="0")
    avg_impact_delay_days:  Mapped[float]            = mapped_column(Numeric(10, 4), nullable=False, server_default="0")
    bottleneck_score:       Mapped[float]            = mapped_column(Numeric(5, 4), nullable=False, server_default="0")
    betweenness_centrality: Mapped[Optional[float]]  = mapped_column(Numeric(8, 6))
    degree_centrality:      Mapped[Optional[float]]  = mapped_column(Numeric(8, 6))
    closeness_centrality:   Mapped[Optional[float]]  = mapped_column(Numeric(8, 6))
    created_at:             Mapped[datetime]         = mapped_column(DateTime(timezone=True), nullable=False, server_default=FetchedValue())
    # No updated_at — immutable

    # Relationships
    run:  Mapped["SimulationRun"]              = relationship("SimulationRun", back_populates="vulnerability_assessments")
    node: Mapped[Optional["SupplyChainNode"]]  = relationship("SupplyChainNode", back_populates="vulnerability_assessments")
    link: Mapped[Optional["SupplyChainLink"]]  = relationship("SupplyChainLink", back_populates="vulnerability_assessments")

    def __repr__(self) -> str:
        target = f"node={self.node_id}" if self.node_id else f"link={self.link_id}"
        return f"<VulnerabilityAssessment {target} score={self.vulnerability_score:.3f} rank=#{self.criticality_rank}>"


# ─── Model 12: mitigation_strategies ─────────────────────────────────────────

class MitigationStrategy(Base):
    """
    Risk mitigation interventions catalogue.
    Maps to: public.mitigation_strategies
    """
    __tablename__ = "mitigation_strategies"
    __table_args__ = (
        UniqueConstraint("strategy_name", name="uq_strategy_name"),
        CheckConstraint("implementation_cost_usd >= 0",          name="ms_cost_nonneg"),
        CheckConstraint("effectiveness_score BETWEEN 0 AND 1",   name="ms_effectiveness_range"),
        CheckConstraint("reduces_probability_by BETWEEN 0 AND 1", name="ms_prob_reduction_range"),
        CheckConstraint("reduces_severity_by BETWEEN 0 AND 1",   name="ms_severity_reduction_range"),
        CheckConstraint("feasibility_score BETWEEN 0 AND 1",     name="ms_feasibility_range"),
        Index("idx_mitigation_disruption", "target_disruption_type_id"),
        {"schema": "public"},
    )

    strategy_id:                  Mapped[uuid.UUID]        = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=FetchedValue())
    strategy_name:                Mapped[str]              = mapped_column(String(255), nullable=False)
    description:                  Mapped[str]              = mapped_column(Text, nullable=False)
    target_disruption_type_id:    Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("public.disruption_types.disruption_type_id", ondelete="SET NULL"))
    applicable_node_types:        Mapped[dict]             = mapped_column(JSONB, nullable=False, server_default="[]")
    applicable_link_types:        Mapped[dict]             = mapped_column(JSONB, nullable=False, server_default="[]")
    implementation_cost_usd:      Mapped[float]            = mapped_column(Numeric(18, 2), nullable=False)
    annual_maintenance_cost_usd:  Mapped[float]            = mapped_column(Numeric(14, 2), nullable=False, server_default="0")
    effectiveness_score:          Mapped[float]            = mapped_column(Numeric(5, 4), nullable=False)
    reduces_probability_by:       Mapped[float]            = mapped_column(Numeric(5, 4), nullable=False, server_default="0")
    reduces_severity_by:          Mapped[float]            = mapped_column(Numeric(5, 4), nullable=False, server_default="0")
    reduces_recovery_time_by_pct: Mapped[float]            = mapped_column(Numeric(5, 4), nullable=False, server_default="0")
    feasibility_score:            Mapped[float]            = mapped_column(Numeric(5, 4), nullable=False, server_default="1.0")
    implementation_time_days:     Mapped[Optional[int]]    = mapped_column(Integer, server_default="0")
    metadata:                     Mapped[dict]             = mapped_column(JSONB, nullable=False, server_default="{}")
    created_at:                   Mapped[datetime]         = mapped_column(DateTime(timezone=True), nullable=False, server_default=FetchedValue())
    updated_at:                   Mapped[datetime]         = mapped_column(DateTime(timezone=True), nullable=False, server_default=FetchedValue())

    # Relationships
    target_disruption_type: Mapped[Optional["DisruptionType"]] = relationship("DisruptionType", back_populates="mitigation_strategies")

    def __repr__(self) -> str:
        return f"<MitigationStrategy {self.strategy_name!r} effectiveness={self.effectiveness_score:.2f}>"


# ─── Model 13: user_profiles ──────────────────────────────────────────────────

class UserProfile(Base):
    """
    Extended user profile linked 1:1 to auth.users.
    Maps to: public.user_profiles
    """
    __tablename__ = "user_profiles"
    __table_args__ = (
        CheckConstraint("api_calls_today >= 0",  name="profile_calls_nonneg"),
        CheckConstraint("daily_api_limit >= 0",  name="profile_limit_nonneg"),
        Index("idx_profiles_role",   "role"),
        Index("idx_profiles_active", "last_active"),
        {"schema": "public"},
    )

    profile_id:           Mapped[uuid.UUID]      = mapped_column(PG_UUID(as_uuid=True), ForeignKey("auth.users.id", ondelete="CASCADE"), primary_key=True)
    full_name:            Mapped[str]            = mapped_column(String(255), nullable=False)
    organization:         Mapped[Optional[str]]  = mapped_column(String(255))
    job_title:            Mapped[Optional[str]]  = mapped_column(String(255))
    role:                 Mapped[UserRoleEnum]   = mapped_column(SA_UserRoleEnum, nullable=False, server_default="viewer")
    api_calls_today:      Mapped[int]            = mapped_column(Integer, nullable=False, server_default="0")
    api_calls_reset_at:   Mapped[datetime]       = mapped_column(DateTime(timezone=True), nullable=False, server_default=FetchedValue())
    daily_api_limit:      Mapped[int]            = mapped_column(Integer, nullable=False, server_default="100")
    last_active:          Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    total_simulations_run: Mapped[int]           = mapped_column(Integer, nullable=False, server_default="0")
    preferences:          Mapped[dict]           = mapped_column(JSONB, nullable=False, server_default="{}")
    created_at:           Mapped[datetime]       = mapped_column(DateTime(timezone=True), nullable=False, server_default=FetchedValue())
    updated_at:           Mapped[datetime]       = mapped_column(DateTime(timezone=True), nullable=False, server_default=FetchedValue())

    def __repr__(self) -> str:
        return f"<UserProfile {self.profile_id} [{self.role.value}] {self.full_name!r}>"


# ─── Model 14: audit_logs ─────────────────────────────────────────────────────

class AuditLog(Base):
    """
    Immutable append-only audit trail.
    Maps to: public.audit_logs
    NOTE: No updated_at — logs are never updated. performed_at is the timestamp.
    """
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("idx_audit_user",      "user_id"),
        Index("idx_audit_table",     "table_name"),
        Index("idx_audit_performed", "performed_at"),
        Index("idx_audit_action",    "action"),
        {"schema": "public"},
    )

    log_id:       Mapped[uuid.UUID]        = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=FetchedValue())
    user_id:      Mapped[uuid.UUID]        = mapped_column(PG_UUID(as_uuid=True), ForeignKey("auth.users.id", ondelete="RESTRICT"), nullable=False)
    action:       Mapped[str]              = mapped_column(String(50), nullable=False)
    table_name:   Mapped[Optional[str]]    = mapped_column(String(100))
    record_id:    Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True))
    old_values:   Mapped[Optional[dict]]   = mapped_column(JSONB)
    new_values:   Mapped[Optional[dict]]   = mapped_column(JSONB)
    ip_address:   Mapped[Optional[Any]]    = mapped_column(INET)
    user_agent:   Mapped[Optional[str]]    = mapped_column(Text)
    session_id:   Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True))
    performed_at: Mapped[datetime]         = mapped_column(DateTime(timezone=True), nullable=False, server_default=FetchedValue())
    # No updated_at — append-only

    def __repr__(self) -> str:
        return f"<AuditLog user={self.user_id} action={self.action!r} table={self.table_name!r} at={self.performed_at}>"
