from typing import Literal

from pydantic import BaseModel, Field


class Line(BaseModel):
    route_id: str
    route_short_name: str | None = None
    route_long_name: str | None = None
    route_type: int | None = None
    route_color: str | None = None
    route_text_color: str | None = None


class Stop(BaseModel):
    stop_id: str
    stop_code: str | None = None
    stop_name: str
    stop_lat: float
    stop_lon: float
    wheelchair_boarding: int | None = None


class Trip(BaseModel):
    route_id: str
    service_id: str | None = None
    trip_id: str
    trip_headsign: str | None = None
    direction_id: str | None = None
    shape_id: str | None = None


class LineStop(Stop):
    stop_sequence: int = Field(ge=0)
    arrival_time: str | None = None
    departure_time: str | None = None


class GeoJsonLineString(BaseModel):
    type: Literal["LineString"] = "LineString"
    coordinates: list[tuple[float, float]]


class LineRoute(BaseModel):
    route_id: str
    trip_id: str
    shape_id: str
    direction_id: str | None = None
    geometry: GeoJsonLineString
