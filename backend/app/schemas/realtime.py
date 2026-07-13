from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class VehiclePosition(BaseModel):
    vehicle_id: str
    route_id: str | None = None
    trip_id: str | None = None
    latitude: float
    longitude: float
    bearing: float | None = None
    speed_kmh: float | None = None
    observed_at: datetime
    status: Literal["in_transit", "stopped", "unknown"] = "unknown"


class ArrivalPrediction(BaseModel):
    stop_id: str
    route_id: str
    trip_id: str | None = None
    vehicle_id: str | None = None
    predicted_arrival: datetime
    generated_at: datetime
    uncertainty_seconds: int | None = None
    model_version: str | None = None


class RealtimeMeta(BaseModel):
    generated_at: datetime
    count: int = Field(ge=0)
    status: Literal["live", "empty", "stale"]
    stale: bool = False
    stale_after_seconds: int = Field(ge=1)


class VehiclePositionResponse(BaseModel):
    data: list[VehiclePosition]
    meta: RealtimeMeta


class ArrivalPredictionResponse(BaseModel):
    data: list[ArrivalPrediction]
    meta: RealtimeMeta
