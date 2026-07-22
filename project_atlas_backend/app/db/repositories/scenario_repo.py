"""app/db/repositories/scenario_repo.py — Scenario CRUD."""
from __future__ import annotations
import uuid
from typing import Optional
import structlog
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Scenario, ScenarioDisruption, ScenarioStatusEnum
from app.schemas.scenario import (
    ScenarioCreate, ScenarioResponse, ScenarioListResponse,
    ScenarioDisruptionCreate, ScenarioDisruptionResponse, ScenarioUpdate,
)
from app.core.exceptions import ScenarioNotFoundError, PermissionDeniedError

logger = structlog.get_logger(__name__)


class ScenarioRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, data: ScenarioCreate, user_id: uuid.UUID) -> ScenarioResponse:
        scenario = Scenario(
            scenario_name=data.scenario_name,
            description=data.description,
            created_by=user_id,
            is_public=data.is_public,
            simulation_iterations=data.simulation_iterations,
            time_horizon_days=data.time_horizon_days,
            random_seed=data.random_seed,
            status=ScenarioStatusEnum.draft,
            tags=data.tags,
        )
        self.db.add(scenario)
        await self.db.flush()  # flush to get scenario_id

        for d in data.disruptions:
            sd = ScenarioDisruption(
                scenario_id=scenario.scenario_id,
                disruption_type_id=d.disruption_type_id,
                target_node_id=d.target_node_id,
                target_link_id=d.target_link_id,
                probability_override=d.probability_override,
                severity_override=d.severity_override,
                duration_days_override=d.duration_days_override,
                simultaneous_with=d.simultaneous_with,
                is_active=d.is_active,
            )
            self.db.add(sd)

        await self.db.flush()
        await self.db.refresh(scenario)
        logger.info("scenario_repo.created", scenario_id=str(scenario.scenario_id))
        return await self.get_by_id(scenario.scenario_id)

    async def get_by_id(self, scenario_id: uuid.UUID) -> ScenarioResponse:
        row = (await self.db.execute(
            select(Scenario)
            .options(selectinload(Scenario.disruptions))
            .where(Scenario.scenario_id == scenario_id)
        )).scalar_one_or_none()
        if row is None:
            raise ScenarioNotFoundError(detail={"scenario_id": str(scenario_id)})
        return ScenarioResponse.model_validate(row)

    async def get_user_scenarios(
        self, user_id: uuid.UUID, limit: int = 20, offset: int = 0
    ) -> ScenarioListResponse:
        total = (await self.db.execute(
            select(func.count()).select_from(Scenario)
            .where(Scenario.created_by == user_id)
        )).scalar_one()
        rows = (await self.db.execute(
            select(Scenario)
            .options(selectinload(Scenario.disruptions))
            .where(Scenario.created_by == user_id)
            .order_by(Scenario.created_at.desc())
            .offset(offset).limit(limit)
        )).scalars().all()
        return ScenarioListResponse(
            items=[ScenarioResponse.model_validate(r) for r in rows],
            total=total, limit=limit, offset=offset,
        )

    async def get_public_scenarios(
        self, limit: int = 20, offset: int = 0
    ) -> ScenarioListResponse:
        total = (await self.db.execute(
            select(func.count()).select_from(Scenario)
            .where(Scenario.is_public == True)
        )).scalar_one()
        rows = (await self.db.execute(
            select(Scenario)
            .options(selectinload(Scenario.disruptions))
            .where(Scenario.is_public == True)
            .order_by(Scenario.updated_at.desc())
            .offset(offset).limit(limit)
        )).scalars().all()
        return ScenarioListResponse(
            items=[ScenarioResponse.model_validate(r) for r in rows],
            total=total, limit=limit, offset=offset,
        )

    async def update(
        self, scenario_id: uuid.UUID, data: ScenarioUpdate, user_id: uuid.UUID
    ) -> ScenarioResponse:
        row = (await self.db.execute(
            select(Scenario).where(Scenario.scenario_id == scenario_id)
        )).scalar_one_or_none()
        if row is None:
            raise ScenarioNotFoundError()
        if row.created_by != user_id:
            raise PermissionDeniedError(message="You can only update your own scenarios.")
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(row, field, value)
        row.version += 1
        await self.db.flush()
        return await self.get_by_id(scenario_id)

    async def delete(self, scenario_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        row = (await self.db.execute(
            select(Scenario).where(Scenario.scenario_id == scenario_id)
        )).scalar_one_or_none()
        if row is None:
            raise ScenarioNotFoundError()
        if row.created_by != user_id:
            raise PermissionDeniedError(message="You can only delete your own scenarios.")
        await self.db.delete(row)
        await self.db.flush()
        logger.info("scenario_repo.deleted", scenario_id=str(scenario_id))
        return True

    async def add_disruption(
        self, scenario_id: uuid.UUID, data: ScenarioDisruptionCreate
    ) -> ScenarioDisruptionResponse:
        sd = ScenarioDisruption(
            scenario_id=scenario_id,
            disruption_type_id=data.disruption_type_id,
            target_node_id=data.target_node_id,
            target_link_id=data.target_link_id,
            probability_override=data.probability_override,
            severity_override=data.severity_override,
            duration_days_override=data.duration_days_override,
            simultaneous_with=data.simultaneous_with,
            is_active=data.is_active,
        )
        self.db.add(sd)
        await self.db.flush()
        await self.db.refresh(sd)
        return ScenarioDisruptionResponse.model_validate(sd)
