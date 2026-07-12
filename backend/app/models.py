from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class TransitRoute(Base):
    __tablename__ = "transit_routes"

    id: Mapped[int] = mapped_column(primary_key=True)
    gtfs_route_id: Mapped[str | None] = mapped_column(String(100), unique=True)
    short_name: Mapped[str | None] = mapped_column(String(50), index=True)
    long_name: Mapped[str | None] = mapped_column(String(255))
    trips: Mapped[list["TransitTrip"]] = relationship(back_populates="route")


class RouteSourceCode(Base):
    __tablename__ = "route_source_codes"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_code: Mapped[str] = mapped_column(String(50), unique=True)
    public_line_code: Mapped[str] = mapped_column(String(50), index=True)
    source_name: Mapped[str | None] = mapped_column(String(255))
    route_id: Mapped[int | None] = mapped_column(ForeignKey("transit_routes.id"), index=True)


class TransitStop(Base):
    __tablename__ = "transit_stops"

    id: Mapped[int] = mapped_column(primary_key=True)
    gtfs_stop_id: Mapped[str] = mapped_column(String(100), unique=True)
    name: Mapped[str] = mapped_column(String(255))
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)

    __table_args__ = (
        CheckConstraint("latitude BETWEEN -90 AND 90", name="ck_stop_latitude"),
        CheckConstraint("longitude BETWEEN -180 AND 180", name="ck_stop_longitude"),
        Index("ix_transit_stops_coordinates", "latitude", "longitude"),
    )


class TransitTrip(Base):
    __tablename__ = "transit_trips"

    id: Mapped[int] = mapped_column(primary_key=True)
    gtfs_trip_id: Mapped[str] = mapped_column(String(150), unique=True)
    route_id: Mapped[int] = mapped_column(ForeignKey("transit_routes.id"), index=True)
    service_id: Mapped[str | None] = mapped_column(String(100))
    direction_id: Mapped[int | None] = mapped_column(Integer)
    headsign: Mapped[str | None] = mapped_column(String(255))
    shape_id: Mapped[str | None] = mapped_column(String(100))
    start_time_seconds: Mapped[int | None] = mapped_column(Integer, index=True)
    end_time_seconds: Mapped[int | None] = mapped_column(Integer)
    route: Mapped[TransitRoute] = relationship(back_populates="trips")


class TripStop(Base):
    __tablename__ = "trip_stops"

    id: Mapped[int] = mapped_column(primary_key=True)
    trip_id: Mapped[int] = mapped_column(ForeignKey("transit_trips.id"), index=True)
    stop_id: Mapped[int] = mapped_column(ForeignKey("transit_stops.id"), index=True)
    stop_sequence: Mapped[int] = mapped_column(Integer)
    scheduled_arrival_seconds: Mapped[int | None] = mapped_column(Integer)
    scheduled_departure_seconds: Mapped[int | None] = mapped_column(Integer)
    shape_progress: Mapped[float | None] = mapped_column(Float)

    __table_args__ = (UniqueConstraint("trip_id", "stop_sequence", name="uq_trip_stop_sequence"),)


class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_vehicle_id: Mapped[str] = mapped_column(String(100), unique=True)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    disappeared_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class VehiclePosition(Base):
    __tablename__ = "vehicle_positions"

    id: Mapped[int] = mapped_column(primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id"), index=True)
    route_id: Mapped[int | None] = mapped_column(ForeignKey("transit_routes.id"), index=True)
    trip_id: Mapped[int | None] = mapped_column(ForeignKey("transit_trips.id"), index=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    speed_kmh: Mapped[float | None] = mapped_column(Float)
    bearing: Mapped[float | None] = mapped_column(Float)
    direction_code: Mapped[int | None] = mapped_column(Integer)
    source_line_code: Mapped[str | None] = mapped_column(String(50), index=True)
    distance_traveled: Mapped[float | None] = mapped_column(Float)
    source_event: Mapped[str] = mapped_column(String(20), default="105")
    shape_progress: Mapped[float | None] = mapped_column(Float)
    trip_match_confidence: Mapped[float | None] = mapped_column(Float)
    trip_match_method: Mapped[str | None] = mapped_column(String(50))

    __table_args__ = (
        CheckConstraint("latitude BETWEEN -90 AND 90", name="ck_position_latitude"),
        CheckConstraint("longitude BETWEEN -180 AND 180", name="ck_position_longitude"),
        CheckConstraint("speed_kmh IS NULL OR speed_kmh >= 0", name="ck_position_speed"),
        CheckConstraint("bearing IS NULL OR bearing BETWEEN 0 AND 360", name="ck_position_bearing"),
        UniqueConstraint("vehicle_id", "observed_at", name="uq_vehicle_position_observation"),
        Index("ix_vehicle_positions_vehicle_observed", "vehicle_id", "observed_at"),
        Index("ix_vehicle_positions_route_observed", "route_id", "observed_at"),
        Index("ix_vehicle_positions_trip_observed", "trip_id", "observed_at"),
        Index("ix_vehicle_positions_coordinates", "latitude", "longitude"),
    )


class ArrivalPrediction(Base):
    __tablename__ = "arrival_predictions"

    id: Mapped[int] = mapped_column(primary_key=True)
    stop_id: Mapped[int] = mapped_column(ForeignKey("transit_stops.id"), index=True)
    route_id: Mapped[int] = mapped_column(ForeignKey("transit_routes.id"), index=True)
    trip_id: Mapped[int | None] = mapped_column(ForeignKey("transit_trips.id"), index=True)
    vehicle_id: Mapped[int | None] = mapped_column(ForeignKey("vehicles.id"), index=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    predicted_arrival: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    actual_arrival: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    distance_to_stop_meters: Mapped[float | None] = mapped_column(Float)
    uncertainty_seconds: Mapped[int | None] = mapped_column(Integer)
    model_version: Mapped[str] = mapped_column(String(50), default="baseline-haversine-v1")


class CollectionRun(Base):
    __tablename__ = "collection_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), index=True)
    attempt_count: Mapped[int] = mapped_column(Integer, default=1)
    http_status: Mapped[int | None] = mapped_column(Integer)
    fetched_count: Mapped[int] = mapped_column(Integer, default=0)
    parsed_count: Mapped[int] = mapped_column(Integer, default=0)
    parse_error_count: Mapped[int] = mapped_column(Integer, default=0)
    inserted_count: Mapped[int] = mapped_column(Integer, default=0)
    duplicate_count: Mapped[int] = mapped_column(Integer, default=0)
    unmatched_route_count: Mapped[int] = mapped_column(Integer, default=0)
    disappeared_vehicle_count: Mapped[int] = mapped_column(Integer, default=0)
    source_latest_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source_lag_seconds: Mapped[float | None] = mapped_column(Float)
    duration_ms: Mapped[float | None] = mapped_column(Float)
    error_type: Mapped[str | None] = mapped_column(String(100))
    error_message: Mapped[str | None] = mapped_column(Text)


class ServiceCalendar(Base):
    __tablename__ = "service_calendars"

    id: Mapped[int] = mapped_column(primary_key=True)
    service_id: Mapped[str] = mapped_column(String(100), unique=True)
    monday: Mapped[bool] = mapped_column(Boolean)
    tuesday: Mapped[bool] = mapped_column(Boolean)
    wednesday: Mapped[bool] = mapped_column(Boolean)
    thursday: Mapped[bool] = mapped_column(Boolean)
    friday: Mapped[bool] = mapped_column(Boolean)
    saturday: Mapped[bool] = mapped_column(Boolean)
    sunday: Mapped[bool] = mapped_column(Boolean)
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)


class ServiceException(Base):
    __tablename__ = "service_exceptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    service_id: Mapped[str] = mapped_column(String(100), index=True)
    service_date: Mapped[date] = mapped_column(Date, index=True)
    exception_type: Mapped[int] = mapped_column(Integer)

    __table_args__ = (
        UniqueConstraint("service_id", "service_date", name="uq_service_exception"),
        CheckConstraint("exception_type IN (1, 2)", name="ck_service_exception_type"),
    )


class TransitShape(Base):
    __tablename__ = "transit_shapes"

    id: Mapped[int] = mapped_column(primary_key=True)
    gtfs_shape_id: Mapped[str] = mapped_column(String(100), unique=True)
    point_count: Mapped[int] = mapped_column(Integer)
    length_meters: Mapped[float | None] = mapped_column(Float)


class ArrivalEvent(Base):
    __tablename__ = "arrival_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id"), index=True)
    route_id: Mapped[int] = mapped_column(ForeignKey("transit_routes.id"), index=True)
    trip_id: Mapped[int] = mapped_column(ForeignKey("transit_trips.id"), index=True)
    stop_id: Mapped[int] = mapped_column(ForeignKey("transit_stops.id"), index=True)
    position_id: Mapped[int] = mapped_column(ForeignKey("vehicle_positions.id"), unique=True)
    service_date: Mapped[date] = mapped_column(Date, index=True)
    arrived_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    distance_to_stop_meters: Mapped[float] = mapped_column(Float)
    detection_method: Mapped[str] = mapped_column(String(50))

    __table_args__ = (
        UniqueConstraint(
            "vehicle_id",
            "trip_id",
            "stop_id",
            "service_date",
            name="uq_arrival_event_vehicle_trip_stop_date",
        ),
        CheckConstraint("distance_to_stop_meters >= 0", name="ck_arrival_distance"),
    )
