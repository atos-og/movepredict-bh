from datetime import datetime
from typing import Literal

from pydantic import BaseModel


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
