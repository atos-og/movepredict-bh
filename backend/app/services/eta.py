import math
import statistics
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    ArrivalPrediction,
    TransitRoute,
    TransitStop,
    TransitTrip,
    TripStop,
    VehiclePosition,
)

SAO_PAULO = ZoneInfo("America/Sao_Paulo")


@dataclass(frozen=True)
class EvaluationRecord:
    predicted: datetime
    actual: datetime
    generated_at: datetime
    route_id: str
    distance_meters: float | None


@dataclass(frozen=True)
class PredictionMetrics:
    count: int
    mae_seconds: float
    median_seconds: float
    p90_seconds: float
    p95_seconds: float


def haversine_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6_371_000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    value = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    return radius * 2 * math.atan2(math.sqrt(value), math.sqrt(1 - value))


def estimate_arrival(
    *,
    observed_at: datetime,
    vehicle_latitude: float,
    vehicle_longitude: float,
    stop_latitude: float,
    stop_longitude: float,
    speed_kmh: float | None,
    fallback_speed_kmh: float = 18.0,
) -> tuple[datetime, int]:
    distance = haversine_meters(vehicle_latitude, vehicle_longitude, stop_latitude, stop_longitude)
    effective_speed = speed_kmh if speed_kmh and speed_kmh >= 5 else fallback_speed_kmh
    seconds = round(distance / (effective_speed / 3.6))
    uncertainty = max(60, round(seconds * 0.35))
    return observed_at + timedelta(seconds=seconds), uncertainty


def mean_absolute_error_seconds(
    pairs: list[tuple[datetime, datetime]],
) -> float | None:
    if not pairs:
        return None
    return sum(abs((predicted - actual).total_seconds()) for predicted, actual in pairs) / len(
        pairs
    )


def create_baseline_prediction(
    session: Session, *, vehicle_position_id: int, stop_id: int
) -> ArrivalPrediction:
    position = session.get(VehiclePosition, vehicle_position_id)
    stop = session.get(TransitStop, stop_id)
    if position is None or stop is None:
        raise ValueError("Posição ou ponto inexistente.")
    if position.route_id is None:
        raise ValueError("A posição ainda não está relacionada a uma linha GTFS.")
    predicted, uncertainty = estimate_arrival(
        observed_at=position.observed_at,
        vehicle_latitude=position.latitude,
        vehicle_longitude=position.longitude,
        stop_latitude=stop.latitude,
        stop_longitude=stop.longitude,
        speed_kmh=position.speed_kmh,
    )
    prediction = ArrivalPrediction(
        stop_id=stop.id,
        route_id=position.route_id,
        trip_id=position.trip_id,
        vehicle_id=position.vehicle_id,
        generated_at=position.observed_at,
        predicted_arrival=predicted,
        distance_to_stop_meters=haversine_meters(
            position.latitude, position.longitude, stop.latitude, stop.longitude
        ),
        uncertainty_seconds=uncertainty,
        model_version="baseline-haversine-v1",
    )
    session.add(prediction)
    session.commit()
    session.refresh(prediction)
    return prediction


def create_scheduled_prediction(
    session: Session,
    *,
    trip_stop_id: int,
    service_date: date,
    generated_at: datetime | None = None,
    vehicle_id: int | None = None,
) -> ArrivalPrediction:
    trip_stop = session.get(TripStop, trip_stop_id)
    if trip_stop is None or trip_stop.scheduled_arrival_seconds is None:
        raise ValueError("Parada programada inexistente ou sem horário de chegada.")
    generated_at = (generated_at or datetime.now(UTC)).astimezone(UTC)
    predicted_arrival = scheduled_datetime_utc(service_date, trip_stop.scheduled_arrival_seconds)
    if predicted_arrival < generated_at:
        raise ValueError("O horário programado já ocorreu.")
    route_id = session.scalar(
        select(TransitTrip.route_id).where(TransitTrip.id == trip_stop.trip_id)
    )
    if route_id is None:
        raise ValueError("Viagem sem linha relacionada.")
    prediction = ArrivalPrediction(
        stop_id=trip_stop.stop_id,
        route_id=route_id,
        trip_id=trip_stop.trip_id,
        vehicle_id=vehicle_id,
        generated_at=generated_at,
        predicted_arrival=predicted_arrival,
        uncertainty_seconds=300,
        model_version="baseline-schedule-v1",
    )
    session.add(prediction)
    session.commit()
    session.refresh(prediction)
    return prediction


def scheduled_datetime_utc(service_date: date, seconds_after_midnight: int) -> datetime:
    local_midnight = datetime.combine(service_date, time.min, tzinfo=SAO_PAULO)
    return (local_midnight + timedelta(seconds=seconds_after_midnight)).astimezone(UTC)


def evaluate_saved_predictions(
    session: Session, model_version: str = "baseline-haversine-v1"
) -> tuple[int, float | None]:
    pairs = list(
        session.execute(
            select(ArrivalPrediction.predicted_arrival, ArrivalPrediction.actual_arrival).where(
                ArrivalPrediction.model_version == model_version,
                ArrivalPrediction.actual_arrival.is_not(None),
            )
        )
    )
    return len(pairs), mean_absolute_error_seconds(pairs)


def load_evaluation_records(session: Session, model_version: str) -> list[EvaluationRecord]:
    rows = session.execute(
        select(ArrivalPrediction, TransitRoute)
        .join(TransitRoute, TransitRoute.id == ArrivalPrediction.route_id)
        .where(
            ArrivalPrediction.model_version == model_version,
            ArrivalPrediction.actual_arrival.is_not(None),
        )
        .order_by(ArrivalPrediction.generated_at)
    )
    return [
        EvaluationRecord(
            predicted=prediction.predicted_arrival.astimezone(UTC),
            actual=prediction.actual_arrival.astimezone(UTC),
            generated_at=prediction.generated_at.astimezone(UTC),
            route_id=route.gtfs_route_id or str(route.id),
            distance_meters=prediction.distance_to_stop_meters,
        )
        for prediction, route in rows
    ]


def temporal_split(
    records: list[EvaluationRecord], validation_fraction: float = 0.2
) -> tuple[list[EvaluationRecord], list[EvaluationRecord]]:
    if not 0 < validation_fraction < 1:
        raise ValueError("validation_fraction deve estar entre 0 e 1.")
    ordered = sorted(records, key=lambda record: record.generated_at)
    if len(ordered) < 2:
        return ordered, []
    validation_size = max(1, math.ceil(len(ordered) * validation_fraction))
    return ordered[:-validation_size], ordered[-validation_size:]


def calculate_metrics(records: list[EvaluationRecord]) -> PredictionMetrics | None:
    if not records:
        return None
    errors = sorted(abs((record.predicted - record.actual).total_seconds()) for record in records)
    return PredictionMetrics(
        count=len(errors),
        mae_seconds=sum(errors) / len(errors),
        median_seconds=statistics.median(errors),
        p90_seconds=_percentile(errors, 0.90),
        p95_seconds=_percentile(errors, 0.95),
    )


def segmented_metrics(records: list[EvaluationRecord]) -> dict[str, dict[str, PredictionMetrics]]:
    groups: dict[str, dict[str, list[EvaluationRecord]]] = {
        "route": {},
        "hour": {},
        "distance": {},
    }
    for record in records:
        groups["route"].setdefault(record.route_id, []).append(record)
        local_hour = str(record.generated_at.astimezone(SAO_PAULO).hour)
        groups["hour"].setdefault(local_hour, []).append(record)
        groups["distance"].setdefault(_distance_bucket(record.distance_meters), []).append(record)
    return {
        dimension: {
            key: metrics
            for key, values in dimension_groups.items()
            if (metrics := calculate_metrics(values)) is not None
        }
        for dimension, dimension_groups in groups.items()
    }


def _distance_bucket(distance: float | None) -> str:
    if distance is None:
        return "unknown"
    if distance < 500:
        return "0-499m"
    if distance < 2_000:
        return "500-1999m"
    return "2000m+"


def _percentile(values: list[float], percentile: float) -> float:
    if len(values) == 1:
        return values[0]
    position = (len(values) - 1) * percentile
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return values[lower]
    weight = position - lower
    return values[lower] * (1 - weight) + values[upper] * weight
