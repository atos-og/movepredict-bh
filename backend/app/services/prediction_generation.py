from dataclasses import dataclass
from datetime import timedelta

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.models import ArrivalPrediction, Vehicle, VehiclePosition

MODEL_VERSION = "baseline-shape-speed-v1"


@dataclass(frozen=True)
class PredictionGenerationResult:
    vehicles: int
    predictions: int


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
    created = 0
    route_speeds: dict[int, float] = {}
    for position in positions:
        speed = position.speed_kmh if position.speed_kmh and position.speed_kmh >= 5 else None
        if speed is None:
            speed = route_speeds.get(position.route_id)
            if speed is None:
                speed = _recent_route_speed(session, position.route_id) or fallback_speed_kmh
                route_speeds[position.route_id] = speed
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
            seconds = round(distance / (speed / 3.6))
            uncertainty = max(60, round(seconds * 0.35))
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
                )
            )
            created += 1
    session.commit()
    return PredictionGenerationResult(len(positions), created)


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


def _recent_route_speed(session: Session, route_id: int) -> float | None:
    return session.scalar(
        select(func.avg(VehiclePosition.speed_kmh)).where(
            VehiclePosition.route_id == route_id,
            VehiclePosition.speed_kmh >= 5,
            VehiclePosition.observed_at >= func.now() - timedelta(minutes=30),
        )
    )
