"""app/db/repositories/simulation_repo.py — Simulation run CRUD and bulk insert."""
from __future__ import annotations
import uuid
from typing import Optional
import structlog
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import SimulationRun, SimulationAggregate, SimulationRunStatusEnum
from app.schemas.simulation import SimulationRunResponse, AggregateMetricResponse
from app.core.exceptions import SimulationRunNotFoundError
from app.config import get_settings

logger = structlog.get_logger(__name__)
ENGINE_VERSION = "1.0.0"


class SimulationRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_run(
        self, scenario_id: uuid.UUID, user_id: uuid.UUID
    ) -> SimulationRunResponse:
        from app.db.repositories.scenario_repo import ScenarioRepository
        # Verify scenario exists (raises ScenarioNotFoundError if not)
        scenario = await ScenarioRepository(self.db).get_by_id(scenario_id)

        run = SimulationRun(
            scenario_id=scenario_id,
            total_iterations=scenario.simulation_iterations,
            completed_iterations=0,
            status=SimulationRunStatusEnum.queued,
            engine_version=ENGINE_VERSION,
            triggered_by=user_id,
        )
        self.db.add(run)
        await self.db.flush()
        await self.db.refresh(run)
        logger.info("simulation_repo.run_created", run_id=str(run.run_id))
        return SimulationRunResponse.model_validate(run)

    async def update_run_status(
        self,
        run_id: uuid.UUID,
        status: SimulationRunStatusEnum,
        error_msg: Optional[str] = None,
        completed_iterations: Optional[int] = None,
    ) -> SimulationRunResponse:
        row = (await self.db.execute(
            select(SimulationRun).where(SimulationRun.run_id == run_id)
        )).scalar_one_or_none()
        if row is None:
            raise SimulationRunNotFoundError()
        row.status = status
        if error_msg:
            row.error_message = error_msg
        if completed_iterations is not None:
            row.completed_iterations = completed_iterations
        if status == SimulationRunStatusEnum.completed:
            from sqlalchemy import func
            row.completed_at = (await self.db.execute(select(text("NOW()")))).scalar()
        await self.db.flush()
        return SimulationRunResponse.model_validate(row)

    async def get_run(self, run_id: uuid.UUID) -> SimulationRunResponse:
        row = (await self.db.execute(
            select(SimulationRun).where(SimulationRun.run_id == run_id)
        )).scalar_one_or_none()
        if row is None:
            raise SimulationRunNotFoundError(detail={"run_id": str(run_id)})
        return SimulationRunResponse.model_validate(row)

    async def get_runs_for_scenario(
        self, scenario_id: uuid.UUID
    ) -> list[SimulationRunResponse]:
        rows = (await self.db.execute(
            select(SimulationRun)
            .where(SimulationRun.scenario_id == scenario_id)
            .order_by(SimulationRun.started_at.desc())
        )).scalars().all()
        return [SimulationRunResponse.model_validate(r) for r in rows]

    async def bulk_insert_results(
        self, run_id: uuid.UUID, result_rows: list[dict]
    ) -> int:
        """
        Insert simulation iteration results in batches.

        Uses raw SQL INSERT for performance — ORM overhead per-row would
        make 10,000 inserts unacceptably slow (~30s vs ~1s with bulk insert).

        Returns the number of rows inserted.
        """
        if not result_rows:
            return 0

        BATCH_SIZE = 500
        total_inserted = 0

        for i in range(0, len(result_rows), BATCH_SIZE):
            batch = result_rows[i:i + BATCH_SIZE]
            import json
            values_sql = ", ".join(
                f"(gen_random_uuid(), :run_id_{j}, :iter_{j}, :cost_{j}, "
                f":delay_{j}, :loss_{j}, :nodes_{j}, :links_{j}, "
                f":flow_{j}, :recovery_{j}, :disruptions_{j}::jsonb, NOW())"
                for j in range(len(batch))
            )
            params: dict = {}
            for j, row in enumerate(batch):
                params[f"run_id_{j}"]      = str(run_id)
                params[f"iter_{j}"]        = row["iteration_number"]
                params[f"cost_{j}"]        = row["total_cost_usd"]
                params[f"delay_{j}"]       = row["total_delay_days"]
                params[f"loss_{j}"]        = row["production_loss_barrels"]
                params[f"nodes_{j}"]       = row["nodes_affected"]
                params[f"links_{j}"]       = row["links_disrupted"]
                params[f"flow_{j}"]        = row["supply_chain_flow_pct"]
                params[f"recovery_{j}"]    = row["recovery_time_days"]
                params[f"disruptions_{j}"] = json.dumps(row.get("disruptions_triggered", []))

            await self.db.execute(
                text(
                    f"""
                    INSERT INTO public.simulation_results
                        (result_id, run_id, iteration_number, total_cost_usd,
                         total_delay_days, production_loss_barrels,
                         nodes_affected, links_disrupted, supply_chain_flow_pct,
                         recovery_time_days, disruptions_triggered, created_at)
                    VALUES {values_sql}
                    """
                ),
                params,
            )
            total_inserted += len(batch)

        logger.info(
            "simulation_repo.results_inserted",
            run_id=str(run_id),
            total_rows=total_inserted,
        )
        return total_inserted

    async def save_aggregates(
        self, run_id: uuid.UUID, aggregates: list
    ) -> list[AggregateMetricResponse]:
        """Save AggregateMetrics dataclasses to simulation_aggregates table."""
        import json
        saved = []
        for agg in aggregates:
            row = SimulationAggregate(
                run_id=run_id,
                metric_name=agg.metric_name,
                mean_value=agg.mean_value,
                std_deviation=agg.std_deviation,
                percentile_5=agg.percentile_5,
                percentile_25=agg.percentile_25,
                median_value=agg.median_value,
                percentile_75=agg.percentile_75,
                percentile_95=agg.percentile_95,
                min_value=agg.min_value,
                max_value=agg.max_value,
                var_95=agg.var_95,
                cvar_95=agg.cvar_95,
                skewness=agg.skewness,
                kurtosis=agg.kurtosis,
            )
            self.db.add(row)
            saved.append(row)

        await self.db.flush()
        logger.info(
            "simulation_repo.aggregates_saved",
            run_id=str(run_id),
            n_metrics=len(saved),
        )
        return [AggregateMetricResponse.model_validate(r) for r in saved]
