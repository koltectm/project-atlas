"""
app/api/v1/scenarios.py
========================
Scenario CRUD endpoints.

Access control:
    GET public   — unauthenticated allowed (RLS enforces is_public filter)
    GET own      — authenticated users
    POST/PATCH   — authenticated analysts + admins
    DELETE       — owner or admin
"""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Query

from app.dependencies import (
    AnalystRequired,
    CurrentUser,
    CurrentUserId,
    ScenarioRepo,
)
from app.schemas.scenario import (
    ScenarioCreate,
    ScenarioDisruptionCreate,
    ScenarioDisruptionResponse,
    ScenarioListResponse,
    ScenarioResponse,
    ScenarioUpdate,
)

router = APIRouter(prefix="/scenarios", tags=["Scenarios"])


@router.get(
    "/public",
    response_model=ScenarioListResponse,
    summary="List public scenarios (no auth required)",
)
async def list_public_scenarios(
    repo: ScenarioRepo,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> ScenarioListResponse:
    """Return paginated list of scenarios marked is_public=True."""
    return await repo.get_public_scenarios(limit=limit, offset=offset)


@router.get(
    "/mine",
    response_model=ScenarioListResponse,
    summary="List scenarios created by the current user",
)
async def list_my_scenarios(
    user_id: CurrentUserId,
    repo: ScenarioRepo,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> ScenarioListResponse:
    return await repo.get_user_scenarios(user_id=user_id, limit=limit, offset=offset)


@router.post(
    "",
    response_model=ScenarioResponse,
    status_code=201,
    dependencies=[AnalystRequired],
    summary="Create a new simulation scenario",
)
async def create_scenario(
    body: ScenarioCreate,
    user_id: CurrentUserId,
    repo: ScenarioRepo,
) -> ScenarioResponse:
    """
    Create a scenario with optional inline disruption definitions.

    Disruptions can also be added later via POST /scenarios/{id}/disruptions.
    The scenario starts in 'draft' status — trigger a run via
    POST /simulations/run to execute it.
    """
    return await repo.create(data=body, user_id=user_id)


@router.get(
    "/{scenario_id}",
    response_model=ScenarioResponse,
    summary="Get a scenario by ID",
)
async def get_scenario(
    scenario_id: uuid.UUID,
    _user: CurrentUser,
    repo: ScenarioRepo,
) -> ScenarioResponse:
    return await repo.get_by_id(scenario_id)


@router.patch(
    "/{scenario_id}",
    response_model=ScenarioResponse,
    dependencies=[AnalystRequired],
    summary="Update a scenario (owner or admin only)",
)
async def update_scenario(
    scenario_id: uuid.UUID,
    body: ScenarioUpdate,
    user_id: CurrentUserId,
    repo: ScenarioRepo,
) -> ScenarioResponse:
    return await repo.update(scenario_id=scenario_id, data=body, user_id=user_id)


@router.delete(
    "/{scenario_id}",
    status_code=204,
    summary="Delete a scenario (owner or admin only)",
)
async def delete_scenario(
    scenario_id: uuid.UUID,
    user_id: CurrentUserId,
    repo: ScenarioRepo,
) -> None:
    await repo.delete(scenario_id=scenario_id, user_id=user_id)


@router.post(
    "/{scenario_id}/disruptions",
    response_model=ScenarioDisruptionResponse,
    status_code=201,
    dependencies=[AnalystRequired],
    summary="Add a disruption to an existing scenario",
)
async def add_disruption_to_scenario(
    scenario_id: uuid.UUID,
    body: ScenarioDisruptionCreate,
    _user: CurrentUser,
    repo: ScenarioRepo,
) -> ScenarioDisruptionResponse:
    """
    Attach a disruption type (with optional parameter overrides) to a scenario.

    Target: either target_node_id OR target_link_id must be set (XOR),
    or both null for a network-wide disruption of matching node/link types.
    """
    return await repo.add_disruption(scenario_id=scenario_id, data=body)
