from dataclasses import dataclass
from datetime import date, datetime, timedelta

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.models import VehiclePosition
from app.services.eta import SAO_PAULO


@dataclass(frozen=True)
class TripCandidate:
    trip_id: int
    gtfs_trip_id: str
    shape_distance_meters: float
    shape_progress: float
    schedule_delta_seconds: int
    confidence: float


@dataclass(frozen=True)
class MatchBatchResult:
    inspected: int
    matched: int
    rejected_no_candidate: int
    rejected_ambiguous: int


def match_unassigned_positions(
    session: Session,
    *,
    limit: int = 2_000,
    max_shape_distance_meters: float = 500,
    max_schedule_delta_seconds: int = 3 * 3600,
    min_confidence: float = 0.45,
    min_margin: float = 0.05,
) -> MatchBatchResult:
    positions = list(
        session.scalars(
            select(VehiclePosition)
            .where(
                VehiclePosition.trip_id.is_(None),
                VehiclePosition.route_id.is_not(None),
                VehiclePosition.trip_match_method.is_(None),
            )
            .order_by(VehiclePosition.observed_at.desc())
            .limit(limit)
        )
    )
    matched = no_candidate = ambiguous = 0
    for position in positions:
        candidates = find_trip_candidates(
            session,
            position,
            max_shape_distance_meters=max_shape_distance_meters,
            max_schedule_delta_seconds=max_schedule_delta_seconds,
        )
        if not candidates or candidates[0].confidence < min_confidence:
            position.trip_match_confidence = candidates[0].confidence if candidates else 0
            position.trip_match_method = "rejected-no-confident-candidate-v1"
            no_candidate += 1
            continue
        if len(candidates) > 1 and candidates[0].confidence - candidates[1].confidence < min_margin:
            position.trip_match_confidence = candidates[0].confidence
            position.trip_match_method = "rejected-ambiguous-candidate-v1"
            ambiguous += 1
            continue
        best = candidates[0]
        position.trip_id = best.trip_id
        position.shape_progress = best.shape_progress
        position.trip_match_confidence = best.confidence
        position.trip_match_method = "route-direction-calendar-time-shape-v1"
        matched += 1
    session.commit()
    return MatchBatchResult(len(positions), matched, no_candidate, ambiguous)


def find_trip_candidates(
    session: Session,
    position: VehiclePosition,
    *,
    max_shape_distance_meters: float,
    max_schedule_delta_seconds: int,
) -> list[TripCandidate]:
    local_time = position.observed_at.astimezone(SAO_PAULO)
    contexts = (
        (local_time.date(), _seconds_since_midnight(local_time)),
        (local_time.date() - timedelta(days=1), _seconds_since_midnight(local_time) + 86_400),
    )
    direction_id = _gtfs_direction(position.direction_code)
    candidates: dict[int, TripCandidate] = {}
    for service_date, service_seconds in contexts:
        for row in _candidate_rows(
            session,
            position=position,
            service_date=service_date,
            service_seconds=service_seconds,
            direction_id=direction_id,
            max_shape_distance_meters=max_shape_distance_meters,
            max_schedule_delta_seconds=max_schedule_delta_seconds,
        ):
            confidence = _confidence(
                row["shape_distance_meters"],
                row["schedule_delta_seconds"],
                max_shape_distance_meters,
                max_schedule_delta_seconds,
            )
            candidate = TripCandidate(
                trip_id=row["trip_id"],
                gtfs_trip_id=row["gtfs_trip_id"],
                shape_distance_meters=row["shape_distance_meters"],
                shape_progress=row["shape_progress"],
                schedule_delta_seconds=row["schedule_delta_seconds"],
                confidence=confidence,
            )
            current = candidates.get(candidate.trip_id)
            if current is None or candidate.confidence > current.confidence:
                candidates[candidate.trip_id] = candidate
    return sorted(candidates.values(), key=lambda candidate: candidate.confidence, reverse=True)


def _candidate_rows(
    session: Session,
    *,
    position: VehiclePosition,
    service_date: date,
    service_seconds: int,
    direction_id: int | None,
    max_shape_distance_meters: float,
    max_schedule_delta_seconds: int,
):
    weekday = service_date.strftime("%A").lower()
    if weekday not in _WEEKDAYS:
        raise ValueError("Dia da semana inválido.")
    direction_filter = "" if direction_id is None else "AND t.direction_id = :direction_id"
    statement = text(
        f"""
        WITH candidate AS (
            SELECT
                t.id AS trip_id,
                t.gtfs_trip_id,
                ABS(t.start_time_seconds - :service_seconds)::integer AS schedule_delta_seconds,
                ST_Distance(
                    sh.path::geography,
                    ST_SetSRID(ST_MakePoint(:longitude, :latitude), 4326)::geography
                ) AS shape_distance_meters,
                ST_LineLocatePoint(
                    sh.path,
                    ST_SetSRID(ST_MakePoint(:longitude, :latitude), 4326)
                ) AS shape_progress
            FROM transit_trips AS t
            JOIN transit_shapes AS sh ON sh.gtfs_shape_id = t.shape_id
            WHERE t.route_id = :route_id
              {direction_filter}
              AND t.start_time_seconds IS NOT NULL
              AND ABS(t.start_time_seconds - :service_seconds) <= :max_schedule_delta
              AND (
                    EXISTS (
                        SELECT 1 FROM service_exceptions AS se
                        WHERE se.service_id = t.service_id
                          AND se.service_date = :service_date
                          AND se.exception_type = 1
                    )
                    OR (
                        EXISTS (
                            SELECT 1 FROM service_calendars AS sc
                            WHERE sc.service_id = t.service_id
                              AND :service_date BETWEEN sc.start_date AND sc.end_date
                              AND sc.{weekday} = TRUE
                        )
                        AND NOT EXISTS (
                            SELECT 1 FROM service_exceptions AS se
                            WHERE se.service_id = t.service_id
                              AND se.service_date = :service_date
                              AND se.exception_type = 2
                        )
                    )
              )
        )
        SELECT * FROM candidate
        WHERE shape_distance_meters <= :max_shape_distance
        ORDER BY shape_distance_meters, schedule_delta_seconds
        LIMIT 8
        """
    )
    return session.execute(
        statement,
        {
            "service_seconds": service_seconds,
            "longitude": position.longitude,
            "latitude": position.latitude,
            "route_id": position.route_id,
            "direction_id": direction_id,
            "service_date": service_date,
            "max_schedule_delta": max_schedule_delta_seconds,
            "max_shape_distance": max_shape_distance_meters,
        },
    ).mappings()


def _confidence(
    shape_distance: float,
    schedule_delta: int,
    max_shape_distance: float,
    max_schedule_delta: int,
) -> float:
    spatial = max(0.0, 1 - shape_distance / max_shape_distance)
    temporal = max(0.0, 1 - schedule_delta / max_schedule_delta)
    return round(spatial * 0.65 + temporal * 0.35, 6)


def _seconds_since_midnight(value: datetime) -> int:
    return value.hour * 3600 + value.minute * 60 + value.second


def _gtfs_direction(source_direction: int | None) -> int | None:
    return {1: 0, 2: 1}.get(source_direction)


_WEEKDAYS = {
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
}
