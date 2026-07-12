from dataclasses import dataclass
from datetime import timedelta

from sqlalchemy import select, text, update
from sqlalchemy.orm import Session

from app.models import ArrivalEvent, ArrivalPrediction, TransitTrip, VehiclePosition
from app.services.eta import SAO_PAULO


@dataclass(frozen=True)
class ArrivalDetectionResult:
    inspected: int
    detected: int
    predictions_labeled: int


def detect_arrivals(
    session: Session,
    *,
    limit: int = 2_000,
    radius_meters: float = 45,
    max_speed_kmh: float = 15,
) -> ArrivalDetectionResult:
    positions = list(
        session.scalars(
            select(VehiclePosition)
            .outerjoin(ArrivalEvent, ArrivalEvent.position_id == VehiclePosition.id)
            .where(
                VehiclePosition.trip_id.is_not(None),
                VehiclePosition.shape_progress.is_not(None),
                ArrivalEvent.id.is_(None),
                (VehiclePosition.speed_kmh.is_(None))
                | (VehiclePosition.speed_kmh <= max_speed_kmh),
            )
            .order_by(VehiclePosition.observed_at)
            .limit(limit)
        )
    )
    detected = labeled = 0
    for position in positions:
        nearest = _nearest_stop(session, position, radius_meters)
        if nearest is None or not _is_arrival(session, position, nearest):
            continue
        service_date = _service_date(session, position)
        exists = session.scalar(
            select(ArrivalEvent.id).where(
                ArrivalEvent.vehicle_id == position.vehicle_id,
                ArrivalEvent.trip_id == position.trip_id,
                ArrivalEvent.stop_id == nearest["stop_id"],
                ArrivalEvent.service_date == service_date,
            )
        )
        if exists:
            continue
        session.add(
            ArrivalEvent(
                vehicle_id=position.vehicle_id,
                route_id=position.route_id,
                trip_id=position.trip_id,
                stop_id=nearest["stop_id"],
                position_id=position.id,
                service_date=service_date,
                arrived_at=position.observed_at,
                distance_to_stop_meters=nearest["distance_meters"],
                detection_method="proximity-approach-low-speed-v1",
            )
        )
        result = session.execute(
            update(ArrivalPrediction)
            .where(
                ArrivalPrediction.vehicle_id == position.vehicle_id,
                ArrivalPrediction.trip_id == position.trip_id,
                ArrivalPrediction.stop_id == nearest["stop_id"],
                ArrivalPrediction.actual_arrival.is_(None),
                ArrivalPrediction.generated_at <= position.observed_at,
                ArrivalPrediction.generated_at >= position.observed_at - timedelta(hours=2),
            )
            .values(actual_arrival=position.observed_at)
        )
        labeled += result.rowcount or 0
        detected += 1
    session.commit()
    return ArrivalDetectionResult(len(positions), detected, labeled)


def _nearest_stop(session: Session, position: VehiclePosition, radius: float):
    return (
        session.execute(
            text(
                """
            SELECT
                ts.stop_id,
                ts.stop_sequence,
                ST_Distance(st.location, vp.location) AS distance_meters
            FROM trip_stops AS ts
            JOIN transit_stops AS st ON st.id = ts.stop_id
            JOIN vehicle_positions AS vp ON vp.id = :position_id
            WHERE ts.trip_id = :trip_id
              AND ts.shape_progress BETWEEN :progress - 0.02 AND :progress + 0.02
              AND ST_DWithin(st.location, vp.location, :radius)
            ORDER BY distance_meters
            LIMIT 1
            """
            ),
            {
                "position_id": position.id,
                "trip_id": position.trip_id,
                "progress": position.shape_progress,
                "radius": radius,
            },
        )
        .mappings()
        .first()
    )


def _is_arrival(session: Session, position: VehiclePosition, stop) -> bool:
    previous = (
        session.execute(
            text(
                """
            SELECT ST_Distance(st.location, vp.location) AS distance_meters
            FROM vehicle_positions AS vp
            JOIN transit_stops AS st ON st.id = :stop_id
            WHERE vp.vehicle_id = :vehicle_id
              AND vp.trip_id = :trip_id
              AND vp.observed_at < :observed_at
            ORDER BY vp.observed_at DESC
            LIMIT 1
            """
            ),
            {
                "stop_id": stop["stop_id"],
                "vehicle_id": position.vehicle_id,
                "trip_id": position.trip_id,
                "observed_at": position.observed_at,
            },
        )
        .mappings()
        .first()
    )
    if previous is None:
        return (position.speed_kmh or 0) <= 2
    return previous["distance_meters"] > stop["distance_meters"]


def _service_date(session: Session, position: VehiclePosition):
    local = position.observed_at.astimezone(SAO_PAULO)
    trip = session.get(TransitTrip, position.trip_id)
    local_seconds = local.hour * 3600 + local.minute * 60 + local.second
    if trip and trip.start_time_seconds and trip.start_time_seconds >= 86_400:
        if local_seconds < 12 * 3600:
            return local.date() - timedelta(days=1)
    return local.date()
