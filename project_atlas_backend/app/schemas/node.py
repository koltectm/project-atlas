"""
app/schemas/node.py
===================
Pydantic v2 schemas for supply chain nodes.
"""
from __future__ import annotations
import uuid
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict
from app.db.models import NodeTypeEnum, StageEnum, GeopoliticalZoneEnum, NodeStatusEnum


class NodeBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    node_name:               str            = Field(..., min_length=1, max_length=255)
    node_code:               str            = Field(..., min_length=1, max_length=50)
    node_type:               NodeTypeEnum
    stage:                   StageEnum
    latitude:                float          = Field(..., ge=-90.0, le=90.0)
    longitude:               float          = Field(..., ge=-180.0, le=180.0)
    state_location:          str            = Field(..., max_length=100)
    geopolitical_zone:       GeopoliticalZoneEnum
    address_description:     Optional[str]  = None
    operator:                str            = Field(..., max_length=255)
    operator_type:           Optional[str]  = None
    capacity_bpd:            float          = Field(default=0.0, ge=0)
    current_utilization_pct: float          = Field(default=0.0, ge=0.0, le=1.0)
    status:                  NodeStatusEnum = NodeStatusEnum.operational
    redundancy_score:        float          = Field(default=0.0, ge=0.0, le=1.0)
    criticality_score:       float          = Field(default=0.0, ge=0.0, le=1.0)
    mean_time_between_failures_days: Optional[float] = Field(default=None, gt=0)
    mean_time_to_repair_days:        Optional[float] = Field(default=None, gt=0)
    daily_operating_cost_usd:        Optional[float] = Field(default=None, ge=0)
    replacement_cost_usd:            Optional[float] = Field(default=None, ge=0)
    metadata:                dict           = Field(default_factory=dict)


class NodeCreate(NodeBase):
    """Schema for creating a new supply chain node (admin only)."""
    pass


class NodeUpdate(BaseModel):
    """Schema for partial node updates. All fields optional."""
    model_config = ConfigDict(from_attributes=True)

    node_name:               Optional[str]            = None
    current_utilization_pct: Optional[float]          = Field(default=None, ge=0.0, le=1.0)
    status:                  Optional[NodeStatusEnum] = None
    redundancy_score:        Optional[float]          = Field(default=None, ge=0.0, le=1.0)
    criticality_score:       Optional[float]          = Field(default=None, ge=0.0, le=1.0)
    metadata:                Optional[dict]           = None


class NodeResponse(NodeBase):
    """Full node response including server-generated fields."""
    node_id:    uuid.UUID
    created_at: datetime
    updated_at: datetime


class NodeGraphData(BaseModel):
    """Minimal node representation for NetworkX graph construction."""
    model_config = ConfigDict(from_attributes=True)

    node_id:               uuid.UUID
    node_code:             str
    node_type:             NodeTypeEnum
    stage:                 StageEnum
    latitude:              float
    longitude:             float
    geopolitical_zone:     GeopoliticalZoneEnum
    capacity_bpd:          float
    current_utilization_pct: float
    status:                NodeStatusEnum
    redundancy_score:      float
    criticality_score:     float
    mean_time_between_failures_days: Optional[float]
    mean_time_to_repair_days:        Optional[float]


class NodeListResponse(BaseModel):
    items:  list[NodeResponse]
    total:  int
    limit:  int
    offset: int
