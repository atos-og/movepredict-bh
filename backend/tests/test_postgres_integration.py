import os
from datetime import UTC, date, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session

from app.database import get_db
from app.main import create_app
from app.models import (
    ArrivalPrediction,
    RouteSourceCode,
    ServiceCalendar,
    TransitRoute,
    TransitStop,
    TransitTrip,
    TripStop,
    Vehicle,
    VehiclePosition,
)
from app.schemas.realtime import ArrivalPrediction as ArrivalPredictionSchema
from app.schemas.realtime import VehiclePosition as VehiclePositionSchema
from app.services.arrival_detection import detect_arrivals
from app.services.pbh_realtime import PbhVehiclePosition
from app.services.prediction_generation import MODEL_VERSION, generate_predictions
from app.services.provider_contracts import ArrivalPredictionProvider, VehiclePositionProvider
from app.services.sql_providers import SqlArrivalPredictionProvider, SqlVehiclePositionProvider
from app.services.trip_matching import match_unassigned_positions
from app.workers.realtime_consumer import persist_snapshot

pytestmark = pytest.mark.integration


@pytest.fixture
def postgres_session() -> Session:
    database_url = os.getenv("MOVEPREDICT_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("MOVEPREDICT_TEST_DATABASE_URL não configurada")
    engine = create_engine(database_url)
    with Session(engine) as session:
        session.execute(
            text(
                "TRUNCATE pipeline_runs, collection_runs, arrival_events, arrival_predictions, "
                "vehicle_positions, vehicles, trip_stops, transit_trips, transit_shapes, "
                "service_exceptions, service_calendars, transit_stops, route_source_codes, "
                "transit_routes "
                "RESTART IDENTITY CASCADE"
            )
        )
        session.commit()
        yield session
        session.rollback()
    engine.dispose()


def test_persistence_deduplication_disappearance_and_provider_contract(
    postgres_session: Session,
) -> None:
    route = TransitRoute(gtfs_route_id="r1", short_name="5106", long_name="Linha teste")
    stop = TransitStop(gtfs_stop_id="s1", name="Ponto teste", latitude=-19.92, longitude=-43.94)
    postgres_session.add_all([route, stop])
    postgres_session.flush()
    postgres_session.add(
        RouteSourceCode(
            source_code="101",
            public_line_code="5106",
            source_name="Linha teste",
            route_id=route.id,
        )
    )
    observed = datetime.now(UTC)
    first_snapshot = [
        _position("bus-1", observed, "101"),
        _position("bus-1", observed, "101"),
        _position("bus-2", observed, "101"),
    ]

    first = persist_snapshot(postgres_session, first_snapshot, ingested_at=observed)
    second = persist_snapshot(postgres_session, first_snapshot, ingested_at=observed)
    later = persist_snapshot(
        postgres_session,
        [_position("bus-1", observed + timedelta(minutes=3), "101")],
        ingested_at=observed + timedelta(minutes=3),
        disappearance_seconds=120,
    )
    postgres_session.commit()

    assert first.inserted == 2
    assert first.duplicates == 1
    assert second.inserted == 0
    assert later.disappeared_vehicles == 1
    assert postgres_session.get(Vehicle, 2).is_active is False

    vehicle_provider: VehiclePositionProvider = SqlVehiclePositionProvider(postgres_session)
    positions = vehicle_provider.list_current_positions("r1")
    assert len(positions) == 1
    assert isinstance(positions[0], VehiclePositionSchema)
    assert positions[0].vehicle_id == "bus-1"
    assert positions[0].route_id == "r1"

    vehicle = postgres_session.get(Vehicle, 1)
    postgres_session.add(
        ArrivalPrediction(
            stop_id=stop.id,
            route_id=route.id,
            trip_id=None,
            vehicle_id=vehicle.id,
            generated_at=observed,
            predicted_arrival=observed + timedelta(minutes=5),
            uncertainty_seconds=90,
            model_version="baseline-schedule-v1",
        )
    )
    postgres_session.commit()
    arrival_provider: ArrivalPredictionProvider = SqlArrivalPredictionProvider(postgres_session)
    predictions = arrival_provider.predict_arrivals("s1", at=observed)
    assert len(predictions) == 1
    assert isinstance(predictions[0], ArrivalPredictionSchema)
    assert predictions[0].vehicle_id == "bus-1"
    assert predictions[0].route_id == "r1"

    application = create_app()
    application.dependency_overrides[get_db] = lambda: postgres_session
    with TestClient(application) as client:
        vehicle_response = client.get(
            "/realtime/vehicles",
            params={"route_id": "r1", "max_age_seconds": 3600},
        )
        arrival_response = client.get(
            "/realtime/stops/s1/arrivals",
            params={"max_age_seconds": 3600},
        )

    assert vehicle_response.status_code == 200
    assert vehicle_response.json()["data"][0]["vehicle_id"] == "bus-1"
    assert arrival_response.status_code == 200
    assert arrival_response.json()["data"][0]["stop_id"] == "s1"


def test_trip_matching_prediction_and_arrival_detection(postgres_session: Session) -> None:
    route = TransitRoute(gtfs_route_id="r1", short_name="5106", long_name="Linha teste")
    first_stop = TransitStop(
        gtfs_stop_id="s1", name="Ponto inicial", latitude=-19.92, longitude=-43.94
    )
    next_stop = TransitStop(
        gtfs_stop_id="s2", name="Ponto seguinte", latitude=-19.92, longitude=-43.93
    )
    postgres_session.add_all([route, first_stop, next_stop])
    postgres_session.flush()
    trip = TransitTrip(
        gtfs_trip_id="t1",
        route_id=route.id,
        service_id="daily",
        direction_id=0,
        headsign="Centro",
        shape_id="shape-1",
        start_time_seconds=12 * 3600,
        end_time_seconds=13 * 3600,
    )
    postgres_session.add_all(
        [
            RouteSourceCode(
                source_code="101",
                public_line_code="5106",
                source_name="Linha teste",
                route_id=route.id,
            ),
            ServiceCalendar(
                service_id="daily",
                monday=True,
                tuesday=True,
                wednesday=True,
                thursday=True,
                friday=True,
                saturday=True,
                sunday=True,
                start_date=date(2026, 1, 1),
                end_date=date(2026, 12, 31),
            ),
            trip,
        ]
    )
    postgres_session.flush()
    postgres_session.execute(
        text(
            "INSERT INTO transit_shapes (gtfs_shape_id, point_count, path, length_meters) "
            "VALUES ('shape-1', 2, ST_GeomFromText("
            "'LINESTRING(-43.94 -19.92,-43.93 -19.92)', 4326), 1046)"
        )
    )
    postgres_session.add_all(
        [
            TripStop(
                trip_id=trip.id,
                stop_id=first_stop.id,
                stop_sequence=1,
                scheduled_arrival_seconds=12 * 3600,
                scheduled_departure_seconds=12 * 3600,
                shape_progress=0,
            ),
            TripStop(
                trip_id=trip.id,
                stop_id=next_stop.id,
                stop_sequence=2,
                scheduled_arrival_seconds=12 * 3600 + 300,
                scheduled_departure_seconds=12 * 3600 + 300,
                shape_progress=1,
            ),
        ]
    )
    observed = datetime(2026, 7, 11, 15, tzinfo=UTC)
    persist_snapshot(
        postgres_session,
        [_position_at("bus-1", observed, longitude=-43.939, speed_kmh=18)],
        ingested_at=observed,
    )
    postgres_session.commit()

    matched = match_unassigned_positions(postgres_session)
    generated = generate_predictions(postgres_session)
    prediction = postgres_session.scalar(
        select(ArrivalPrediction).where(ArrivalPrediction.model_version == MODEL_VERSION)
    )
    assert matched.matched == 1
    assert generated.predictions == 1
    assert prediction is not None
    assert prediction.stop_id == next_stop.id

    vehicle = postgres_session.scalar(select(Vehicle).where(Vehicle.source_vehicle_id == "bus-1"))
    postgres_session.add(
        VehiclePosition(
            vehicle_id=vehicle.id,
            route_id=route.id,
            trip_id=trip.id,
            observed_at=observed + timedelta(minutes=3),
            ingested_at=observed + timedelta(minutes=3),
            latitude=-19.92,
            longitude=-43.93,
            speed_kmh=0,
            bearing=90,
            direction_code=1,
            source_line_code="101",
            distance_traveled=2_000,
            source_event="105",
            shape_progress=1,
            trip_match_confidence=1,
            trip_match_method="test",
        )
    )
    postgres_session.commit()

    detected = detect_arrivals(postgres_session)
    postgres_session.refresh(prediction)
    assert detected.detected == 1
    assert detected.predictions_labeled == 1
    assert prediction.actual_arrival == observed + timedelta(minutes=3)


def _position(vehicle_id: str, observed_at: datetime, line_code: str) -> PbhVehiclePosition:
    return PbhVehiclePosition(
        vehicle_id=vehicle_id,
        observed_at=observed_at,
        latitude=-19.92,
        longitude=-43.94,
        speed_kmh=20,
        bearing=90,
        source_line_code=line_code,
        direction_code=1,
        distance_traveled=1_000,
        event_code="105",
    )


def _position_at(
    vehicle_id: str, observed_at: datetime, *, longitude: float, speed_kmh: float
) -> PbhVehiclePosition:
    position = _position(vehicle_id, observed_at, "101")
    return PbhVehiclePosition(
        vehicle_id=position.vehicle_id,
        observed_at=position.observed_at,
        latitude=position.latitude,
        longitude=longitude,
        speed_kmh=speed_kmh,
        bearing=position.bearing,
        source_line_code=position.source_line_code,
        direction_code=position.direction_code,
        distance_traveled=position.distance_traveled,
        event_code=position.event_code,
    )
