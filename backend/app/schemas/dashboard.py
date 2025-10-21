from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.metric import MetricBrief


class DashboardBase(BaseModel):
    name: str
    description: str | None = None


class DashboardCreate(DashboardBase):
    pass


class DashboardUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class DashboardResponse(BaseModel):
    id: int
    name: str
    description: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DashboardDetailResponse(DashboardResponse):
    metrics: list[MetricBrief] = []


class Dashboard(DashboardBase):
    id: int
    owner_id: int

    model_config = ConfigDict(from_attributes=True)
