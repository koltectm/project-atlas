"""app/api/v1/disruptions.py — Disruption types catalogue endpoints."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query
from sqlalchemy import select

from app.db.models import DisruptionType, DisruptionCategoryEnum
from app.dependencies import CurrentUser, DbSession
from app.schemas.scenario import DisruptionTypeResponse

router = APIRouter(prefix="/disruptions", tags=["Disruption Types"])


@router.get(
    "",
    response_model=list[DisruptionTypeResponse],
    summary="List all disruption types",
)
async def list_disruption_types(
    _user: CurrentUser,
    db: DbSession,
    category: Optional[DisruptionCategoryEnum] = Query(
        default=None,
        description="Filter by disruption category (e.g. infrastructure, geopolitical)",
    ),
) -> list[DisruptionTypeResponse]:
    """
    Return the full parameterised catalogue of disruption types.

    Each entry contains the triangular distribution parameters (min/mode/max)
    used by the Monte Carlo engine for duration and severity sampling.
    """
    q = select(DisruptionType)
    if category:
        q = q.where(DisruptionType.category == category)
    q = q.order_by(DisruptionType.category, DisruptionType.name)
    rows = (await db.execute(q)).scalars().all()
    return [DisruptionTypeResponse.model_validate(r) for r in rows]


@router.get(
    "/{disruption_type_id}",
    response_model=DisruptionTypeResponse,
    summary="Get a disruption type by ID",
)
async def get_disruption_type(
    disruption_type_id: str,
    _user: CurrentUser,
    db: DbSession,
) -> DisruptionTypeResponse:
    import uuid as _uuid
    from app.core.exceptions import NotFoundError

    row = (await db.execute(
        select(DisruptionType).where(
            DisruptionType.disruption_type_id == _uuid.UUID(disruption_type_id)
        )
    )).scalar_one_or_none()
    if row is None:
        raise NotFoundError(message=f"Disruption type {disruption_type_id!r} not found.")
    return DisruptionTypeResponse.model_validate(row)
