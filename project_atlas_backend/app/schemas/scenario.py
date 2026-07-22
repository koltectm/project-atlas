"""app/schemas/scenario.py — Pydantic schemas for scenarios and disruptions."""
from __future__ import annotations
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from app.db.models import ScenarioStatusEnum, DisruptionCategoryEnum


class ScenarioDisruptionCreate(BaseModel):
    disruption_type_id:     uuid.UUID
    target_node_id:         Optional[uuid.UUID] = None
    target_link_id:         Optional[uuid.UUID] = None
    probability_override:   Optional[float]     = Field(default=None, ge=0.0, le=1.0)
    severity_override:      Optional[float]     = Field(default=None, ge=0.0, le=1.0)
    duration_days_override: Optional[float]     = Field(default=None, gt=0)
    simultaneous_with:      Optional[uuid.UUID] = None
    is_active:              bool = True


class ScenarioDisruptionResponse(ScenarioDisruptionCreate):
    model_config = ConfigDict(from_attributes=True)

    scenario_disruption_id: uuid.UUID
    scenario_id:            uuid.UUID
    created_at:             datetime
    updated_at:             datetime


class ScenarioCreate(BaseModel):
    scenario_name:         str          = Field(..., min_length=1, max_length=255)
    description:           Optional[str] = None
    is_public:             bool         = False
    simulation_iterations: int          = Field(default=10_000, ge=100, le=100_000)
    time_horizon_days:     int          = Field(default=365, ge=1, le=3650)
    random_seed:           Optional[int] = None
    tags:                  list[str]    = Field(default_factory=list)
    disruptions:           list[ScenarioDisruptionCreate] = Field(default_factory=list)


class ScenarioUpdate(BaseModel):
    scenario_name:         Optional[str]  = Field(default=None, max_length=255)
    description:           Optional[str]  = None
    is_public:             Optional[bool] = None
    simulation_iterations: Optional[int]  = Field(default=None, ge=100, le=100_000)
    time_horizon_days:     Optional[int]  = Field(default=None, ge=1, le=3650)
    random_seed:           Optional[int]  = None
    tags:                  Optional[list[str]] = None


class ScenarioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    scenario_id:           uuid.UUID
    scenario_name:         str
    description:           Optional[str]
    version:               int
    created_by:            uuid.UUID
    is_public:             bool
    simulation_iterations: int
    time_horizon_days:     int
    random_seed:           Optional[int]
    status:                ScenarioStatusEnum
    tags:                  list[str]
    disruptions:           list[ScenarioDisruptionResponse] = Field(default_factory=list)
    created_at:            datetime
    updated_at:            datetime


class ScenarioListResponse(BaseModel):
    items:  list[ScenarioResponse]
    total:  int
    limit:  int
    offset: int


class DisruptionTypeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    disruption_type_id:          uuid.UUID
    category:                    DisruptionCategoryEnum
    name:                        str
    description:                 str
    typical_duration_days_min:   float
    typical_duration_days_mode:  float
    typical_duration_days_max:   float
    typical_annual_probability:  float
    severity_min:                float
    severity_mode:               float
    severity_max:                float
    cost_multiplier_min:         float
    cost_multiplier_max:         float
    recovery_time_days_min:      float
    recovery_time_days_max:      float
    affected_node_types:         list
    affected_link_types:         list
    correlated_disruption_ids:   list
    cascading_probability:       Optional[float]
    created_at:                  datetime
    updated_at:                  datetime
