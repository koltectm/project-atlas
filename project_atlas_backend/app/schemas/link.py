"""app/schemas/link.py — Pydantic schemas for supply chain links."""
from __future__ import annotations
import uuid
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field, ConfigDict
from app.db.models import LinkTypeEnum, NodeStatusEnum


class LinkBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    link_name:                 str            = Field(..., max_length=255)
    link_code:                 str            = Field(..., max_length=50)
    link_type:                 LinkTypeEnum
    source_node_id:            uuid.UUID
    target_node_id:            uuid.UUID
    distance_km:               float          = Field(..., gt=0)
    diameter_inches:           Optional[float] = None
    pipeline_year_installed:   Optional[int]  = Field(default=None, ge=1900, le=2100)
    normal_lead_time_days:     float          = Field(..., gt=0)
    transport_cost_per_barrel: float          = Field(..., ge=0)
    max_capacity_bpd:          float          = Field(..., gt=0)
    current_utilization_pct:   float          = Field(default=0.0, ge=0.0, le=1.0)
    reliability_score:         float          = Field(default=0.9, ge=0.0, le=1.0)
    vandalism_risk_score:      Optional[float] = Field(default=0.0, ge=0.0, le=1.0)
    is_critical_path:          bool           = False
    alternative_routes:        list           = Field(default_factory=list)
    status:                    NodeStatusEnum = NodeStatusEnum.operational
    metadata:                  dict           = Field(default_factory=dict)


class LinkCreate(LinkBase):
    pass


class LinkUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    current_utilization_pct: Optional[float]          = Field(default=None, ge=0.0, le=1.0)
    reliability_score:       Optional[float]          = Field(default=None, ge=0.0, le=1.0)
    is_critical_path:        Optional[bool]           = None
    status:                  Optional[NodeStatusEnum] = None
    metadata:                Optional[dict]           = None


class LinkResponse(LinkBase):
    link_id:    uuid.UUID
    created_at: datetime
    updated_at: datetime


class LinkGraphData(BaseModel):
    """Minimal link data for NetworkX edge construction."""
    model_config = ConfigDict(from_attributes=True)

    link_id:                   uuid.UUID
    link_code:                 str
    link_type:                 LinkTypeEnum
    source_node_id:            uuid.UUID
    target_node_id:            uuid.UUID
    distance_km:               float
    normal_lead_time_days:     float
    transport_cost_per_barrel: float
    max_capacity_bpd:          float
    current_utilization_pct:   float
    reliability_score:         float
    vandalism_risk_score:      Optional[float]
    is_critical_path:          bool
    alternative_routes:        list
    status:                    NodeStatusEnum


class LinkListResponse(BaseModel):
    items:  list[LinkResponse]
    total:  int
    limit:  int
    offset: int
