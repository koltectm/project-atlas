"""
app/api/v1/simulation.py
=========================
Simulation trigger, status polling, and run management endpoints.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter

from app.core.exceptions import SimulationAlreadyRunningError
from app.db.models import SimulationRunStatusEnum
from app.dependencies import (
    AnalystRequired,
    CurrentUser,
    CurrentUserId,
    ScenarioRepo,
    SimulationRepo,
)
from app.schemas.simulation import SimulationRunCreate, SimulationRunResponse

router = APIRouter(prefix="/simulations", tags=["Simulations"])


@router.post(
    "/run",
    response_model=SimulationRunResponse,
    status_code=202,
    dependencies=[AnalystRequired],
    summary="Trigger a Monte Carlo simulation run for a scenario",
)
async def trigger_simulation(
    body: SimulationRunCreate,
    user_id: CurrentUserId,
    sim_repo: SimulationRepo,
    scenario_repo: ScenarioRepo,
) -> SimulationRunResponse:
    """
    Queue a new simulation run for the specified scenario.

    **Returns 202 Accepted** immediately — the simulation runs asynchronously
    via Celery. Poll `GET /simulations/{run_id}` for status updates.

    The response body contains the `run_id` needed for all subsequent queries.

    **Rate limit:** RATE_LIMIT_SIMULATION_PER_HOUR runs per user per hour.

    **Idempotency:** Returns 409 if a run for this scenario is already queued
    or running (prevents duplicate expensive jobs).
    """
    # Guard against duplicate runs
    existing_runs = await sim_repo.get_runs_for_scenario(body.scenario_id)
    in_progress = [
        r for r in existing_runs
        if r.status in (SimulationRunStatusEnum.queued, SimulationRunStatusEnum.running)
    ]
    if in_progress:
        raise SimulationAlreadyRunningError(
            detail={"active_run_id": str(in_progress[0].run_id)}
        )

    # Create the run row (status=queued)
    run = await sim_repo.create_run(
        scenario_id=body.scenario_id, user_id=user_id
    )

    # Dispatch Celery task (non-blocking)
    from app.workers.simulation_worker import run_simulation_async
    run_simulation_async(str(run.run_id))

    return run


@router.get(
    "/{run_id}",
    response_model=SimulationRunResponse,
    summary="Get simulation run status and metadata",
)
async def get_run_status(
    run_id: uuid.UUID,
    _user: CurrentUser,
    repo: SimulationRepo,
) -> SimulationRunResponse:
    """
    Poll this endpoint to track simulation progress.

    `completed_iterations / total_iterations × 100` gives the progress %.
    Status transitions: queued → running → completed | failed.
    """
    return await repo.get_run(run_id)


@router.get(
    "/scenario/{scenario_id}",
    response_model=list[SimulationRunResponse],
    summary="List all runs for a scenario",
)
async def list_runs_for_scenario(
    scenario_id: uuid.UUID,
    _user: CurrentUser,
    repo: SimulationRepo,
) -> list[SimulationRunResponse]:
    """Return all historical simulation runs for a scenario, newest first."""
    return await repo.get_runs_for_scenario(scenario_id)
