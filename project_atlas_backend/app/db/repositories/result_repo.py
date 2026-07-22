"""app/db/repositories/result_repo.py — Results, aggregates, vulnerability queries."""
from __future__ import annotations
import uuid
from typing import Optional
import structlog
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import (
    SimulationResult, SimulationAggregate, VulnerabilityAssessment
)
from app.schemas.simulation import (
    AggregateMetricResponse, IterationResultResponse,
    VulnerabilityResponse, SimulationResultsPage, ComparisonResponse,
)
from app.core.exceptions import SimulationRunNotFoundError

logger = structlog.get_logger(__name__)


class ResultRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_aggregates(self, run_id: uuid.UUID) -> list[AggregateMetricResponse]:
        rows = (await self.db.execute(
            select(SimulationAggregate)
            .where(SimulationAggregate.run_id == run_id)
            .order_by(SimulationAggregate.metric_name)
        )).scalars().all()
        return [AggregateMetricResponse.model_validate(r) for r in rows]

    async def get_iteration_results(
        self, run_id: uuid.UUID, limit: int = 100, offset: int = 0
    ) -> SimulationResultsPage:
        total = (await self.db.execute(
            select(func.count()).select_from(SimulationResult)
            .where(SimulationResult.run_id == run_id)
        )).scalar_one()
        rows = (await self.db.execute(
            select(SimulationResult)
            .where(SimulationResult.run_id == run_id)
            .order_by(SimulationResult.iteration_number)
            .offset(offset).limit(limit)
        )).scalars().all()
        return SimulationResultsPage(
            items=[IterationResultResponse.model_validate(r) for r in rows],
            total=total, limit=limit, offset=offset,
        )

    async def get_vulnerability_assessments(
        self, run_id: uuid.UUID
    ) -> list[VulnerabilityResponse]:
        rows = (await self.db.execute(
            select(VulnerabilityAssessment)
            .where(VulnerabilityAssessment.run_id == run_id)
            .order_by(VulnerabilityAssessment.criticality_rank)
        )).scalars().all()
        return [VulnerabilityResponse.model_validate(r) for r in rows]

    async def get_worst_case_iterations(
        self, run_id: uuid.UUID, n: int = 10
    ) -> list[IterationResultResponse]:
        rows = (await self.db.execute(
            select(SimulationResult)
            .where(SimulationResult.run_id == run_id)
            .order_by(SimulationResult.total_cost_usd.desc())
            .limit(n)
        )).scalars().all()
        return [IterationResultResponse.model_validate(r) for r in rows]

    async def get_best_case_iterations(
        self, run_id: uuid.UUID, n: int = 10
    ) -> list[IterationResultResponse]:
        rows = (await self.db.execute(
            select(SimulationResult)
            .where(SimulationResult.run_id == run_id)
            .order_by(SimulationResult.total_cost_usd.asc())
            .limit(n)
        )).scalars().all()
        return [IterationResultResponse.model_validate(r) for r in rows]

    async def compare_runs(
        self, run_id_1: uuid.UUID, run_id_2: uuid.UUID
    ) -> ComparisonResponse:
        """Side-by-side aggregate comparison of two runs."""
        aggs_1 = {a.metric_name: a for a in await self.get_aggregates(run_id_1)}
        aggs_2 = {a.metric_name: a for a in await self.get_aggregates(run_id_2)}
        all_metrics = set(aggs_1) | set(aggs_2)

        comparison: dict = {}
        for metric in sorted(all_metrics):
            a1 = aggs_1.get(metric)
            a2 = aggs_2.get(metric)
            m1 = a1.mean_value if a1 else 0.0
            m2 = a2.mean_value if a2 else 0.0
            delta_pct = ((m2 - m1) / m1 * 100) if m1 != 0 else 0.0
            comparison[metric] = {
                "run_1_mean":  m1,
                "run_2_mean":  m2,
                "delta_abs":   m2 - m1,
                "delta_pct":   round(delta_pct, 2),
                "run_1_var95": a1.var_95 if a1 else 0.0,
                "run_2_var95": a2.var_95 if a2 else 0.0,
            }

        return ComparisonResponse(
            run_id_1=run_id_1,
            run_id_2=run_id_2,
            metrics=comparison,
        )
