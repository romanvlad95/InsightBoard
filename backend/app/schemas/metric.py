from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class MetricIngest(BaseModel):
    """Schema for metric ingestion via API"""

    dashboard_id: int
    name: str
    value: float
    metric_type: str = "gauge"
    timestamp: str | None = None
    metadata: dict[str, Any] | None = None


class MetricCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    value: float
    metric_type: str = Field(..., min_length=1, max_length=50)
    dashboard_id: int


class MetricUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    value: float | None = None
    metric_type: str | None = Field(None, min_length=1, max_length=50)


class MetricResponse(BaseModel):
    id: int
    name: str
    value: float
    metric_type: str
    dashboard_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DashboardBrief(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class MetricDetailResponse(MetricResponse):
    dashboard: DashboardBrief


class MetricBrief(BaseModel):
    id: int
    name: str
    metric_type: str

    model_config = ConfigDict(from_attributes=True)
