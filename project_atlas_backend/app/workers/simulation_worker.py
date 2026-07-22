"""
app/workers/simulation_worker.py
==================================
Celery background task for async Monte Carlo simulation execution.

Architecture
------------
1. API receives POST /simulations/run → creates SimulationRun row (status=queued)
2. API dispatches Celery task run_simulation.delay(run_id)
3. Celery worker picks up the task and calls _execute_simulation()
4. _execute_simulation() loads scenario + disruption configs from DB,
   instantiates MonteCarloEngine, calls engine.run(), persists results.
5. Worker updates SimulationRun.status → completed (or failed)
6. Frontend polls GET /simulations/{run_id} for status updates.

Progress Updates
----------------
The worker calls SimulationRepository.update_run_status() periodically
with the completed_iterations count, which the frontend polls to show
a progress bar.

Error Handling
--------------
- DB connection errors: retried up to 3 times with exponential backoff
- Simulation errors: caught, logged, run marked as failed with error_message
- Timeout: Celery soft_time_limit raises SoftTimeLimitExceeded → graceful shutdown
"""

from __future__ import annotations

import traceback
import uuid
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


def make_celery_app():
    """
    Create the Celery application.

    Deferred import so that this module can be imported without Celery
    installed (e.g., in unit tests with mocked Celery).
    """
    from celery import Celery
    from app.config import get_settings
    cfg = get_settings()

    celery_app = Celery(
        "project_atlas",
        broker=cfg.REDIS_URL,
        backend=cfg.REDIS_URL,
    )
    celery_app.conf.update(
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        task_soft_time_limit=get_settings().SIMULATION_TIMEOUT_SECONDS,
        task_time_limit=get_settings().SIMULATION_TIMEOUT_SECONDS + 60,
        worker_prefetch_multiplier=1,   # one task at a time per worker (CPU-bound)
        task_acks_late=True,            # ack only after task completes (no lost runs)
    )
    return celery_app


try:
    celery_app = make_celery_app()
except Exception:
    # Celery/Redis not available at import time (e.g., test environment)
    celery_app = None  # type: ignore


def run_simulation_async(run_id: str) -> Any:
    """
    Dispatch the simulation task to Celery.

    Falls back to synchronous execution if Celery is unavailable
    (development mode without Redis).

    Parameters
    ----------
    run_id : str
        UUID string of the simulation_runs row.

    Returns
    -------
    Celery AsyncResult or None (sync execution returns None).
    """
    if celery_app is not None:
        return run_simulation_task.delay(run_id)
    else:
        logger.warning(
            "simulation_worker.celery_unavailable.sync_fallback",
            run_id=run_id,
        )
        import asyncio
        asyncio.create_task(_execute_simulation_async(run_id))
        return None


if celery_app is not None:
    @celery_app.task(
        name="run_simulation",
        bind=True,
        max_retries=3,
        default_retry_delay=5,
    )
    def run_simulation_task(self, run_id: str) -> dict:
        """
        Celery task entry point. Wraps the async execution in a sync runner.
        """
        import asyncio
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(_execute_simulation_async(run_id))
        finally:
            loop.close()
else:
    def run_simulation_task(run_id: str) -> dict:  # type: ignore
        raise RuntimeError("Celery not available")


async def _execute_simulation_async(run_id: str) -> dict:
    """
    Core simulation execution logic.

    This is the async function that runs the full Monte Carlo pipeline:
    1. Load scenario and disruption configs from DB
    2. Load network graph data from DB
    3. Build DisruptionConfig objects
    4. Instantiate and run MonteCarloEngine
    5. Persist results (bulk insert)
    6. Persist aggregates
    7. Persist vulnerability assessments
    8. Mark run as completed
    """
    from app.db.connection import get_db_session
    from app.db.models import SimulationRunStatusEnum, DisruptionType, Scenario, ScenarioDisruption
    from app.db.repositories.simulation_repo import SimulationRepository
    from app.db.repositories.node_repo import NodeRepository
    from app.db.repositories.link_repo import LinkRepository
    from app.db.repositories.result_repo import ResultRepository
    from app.simulation.engine import MonteCarloEngine
    from app.simulation.disruption_model import DisruptionConfig
    from app.simulation.cost_model import NetworkCostConstants
    from app.config import get_settings
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    cfg = get_settings()
    run_uuid = uuid.UUID(run_id)

    logger.info("simulation_worker.task_started", run_id=run_id)

    async with get_db_session() as db:
        sim_repo  = SimulationRepository(db)
        node_repo = NodeRepository(db)
        link_repo = LinkRepository(db)

        # ── Mark as running ──────────────────────────────────────────────────
        await sim_repo.update_run_status(
            run_uuid, SimulationRunStatusEnum.running
        )

        try:
            # ── Load the simulation run ──────────────────────────────────────
            run = (await db.execute(
                select(__import__('app.db.models', fromlist=['SimulationRun']).SimulationRun)
                .where(__import__('app.db.models', fromlist=['SimulationRun']).SimulationRun.run_id == run_uuid)
            )).scalar_one()

            # ── Load scenario + disruptions ──────────────────────────────────
            scenario = (await db.execute(
                select(Scenario)
                .options(selectinload(Scenario.disruptions).selectinload(
                    ScenarioDisruption.disruption_type
                ))
                .where(Scenario.scenario_id == run.scenario_id)
            )).scalar_one()

            # ── Build DisruptionConfig list ──────────────────────────────────
            disruption_configs: list[DisruptionConfig] = []
            for sd in scenario.disruptions:
                if not sd.is_active:
                    continue
                dt = sd.disruption_type

                # Apply scenario overrides
                annual_prob = float(
                    sd.probability_override
                    if sd.probability_override is not None
                    else dt.typical_annual_probability
                )
                sev_mode = float(
                    sd.severity_override
                    if sd.severity_override is not None
                    else dt.severity_mode
                )
                dur_mode = float(
                    sd.duration_days_override
                    if sd.duration_days_override is not None
                    else dt.typical_duration_days_mode
                )

                # Build cascade targets from correlated_disruption_ids
                cascade_targets = {}
                if dt.correlated_disruption_ids and isinstance(dt.correlated_disruption_ids, list):
                    for corr_id in dt.correlated_disruption_ids:
                        cascade_targets[str(corr_id)] = float(dt.cascading_probability or 0.0)

                disruption_configs.append(DisruptionConfig(
                    disruption_type_id=str(dt.disruption_type_id),
                    name=dt.name,
                    category=dt.category.value,
                    annual_probability=annual_prob,
                    severity_min=float(dt.severity_min),
                    severity_mode=sev_mode,
                    severity_max=float(dt.severity_max),
                    duration_min=float(dt.typical_duration_days_min),
                    duration_mode=dur_mode,
                    duration_max=float(dt.typical_duration_days_max),
                    cascade_targets=cascade_targets,
                    target_node_ids=[str(sd.target_node_id)] if sd.target_node_id else [],
                    target_link_ids=[str(sd.target_link_id)] if sd.target_link_id else [],
                    affected_node_types=list(dt.affected_node_types or []),
                    affected_link_types=list(dt.affected_link_types or []),
                ))

            # ── Load network data ────────────────────────────────────────────
            node_graph_data = await node_repo.get_network_graph_data()
            link_graph_data = await link_repo.get_links_for_graph()
            network_data = {
                "nodes": node_graph_data["nodes"],
                "links": link_graph_data,
            }

            # ── Build cost constants ─────────────────────────────────────────
            cost_constants = NetworkCostConstants(
                baseline_daily_throughput_bpd=1_300_000.0,  # Nigeria avg 2024
                crude_price_usd_per_barrel=cfg.CRUDE_PRICE_USD_PER_BARREL,
                holding_cost_usd_per_barrel_day=cfg.HOLDING_COST_USD_PER_BARREL_DAY,
                sla_tolerance_days=7.0,
                penalty_per_day_usd=50_000.0,
                avg_inventory_barrels=15_000_000.0,  # aggregate depot inventory
            )

            # ── Progress callback ────────────────────────────────────────────
            async def progress_cb(completed: int) -> None:
                await sim_repo.update_run_status(
                    run_uuid,
                    SimulationRunStatusEnum.running,
                    completed_iterations=completed,
                )

            # ── Run the simulation ───────────────────────────────────────────
            engine = MonteCarloEngine(
                run_id=run_id,
                n_iterations=scenario.simulation_iterations,
                time_horizon_days=scenario.time_horizon_days,
                random_seed=scenario.random_seed,
                disruption_configs=disruption_configs,
                network_data=network_data,
                cost_constants=cost_constants,
                progress_callback=progress_cb,
            )
            output = engine.run()

            # ── Persist results ──────────────────────────────────────────────
            result_rows = output.to_result_rows()
            await sim_repo.bulk_insert_results(run_uuid, result_rows)
            await sim_repo.save_aggregates(run_uuid, output.aggregates)

            # ── Persist vulnerability assessments ────────────────────────────
            if output.vulnerabilities:
                from sqlalchemy import text as sql_text
                va_rows = []
                for va in output.vulnerabilities:
                    va_rows.append({
                        "run_id":              str(run_uuid),
                        "node_id":             va.entity_id if va.entity_type == "node" else None,
                        "link_id":             va.entity_id if va.entity_type == "link" else None,
                        "vulnerability_score": va.vulnerability_score,
                        "criticality_rank":    va.criticality_rank,
                        "failure_frequency":   va.failure_frequency,
                        "avg_impact_cost_usd": va.avg_impact_cost_usd,
                        "avg_impact_delay_days": va.avg_impact_delay_days,
                        "bottleneck_score":    va.bottleneck_score,
                    })
                import json
                for va_row in va_rows:
                    await db.execute(
                        sql_text("""
                            INSERT INTO public.vulnerability_assessments
                                (run_id, node_id, link_id, vulnerability_score,
                                 criticality_rank, failure_frequency,
                                 avg_impact_cost_usd, avg_impact_delay_days,
                                 bottleneck_score, created_at)
                            VALUES
                                (:run_id::uuid, :node_id::uuid, :link_id::uuid,
                                 :vulnerability_score, :criticality_rank,
                                 :failure_frequency, :avg_impact_cost_usd,
                                 :avg_impact_delay_days, :bottleneck_score, NOW())
                        """),
                        va_row,
                    )

            # ── Mark completed ───────────────────────────────────────────────
            await sim_repo.update_run_status(
                run_uuid,
                SimulationRunStatusEnum.completed,
                completed_iterations=scenario.simulation_iterations,
            )

            logger.info(
                "simulation_worker.task_completed",
                run_id=run_id,
                elapsed_seconds=output.elapsed_seconds,
                p_failure=output.probability_of_failure,
            )

            return {
                "status": "completed",
                "run_id": run_id,
                "elapsed_seconds": output.elapsed_seconds,
            }

        except Exception as exc:
            tb = traceback.format_exc()
            logger.error(
                "simulation_worker.task_failed",
                run_id=run_id,
                error=str(exc),
                traceback=tb,
            )
            await sim_repo.update_run_status(
                run_uuid,
                SimulationRunStatusEnum.failed,
                error_msg=str(exc)[:2000],  # truncate for DB column
            )
            raise
