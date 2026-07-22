"""app/api/v1/links.py — Supply chain links endpoints."""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Query

from app.db.models import LinkTypeEnum
from app.dependencies import CurrentUser, LinkRepo
from app.schemas.link import LinkListResponse, LinkResponse

router = APIRouter(prefix="/links", tags=["Supply Chain Links"])


@router.get("", response_model=LinkListResponse, summary="List supply chain links")
async def list_links(
    _user: CurrentUser,
    repo: LinkRepo,
    link_type: Optional[LinkTypeEnum] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> LinkListResponse:
    return await repo.get_all(link_type=link_type, limit=limit, offset=offset)


@router.get(
    "/critical-path",
    response_model=list[LinkResponse],
    summary="Get links on the critical path",
)
async def get_critical_path_links(
    _user: CurrentUser, repo: LinkRepo
) -> list[LinkResponse]:
    """
    Return links flagged as is_critical_path=True, sorted by reliability
    ascending (least reliable first — highest risk at the top).
    """
    return await repo.get_critical_path_links()


@router.get("/{link_id}", response_model=LinkResponse, summary="Get a link by ID")
async def get_link(
    link_id: uuid.UUID, _user: CurrentUser, repo: LinkRepo
) -> LinkResponse:
    return await repo.get_by_id(link_id)


@router.get(
    "/from/{node_id}",
    response_model=list[LinkResponse],
    summary="Get all links originating from a node",
)
async def links_from_node(
    node_id: uuid.UUID, _user: CurrentUser, repo: LinkRepo
) -> list[LinkResponse]:
    return await repo.get_by_source_node(node_id)


@router.get(
    "/to/{node_id}",
    response_model=list[LinkResponse],
    summary="Get all links terminating at a node",
)
async def links_to_node(
    node_id: uuid.UUID, _user: CurrentUser, repo: LinkRepo
) -> list[LinkResponse]:
    return await repo.get_by_target_node(node_id)
