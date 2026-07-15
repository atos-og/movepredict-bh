from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ServiceAlert(BaseModel):
    id: str
    title: str
    description: str | None = None
    url: str | None = None
    cause: str | None = None
    effect: str | None = None
    route_ids: list[str] = Field(default_factory=list)
    stop_ids: list[str] = Field(default_factory=list)
    active_from: datetime | None = None
    active_until: datetime | None = None


class ServiceAlertMeta(BaseModel):
    generated_at: datetime
    count: int = Field(ge=0)
    status: Literal["live", "empty", "unavailable"]
    source_configured: bool


class ServiceAlertResponse(BaseModel):
    data: list[ServiceAlert]
    meta: ServiceAlertMeta
