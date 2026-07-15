from dataclasses import dataclass
from datetime import timedelta

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.models import ArrivalPrediction, RouteHourSpeedStat, Vehicle, VehiclePosition
from app.services.eta import SAO_PAULO

MODEL_VERSION = "baseline-shape-speed-v1"


@dataclass(frozen=True)
class PredictionGenerationResult:
    vehicles: int
    predictions: int
    realtime_speed: int = 0
    historical_speed: int = 0
    fallback_speed: int = 0


@dataclass(frozen=True)
class SpeedEstimate:
    speed_kmh: float
    basis: str
    sample_size: int


def generate_predictions(
    session: Session,
    *,
    stops_per_vehicle: int = 3,
    fallback_speed_kmh: float = 18,
) -> PredictionGenerationResult:
    latest = (
        select(
            VehiclePosition.vehicle_id,
            func.max(VehiclePosition.observed_at).label("observed_at"),
        )
        .where(VehiclePosition.trip_id.is_not(None))
        .group_by(VehiclePosition.vehicle_id)
        .subquery()
    )
    positions = list(
        session.scalars(
            select(VehiclePosition)
            .join(
                latest,
                (latest.c.vehicle_id == VehiclePosition.vehicle_id)
                & (latest.c.observed_at == VehiclePosition.observed_at),
            )
            .join(Vehicle, Vehicle.id == VehiclePosition.vehicle_id)
            .where(Vehicle.is_active.is_(True), VehiclePosition.shape_progress.is_not(None))
        )
    )
    created = realtime_count = historical_count = fallback_count = 0
    route_speeds = _historical_speed_cache(session, positions)
    for position in positions:
        estimate = _speed_estimate(
            position,
            route_speeds,
            fallback_speed_kmh=fallback_speed_kmh,
        )
        if estimate.basis == "realtime-speed":
            realtime_count += 1
        elif estimate.basis == "historical-route-hour":
            historical_count += 1
        else:
            fallback_count += 1
        for stop in _upcoming_stops(session, position, stops_per_vehicle):
            exists = session.scalar(
                select(ArrivalPrediction.id).where(
                    ArrivalPrediction.vehicle_id == position.vehicle_id,
                    ArrivalPrediction.stop_id == stop["stop_id"],
                    ArrivalPrediction.generated_at == position.ingested_at,
                    ArrivalPrediction.model_version == MODEL_VERSION,
                )
            )
            if exists:
                continue
            distance = max(0.0, stop["distance_meters"])
            seconds = round(distance / (estimate.speed_kmh / 3.6))
            uncertainty_factor = 0.35 if estimate.basis == "realtime-speed" else 0.5
            if estimate.basis == "fixed-insufficient-history":
                uncertainty_factor = 0.75
            uncertainty = max(60, round(seconds * uncertainty_factor))
            session.add(
                ArrivalPrediction(
                    stop_id=stop["stop_id"],
                    route_id=position.route_id,
                    trip_id=position.trip_id,
                    vehicle_id=position.vehicle_id,
                    generated_at=position.ingested_at,
                    predicted_arrival=position.ingested_at + timedelta(seconds=seconds),
                    distance_to_stop_meters=distance,
                    uncertainty_seconds=uncertainty,
                    model_version=MODEL_VERSION,
                    prediction_basis=estimate.basis,
                    sample_size=estimate.sample_size,
                    horizon_seconds=seconds,
                )
            )
            created += 1
    session.commit()
    return PredictionGenerationResult(
        len(positions), created, realtime_count, historical_count, fallback_count
    )


def _upcoming_stops(session: Session, position: VehiclePosition, limit: int):
    return session.execute(
        text(
            """
            SELECT
                ts.stop_id,
                GREATEST(0, (ts.shape_progress - :progress) * sh.length_meters)
                    AS distance_meters
            FROM trip_stops AS ts
            JOIN transit_trips AS t ON t.id = ts.trip_id
            JOIN transit_shapes AS sh ON sh.gtfs_shape_id = t.shape_id
            WHERE ts.trip_id = :trip_id
              AND ts.shape_progress > :progress + 0.0001
            ORDER BY ts.shape_progress
            LIMIT :limit
            """
        ),
        {"trip_id": position.trip_id, "progress": position.shape_progress, "limit": limit},
    ).mappings()


def _speed_estimate(
    position: VehiclePosition,
    cache: dict[tuple[int, int], SpeedEstimate],
    *,
    fallback_speed_kmh: float,
) -> SpeedEstimate:
    if position.speed_kmh and position.speed_kmh >= 5:
        return SpeedEstimate(position.speed_kmh, "realtime-speed", 1)
    local_hour = position.observed_at.astimezone(SAO_PAULO).hour
    key = (position.route_id, local_hour)
    historical = cache.get(key)
    if historical and historical.sample_size >= 30:
        return historical
    return SpeedEstimate(
        fallback_speed_kmh,
        "fixed-insufficient-history",
        historical.sample_size if historical else 0,
    )


def _historical_speed_cache(
    session: Session, positions: list[VehiclePosition]
) -> dict[tuple[int, int], SpeedEstimate]:
    if not positions:
        return {}
    route_ids = {position.route_id for position in positions if position.route_id is not None}
    rows = session.execute(
        select(RouteHourSpeedStat).where(RouteHourSpeedStat.route_id.in_(route_ids))
    ).scalars()
    return {
        (row.route_id, row.local_hour): SpeedEstimate(
            row.average_speed_kmh, "historical-route-hour", row.sample_size
        )
        for row in rows
    }
