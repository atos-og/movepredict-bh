from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.database import SessionLocal
from app.models import (
    ArrivalPrediction,
    RouteSourceCode,
    TransitRoute,
    TransitStop,
    TransitTrip,
    TripStop,
    Vehicle,
    VehiclePosition,
)


def seed() -> None:
    now = datetime.now(UTC).replace(microsecond=0)
    with SessionLocal() as session:
        if session.scalar(select(TransitRoute).where(TransitRoute.gtfs_route_id == "dev-route")):
            return
        route = TransitRoute(
            gtfs_route_id="dev-route", short_name="DEV1", long_name="Linha de desenvolvimento"
        )
        stop = TransitStop(
            gtfs_stop_id="dev-stop",
            name="Ponto de desenvolvimento",
            latitude=-19.9191,
            longitude=-43.9386,
        )
        session.add_all([route, stop])
        session.flush()
        trip = TransitTrip(
            gtfs_trip_id="dev-trip",
            route_id=route.id,
            service_id="dev-service",
            direction_id=0,
            headsign="Centro",
            shape_id="dev-shape",
        )
        vehicle = Vehicle(
            source_vehicle_id="dev-vehicle",
            first_seen_at=now,
            last_seen_at=now,
            is_active=True,
        )
        session.add_all([trip, vehicle])
        session.flush()
        session.add_all(
            [
                RouteSourceCode(
                    source_code="dev-source-route",
                    public_line_code="DEV1",
                    source_name="Linha de desenvolvimento",
                    route_id=route.id,
                ),
                TripStop(
                    trip_id=trip.id,
                    stop_id=stop.id,
                    stop_sequence=1,
                    scheduled_arrival_seconds=8 * 3600,
                    scheduled_departure_seconds=8 * 3600 + 30,
                ),
                VehiclePosition(
                    vehicle_id=vehicle.id,
                    route_id=route.id,
                    trip_id=trip.id,
                    observed_at=now,
                    ingested_at=now,
                    latitude=-19.9200,
                    longitude=-43.9400,
                    speed_kmh=18,
                    bearing=90,
                    direction_code=1,
                    source_line_code="dev-source-route",
                    distance_traveled=1_000,
                    source_event="105",
                ),
                ArrivalPrediction(
                    stop_id=stop.id,
                    route_id=route.id,
                    trip_id=trip.id,
                    vehicle_id=vehicle.id,
                    generated_at=now,
                    predicted_arrival=now + timedelta(minutes=5),
                    uncertainty_seconds=90,
                    model_version="baseline-schedule-v1",
                ),
            ]
        )
        session.commit()


if __name__ == "__main__":
    seed()
