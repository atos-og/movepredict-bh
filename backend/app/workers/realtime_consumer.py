import argparse
import json
import logging
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import SessionLocal
from app.models import CollectionRun, RouteSourceCode, Vehicle, VehiclePosition
from app.services.pbh_realtime import PbhRealtimeClient, PbhVehiclePosition

logger = logging.getLogger("movepredict.realtime")


@dataclass(frozen=True)
class PersistResult:
    fetched: int
    unique: int
    inserted: int
    duplicates: int
    unmatched_routes: int
    disappeared_vehicles: int
    source_latest_at: datetime | None


def persist_snapshot(
    session: Session,
    positions: list[PbhVehiclePosition],
    *,
    ingested_at: datetime | None = None,
    disappearance_seconds: int = 120,
) -> PersistResult:
    ingested_at = (ingested_at or datetime.now(UTC)).astimezone(UTC)
    fetched = len(positions)
    positions = list(
        {(position.vehicle_id, position.observed_at): position for position in positions}.values()
    )
    if not positions:
        return PersistResult(fetched, 0, 0, fetched, 0, 0, None)

    route_ids = {
        mapping.source_code: mapping.route_id
        for mapping in session.scalars(select(RouteSourceCode))
    }
    source_vehicle_ids = {position.vehicle_id for position in positions}
    vehicles = {
        vehicle.source_vehicle_id: vehicle
        for vehicle in session.scalars(
            select(Vehicle).where(Vehicle.source_vehicle_id.in_(source_vehicle_ids))
        )
    }
    for position in positions:
        vehicle = vehicles.get(position.vehicle_id)
        if vehicle is None:
            vehicle = Vehicle(
                source_vehicle_id=position.vehicle_id,
                first_seen_at=position.observed_at,
                last_seen_at=position.observed_at,
                is_active=True,
            )
            session.add(vehicle)
            session.flush()
            vehicles[position.vehicle_id] = vehicle
        else:
            vehicle.last_seen_at = max(vehicle.last_seen_at, position.observed_at)
            vehicle.is_active = True
            vehicle.disappeared_at = None
    session.flush()

    existing = set(
        session.execute(
            select(VehiclePosition.vehicle_id, VehiclePosition.observed_at).where(
                VehiclePosition.vehicle_id.in_([vehicle.id for vehicle in vehicles.values()]),
                VehiclePosition.observed_at >= min(position.observed_at for position in positions),
                VehiclePosition.observed_at <= max(position.observed_at for position in positions),
            )
        )
    )
    inserted = 0
    unmatched = 0
    for position in positions:
        vehicle = vehicles[position.vehicle_id]
        if (vehicle.id, position.observed_at) in existing:
            continue
        route_id = route_ids.get(position.source_line_code)
        unmatched += route_id is None
        session.add(
            VehiclePosition(
                vehicle_id=vehicle.id,
                route_id=route_id,
                trip_id=None,
                observed_at=position.observed_at,
                ingested_at=ingested_at,
                latitude=position.latitude,
                longitude=position.longitude,
                speed_kmh=position.speed_kmh,
                bearing=position.bearing,
                direction_code=position.direction_code,
                source_line_code=position.source_line_code,
                distance_traveled=position.distance_traveled,
                source_event=position.event_code,
            )
        )
        inserted += 1

    source_latest_at = max(position.observed_at for position in positions)
    disappearance_cutoff = source_latest_at - timedelta(seconds=disappearance_seconds)
    disappeared = list(
        session.scalars(
            select(Vehicle).where(
                Vehicle.is_active.is_(True),
                Vehicle.last_seen_at < disappearance_cutoff,
                ~Vehicle.source_vehicle_id.in_(source_vehicle_ids),
            )
        )
    )
    for vehicle in disappeared:
        vehicle.is_active = False
        vehicle.disappeared_at = ingested_at
    session.flush()
    return PersistResult(
        fetched=fetched,
        unique=len(positions),
        inserted=inserted,
        duplicates=fetched - inserted,
        unmatched_routes=unmatched,
        disappeared_vehicles=len(disappeared),
        source_latest_at=source_latest_at,
    )


def collect_once() -> PersistResult:
    settings = get_settings()
    started_at = datetime.now(UTC)
    started_monotonic = time.monotonic()
    client = PbhRealtimeClient(
        settings.realtime_positions_url,
        timeout=settings.realtime_timeout_seconds,
        max_retries=settings.realtime_max_retries,
        backoff_seconds=settings.realtime_backoff_seconds,
    )
    try:
        positions = client.fetch_positions()
        ingested_at = datetime.now(UTC)
        with SessionLocal() as session:
            result = persist_snapshot(
                session,
                positions,
                ingested_at=ingested_at,
                disappearance_seconds=settings.realtime_disappearance_seconds,
            )
            lag = (
                max(0.0, (ingested_at - result.source_latest_at).total_seconds())
                if result.source_latest_at
                else None
            )
            session.add(
                CollectionRun(
                    started_at=started_at,
                    finished_at=datetime.now(UTC),
                    status="success",
                    attempt_count=client.last_attempt_count,
                    http_status=client.last_http_status,
                    fetched_count=client.last_fetched_count,
                    parsed_count=result.fetched,
                    parse_error_count=client.last_parse_error_count,
                    inserted_count=result.inserted,
                    duplicate_count=result.duplicates,
                    unmatched_route_count=result.unmatched_routes,
                    disappeared_vehicle_count=result.disappeared_vehicles,
                    source_latest_at=result.source_latest_at,
                    source_lag_seconds=lag,
                    duration_ms=(time.monotonic() - started_monotonic) * 1_000,
                )
            )
            session.commit()
        _log_event("collection_success", result=asdict(result), attempts=client.last_attempt_count)
        return result
    except Exception as error:
        with SessionLocal() as session:
            session.add(
                CollectionRun(
                    started_at=started_at,
                    finished_at=datetime.now(UTC),
                    status="failure",
                    attempt_count=client.last_attempt_count,
                    http_status=client.last_http_status,
                    fetched_count=client.last_fetched_count,
                    parse_error_count=client.last_parse_error_count,
                    duration_ms=(time.monotonic() - started_monotonic) * 1_000,
                    error_type=type(error).__name__,
                    error_message=str(error)[:2_000],
                )
            )
            session.commit()
        _log_event(
            "collection_failure",
            level=logging.ERROR,
            error_type=type(error).__name__,
            error=str(error),
            attempts=client.last_attempt_count,
        )
        raise


def _log_event(event: str, *, level: int = logging.INFO, **fields) -> None:
    logger.log(level, json.dumps({"event": event, **fields}, default=str, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser(description="Coleta posições oficiais da PBH.")
    parser.add_argument("--once", action="store_true", help="executa somente uma coleta")
    args = parser.parse_args()
    settings = get_settings()
    logging.basicConfig(level=logging.INFO)
    while True:
        started = time.monotonic()
        try:
            collect_once()
        except Exception:
            if args.once:
                raise
        if args.once:
            break
        elapsed = time.monotonic() - started
        time.sleep(max(0, settings.realtime_interval_seconds - elapsed))


if __name__ == "__main__":
    main()
