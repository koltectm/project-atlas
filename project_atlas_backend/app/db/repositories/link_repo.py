"""app/db/repositories/link_repo.py — Data access for supply chain links."""
from __future__ import annotations
import uuid
from typing import Optional
import structlog
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import SupplyChainLink, LinkTypeEnum, NodeStatusEnum
from app.schemas.link import LinkResponse, LinkListResponse, LinkGraphData
from app.core.exceptions import LinkNotFoundError

logger = structlog.get_logger(__name__)


class LinkRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, link_id: uuid.UUID) -> LinkResponse:
        row = (await self.db.execute(
            select(SupplyChainLink).where(SupplyChainLink.link_id == link_id)
        )).scalar_one_or_none()
        if row is None:
            raise LinkNotFoundError(detail={"link_id": str(link_id)})
        return LinkResponse.model_validate(row)

    async def get_all(
        self,
        link_type: Optional[LinkTypeEnum] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> LinkListResponse:
        filters = []
        if link_type:
            filters.append(SupplyChainLink.link_type == link_type)
        count_q = select(func.count()).select_from(SupplyChainLink)
        data_q  = select(SupplyChainLink)
        if filters:
            count_q = count_q.where(and_(*filters))
            data_q  = data_q.where(and_(*filters))
        total = (await self.db.execute(count_q)).scalar_one()
        rows  = (await self.db.execute(data_q.offset(offset).limit(limit))).scalars().all()
        return LinkListResponse(
            items=[LinkResponse.model_validate(r) for r in rows],
            total=total, limit=limit, offset=offset,
        )

    async def get_by_source_node(self, node_id: uuid.UUID) -> list[LinkResponse]:
        rows = (await self.db.execute(
            select(SupplyChainLink).where(SupplyChainLink.source_node_id == node_id)
        )).scalars().all()
        return [LinkResponse.model_validate(r) for r in rows]

    async def get_by_target_node(self, node_id: uuid.UUID) -> list[LinkResponse]:
        rows = (await self.db.execute(
            select(SupplyChainLink).where(SupplyChainLink.target_node_id == node_id)
        )).scalars().all()
        return [LinkResponse.model_validate(r) for r in rows]

    async def get_critical_path_links(self) -> list[LinkResponse]:
        rows = (await self.db.execute(
            select(SupplyChainLink).where(SupplyChainLink.is_critical_path == True)
            .order_by(SupplyChainLink.reliability_score)
        )).scalars().all()
        return [LinkResponse.model_validate(r) for r in rows]

    async def get_links_for_graph(self) -> list[dict]:
        """Return minimal link data for NetworkX graph construction."""
        rows = (await self.db.execute(
            select(SupplyChainLink).where(
                SupplyChainLink.status != NodeStatusEnum.offline
            )
        )).scalars().all()
        links = [LinkGraphData.model_validate(r).model_dump() for r in rows]
        for lk in links:
            lk["link_id"]       = str(lk["link_id"])
            lk["source_node_id"] = str(lk["source_node_id"])
            lk["target_node_id"] = str(lk["target_node_id"])
        return links
