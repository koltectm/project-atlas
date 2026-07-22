"""
app/api/v1/nodes.py
====================
Supply chain nodes REST endpoints.

Access control (enforced at RLS layer + dependency layer):
    GET  endpoints — all authenticated users
    POST / PATCH / DELETE — admin only
"""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Query

from app.core.exceptions import ValidationError
from app.db.models import GeopoliticalZoneEnum, NodeStatusEnum, NodeTypeEnum, StageEnum
from app.dependencies import (
    AdminRequired,
    CurrentUser,
    NodeRepo,
)
from app.schemas.node import (
    NodeCreate,
    NodeListResponse,
    NodeResponse,
    NodeUpdate,
)

router = APIRouter(prefix="/nodes", tags=["Supply Chain Nodes"])


@router.get(
    "",
    response_model=NodeListResponse,
    summary="List supply chain nodes with optional filters",
)
async def list_nodes(
    _user: CurrentUser,
    repo: NodeRepo,
    stage: Optional[StageEnum] = Query(default=None, description="Filter by supply chain stage"),
    node_type: Optional[NodeTypeEnum] = Query(default=None, description="Filter by node type"),
    status: Optional[NodeStatusEnum] = Query(default=None, description="Filter by operational status"),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> NodeListResponse:
    """
    Return a paginated list of supply chain nodes.

    Supports filtering by stage (upstream/midstream/downstream),
    node_type (wellhead, refinery, etc.), and status.
    """
    return await repo.get_all(
        stage=stage,
        node_type=node_type,
        status=status,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/critical",
    response_model=list[NodeResponse],
    summary="List nodes above a criticality threshold",
)
async def list_critical_nodes(
    _user: CurrentUser,
    repo: NodeRepo,
    threshold: float = Query(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum criticality_score to include (0.0–1.0)",
    ),
) -> list[NodeResponse]:
    """Return nodes whose criticality_score ≥ threshold, sorted descending."""
    return await repo.get_critical_nodes(threshold=threshold)


@router.get(
    "/zone/{zone}",
    response_model=list[NodeResponse],
    summary="Get nodes by Nigerian geopolitical zone",
)
async def list_nodes_by_zone(
    zone: GeopoliticalZoneEnum,
    _user: CurrentUser,
    repo: NodeRepo,
) -> list[NodeResponse]:
    """
    Return all nodes in the specified geopolitical zone.

    Zones: SW (South-West), SE (South-East), SS (South-South / Niger Delta),
    NW (North-West), NE (North-East), NC (North-Central).
    """
    return await repo.get_by_geopolitical_zone(zone)


@router.get(
    "/graph",
    response_model=dict,
    summary="Get minimal node + link data for NetworkX graph construction",
)
async def get_graph_data(
    _user: CurrentUser,
    repo: NodeRepo,
) -> dict:
    """
    Returns nodes formatted for NetworkX graph loading.
    Used internally by the simulation engine and by the frontend's
    network visualisation component.
    """
    return await repo.get_network_graph_data()


@router.get(
    "/{node_id}",
    response_model=NodeResponse,
    summary="Get a single supply chain node by ID",
)
async def get_node(
    node_id: uuid.UUID,
    _user: CurrentUser,
    repo: NodeRepo,
) -> NodeResponse:
    return await repo.get_by_id(node_id)


@router.patch(
    "/{node_id}/status",
    response_model=NodeResponse,
    dependencies=[AdminRequired],
    summary="Update node operational status (admin only)",
)
async def update_node_status(
    node_id: uuid.UUID,
    status: NodeStatusEnum,
    _user: CurrentUser,
    repo: NodeRepo,
) -> NodeResponse:
    """
    Set a node's operational status to operational, degraded, or offline.

    Offline nodes are excluded from the network graph and all future
    simulation runs until restored.
    """
    return await repo.update_status(node_id, status)
