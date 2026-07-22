"""
app/api/v1/results.py
======================
Simulation results retrieval endpoints.

All endpoints require that the run belongs to the requesting user
or the scenario is public (enforced by RLS on simulation_results).
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Query

from app.dependencies import CurrentUser, ResultRepo
from app.schemas.simulation import (
    AggregateMetricResponse,
    ComparisonResponse,
    IterationResultResponse,
    SimulationResultsPage,
    VulnerabilityResponse,
)

router = APIRouter(prefix="/results", tags=["Simulation Results"])


@router.get(
    "/{run_id}/aggregates",
    response_model=list[AggregateMetricResponse],
    summary="Get pre-computed statistical aggregates for a run",
)
async def get_aggregates(
    run_id: uuid.UUID,
    _user: CurrentUser,
    repo: ResultRepo,
) -> list[AggregateMetricResponse]:
    """
    Return statistical summaries (mean, std, percentiles, VaR95, CVaR95,
    skewness, kurtosis) for each metric across all iterations.

    This is the primary data source for dashboard charts.
    """
    return await repo.get_aggregates(run_id)


@router.get(
    "/{run_id}/iterations",
    response_model=SimulationResultsPage,
    summary="Get paginated per-iteration results",
)
async def get_iteration_results(
    run_id: uuid.UUID,
    _user: CurrentUser,
    repo: ResultRepo,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> SimulationResultsPage:
    """
    Return raw per-iteration data for custom analysis or export.

    For 10,000-iteration runs this table has 10,000 rows.
    Always paginate — do not fetch all rows in a single request.
    """
    return await repo.get_iteration_results(run_id, limit=limit, offset=offset)


@router.get(
    "/{run_id}/vulnerability",
    response_model=list[VulnerabilityResponse],
    summary="Get vulnerability rankings for all nodes and links",
)
async def get_vulnerability_assessments(
    run_id: uuid.UUID,
    _user: CurrentUser,
    repo: ResultRepo,
) -> list[VulnerabilityResponse]:
    """
    Return vulnerability scores ranked by criticality.

    Rank 1 = most vulnerable entity in the network.
    Combines failure frequency, cost impact, bottleneck score,
    and network centrality measures.
    """
    return await repo.get_vulnerability_assessments(run_id)


@router.get(
    "/{run_id}/worst-cases",
    response_model=list[IterationResultResponse],
    summary="Get the N worst-case iterations by total cost",
)
async def get_worst_cases(
    run_id: uuid.UUID,
    _user: CurrentUser,
    repo: ResultRepo,
    n: int = Query(default=10, ge=1, le=100),
) -> list[IterationResultResponse]:
    """
    Return the N iterations with the highest total cost (tail risk scenarios).
    Useful for stress-testing and CVaR analysis.
    """
    return await repo.get_worst_case_iterations(run_id, n=n)


@router.get(
    "/{run_id}/best-cases",
    response_model=list[IterationResultResponse],
    summary="Get the N best-case iterations by total cost",
)
async def get_best_cases(
    run_id: uuid.UUID,
    _user: CurrentUser,
    repo: ResultRepo,
    n: int = Query(default=10, ge=1, le=100),
) -> list[IterationResultResponse]:
    """Return the N iterations with the lowest total cost (near-baseline scenarios)."""
    return await repo.get_best_case_iterations(run_id, n=n)


@router.get(
    "/compare/{run_id_1}/{run_id_2}",
    response_model=ComparisonResponse,
    summary="Compare aggregate statistics between two runs",
)
async def compare_runs(
    run_id_1: uuid.UUID,
    run_id_2: uuid.UUID,
    _user: CurrentUser,
    repo: ResultRepo,
) -> ComparisonResponse:
    """
    Side-by-side comparison of two simulation runs.

    Returns delta_abs and delta_pct for every metric, enabling
    before/after analysis (e.g., with vs. without a mitigation strategy).
    """
    return await repo.compare_runs(run_id_1, run_id_2)
