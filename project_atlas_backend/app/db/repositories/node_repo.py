"""
app/db/repositories/node_repo.py
==================================
Data access layer for supply chain nodes.
All methods use SQLAlchemy 2.0 async ORM — no raw SQL.
"""
from __future__ import annotations
import uuid
from typing import Optional
import structlog
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import SupplyChainNode, NodeTypeEnum, StageEnum, NodeStatusEnum, GeopoliticalZoneEnum
from app.schemas.node import NodeResponse, NodeListResponse, NodeGraphData, NodeUpdate
from app.core.exceptions import NodeNotFoundError

logger = structlog.get_logger(__name__)


class NodeRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, node_id: uuid.UUID) -> NodeResponse:
        result = await self.db.execute(
            select(SupplyChainNode).where(SupplyChainNode.node_id == node_id)
        )
        node = result.scalar_one_or_none()
        if node is None:
            raise NodeNotFoundError(detail={"node_id": str(node_id)})
        logger.debug("node_repo.get_by_id", node_id=str(node_id))
        return NodeResponse.model_validate(node)

    async def get_all(
        self,
        stage: Optional[StageEnum] = None,
        node_type: Optional[NodeTypeEnum] = None,
        status: Optional[NodeStatusEnum] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> NodeListResponse:
        filters = []
        if stage:
            filters.append(SupplyChainNode.stage == stage)
        if node_type:
            filters.append(SupplyChainNode.node_type == node_type)
        if status:
            filters.append(SupplyChainNode.status == status)

        count_q = select(func.count()).select_from(SupplyChainNode)
        data_q  = select(SupplyChainNode)
        if filters:
            count_q = count_q.where(and_(*filters))
            data_q  = data_q.where(and_(*filters))

        total    = (await self.db.execute(count_q)).scalar_one()
        rows     = (await self.db.execute(data_q.offset(offset).limit(limit))).scalars().all()
        items    = [NodeResponse.model_validate(r) for r in rows]

        logger.debug("node_repo.get_all", total=total, returned=len(items))
        return NodeListResponse(items=items, total=total, limit=limit, offset=offset)

    async def get_by_geopolitical_zone(
        self, zone: GeopoliticalZoneEnum
    ) -> list[NodeResponse]:
        rows = (await self.db.execute(
            select(SupplyChainNode).where(SupplyChainNode.geopolitical_zone == zone)
        )).scalars().all()
        return [NodeResponse.model_validate(r) for r in rows]

    async def get_critical_nodes(self, threshold: float = 0.7) -> list[NodeResponse]:
        rows = (await self.db.execute(
            select(SupplyChainNode)
            .where(SupplyChainNode.criticality_score >= threshold)
            .order_by(SupplyChainNode.criticality_score.desc())
        )).scalars().all()
        return [NodeResponse.model_validate(r) for r in rows]

    async def update_status(
        self, node_id: uuid.UUID, status: NodeStatusEnum
    ) -> NodeResponse:
        node = (await self.db.execute(
            select(SupplyChainNode).where(SupplyChainNode.node_id == node_id)
        )).scalar_one_or_none()
        if node is None:
            raise NodeNotFoundError(detail={"node_id": str(node_id)})
        node.status = status
        await self.db.flush()
        logger.info("node_repo.status_updated", node_id=str(node_id), status=status.value)
        return NodeResponse.model_validate(node)

    async def get_network_graph_data(self) -> dict:
        """Return minimal node data for NetworkX graph construction."""
        rows = (await self.db.execute(
            select(SupplyChainNode).where(
                SupplyChainNode.status != NodeStatusEnum.offline
            )
        )).scalars().all()
        nodes = [NodeGraphData.model_validate(r).model_dump() for r in rows]
        # Serialise UUIDs to strings for NetworkX compatibility
        for n in nodes:
            n["node_id"] = str(n["node_id"])
        logger.info("node_repo.graph_data_fetched", n_nodes=len(nodes))
        return {"nodes": nodes}
