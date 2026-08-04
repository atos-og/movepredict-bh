from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class Coordinates(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class GeocodedDestination(BaseModel):
    id: str
    kind: Literal["destination", "neighborhood", "landmark", "address"]
    label: str
    description: str
    coordinates: Coordinates


class GeocodingMeta(BaseModel):
    provider: Literal["nominatim"] = "nominatim"
    attribution: str = "OpenStreetMap contributors"
    cached: bool = False


class GeocodingResponse(BaseModel):
    data: list[GeocodedDestination]
    meta: GeocodingMeta


class JourneyStop(BaseModel):
    stop_id: str
    name: str
    coordinates: Coordinates


class JourneyStep(BaseModel):
    id: str
    kind: Literal["walk", "bus"]
    title: str
    description: str | None = None
    duration_minutes: int = Field(ge=0)
    distance_meters: int = Field(ge=0)
    route_id: str | None = None
    route_short_name: str | None = None
    route_long_name: str | None = None
    trip_id: str | None = None
    headsign: str | None = None
    from_stop: JourneyStop | None = None
    to_stop: JourneyStop | None = None
    intermediate_stops: list[JourneyStop] = Field(default_factory=list)
    scheduled_start: datetime | None = None
    scheduled_end: datetime | None = None
    geometry: str | None = None
    realtime: bool = False


class JourneyPlan(BaseModel):
    id: str
    preference: Literal["quickest", "less_walking", "fewer_transfers"]
    total_duration_minutes: int = Field(ge=0)
    walking_duration_minutes: int = Field(ge=0)
    walking_distance_meters: int = Field(ge=0)
    transfer_count: int = Field(ge=0)
    scheduled_departure: datetime | None = None
    estimated_arrival: datetime | None = None
    steps: list[JourneyStep]


class JourneyPlanMeta(BaseModel):
    provider: Literal["opentripplanner"] = "opentripplanner"
    realtime_applied: bool = False
    generated_at: datetime


class JourneyPlanResponse(BaseModel):
    data: list[JourneyPlan]
    meta: JourneyPlanMeta
