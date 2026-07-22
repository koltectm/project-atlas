"""app/schemas/simulation.py — Schemas for simulation runs and results."""
from __future__ import annotations
import uuid
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field, ConfigDict
from app.db.models import SimulationRunStatusEnum


class SimulationRunCreate(BaseModel):
    scenario_id: uuid.UUID


class SimulationRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    run_id:               uuid.UUID
    scenario_id:          uuid.UUID
    started_at:           datetime
    completed_at:         Optional[datetime]
    duration_seconds:     Optional[int]
    total_iterations:     int
    completed_iterations: int
    status:               SimulationRunStatusEnum
    engine_version:       Optional[str]
    error_message:        Optional[str]
    triggered_by:         uuid.UUID
    created_at:           datetime
    updated_at:           datetime

    @property
    def progress_pct(self) -> float:
        if self.total_iterations == 0:
            return 0.0
        return round(self.completed_iterations / self.total_iterations * 100, 1)


class AggregateMetricResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    aggregate_id:  uuid.UUID
    run_id:        uuid.UUID
    metric_name:   str
    mean_value:    float
    std_deviation: float
    percentile_5:  float
    percentile_25: float
    median_value:  float
    percentile_75: float
    percentile_95: float
    min_value:     float
    max_value:     float
    var_95:        float
    cvar_95:       float
    skewness:      Optional[float]
    kurtosis:      Optional[float]


class IterationResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    result_id:               uuid.UUID
    run_id:                  uuid.UUID
    iteration_number:        int
    total_cost_usd:          float
    total_delay_days:        float
    production_loss_barrels: float
    nodes_affected:          int
    links_disrupted:         int
    supply_chain_flow_pct:   float
    recovery_time_days:      float
    disruptions_triggered:   list[dict]


class VulnerabilityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    assessment_id:          uuid.UUID
    run_id:                 uuid.UUID
    node_id:                Optional[uuid.UUID]
    link_id:                Optional[uuid.UUID]
    vulnerability_score:    float
    criticality_rank:       int
    failure_frequency:      float
    avg_impact_cost_usd:    float
    avg_impact_delay_days:  float
    bottleneck_score:       float
    betweenness_centrality: Optional[float]
    degree_centrality:      Optional[float]
    closeness_centrality:   Optional[float]


class RunSummaryResponse(BaseModel):
    """High-level run summary for dashboard cards."""
    run_id:           uuid.UUID
    status:           SimulationRunStatusEnum
    total_iterations: int
    aggregates:       list[AggregateMetricResponse]
    top_vulnerabilities: list[VulnerabilityResponse]


class ComparisonResponse(BaseModel):
    """Side-by-side comparison of two simulation runs."""
    run_id_1: uuid.UUID
    run_id_2: uuid.UUID
    metrics:  dict[str, dict[str, float]]
    # e.g. {"total_cost_usd": {"run_1_mean": ..., "run_2_mean": ..., "delta_pct": ...}}


class SimulationResultsPage(BaseModel):
    items:  list[IterationResultResponse]
    total:  int
    limit:  int
    offset: int
