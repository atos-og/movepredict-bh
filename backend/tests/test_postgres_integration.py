import os
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.models import (
    ArrivalPrediction,
    RouteSourceCode,
    TransitRoute,
    TransitStop,
    Vehicle,
)
from app.schemas.realtime import ArrivalPrediction as ArrivalPredictionSchema
from app.schemas.realtime import VehiclePosition as VehiclePositionSchema
from app.services.pbh_realtime import PbhVehiclePosition
from app.services.provider_contracts import ArrivalPredictionProvider, VehiclePositionProvider
from app.services.sql_providers import SqlArrivalPredictionProvider, SqlVehiclePositionProvider
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
                "TRUNCATE collection_runs, arrival_predictions, vehicle_positions, vehicles, "
                "trip_stops, transit_trips, transit_stops, route_source_codes, transit_routes "
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
    observed = datetime(2026, 7, 11, 15, tzinfo=UTC)
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
