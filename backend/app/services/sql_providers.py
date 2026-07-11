from datetime import UTC, datetime

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session, aliased

from app.models import (
    ArrivalPrediction as ArrivalPredictionRecord,
)
from app.models import (
    TransitRoute,
    TransitStop,
    TransitTrip,
    Vehicle,
)
from app.models import (
    VehiclePosition as VehiclePositionRecord,
)
from app.schemas.realtime import ArrivalPrediction, VehiclePosition


class SqlVehiclePositionProvider:
    """Adaptador SQL para o contrato público VehiclePositionProvider."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def list_current_positions(self, route_id: str | None = None) -> list[VehiclePosition]:
        latest = (
            select(
                VehiclePositionRecord.vehicle_id,
                func.max(VehiclePositionRecord.observed_at).label("observed_at"),
            )
            .group_by(VehiclePositionRecord.vehicle_id)
            .subquery()
        )
        route = aliased(TransitRoute)
        trip = aliased(TransitTrip)
        statement = (
            select(VehiclePositionRecord, Vehicle, route, trip)
            .join(
                latest,
                and_(
                    latest.c.vehicle_id == VehiclePositionRecord.vehicle_id,
                    latest.c.observed_at == VehiclePositionRecord.observed_at,
                ),
            )
            .join(Vehicle, Vehicle.id == VehiclePositionRecord.vehicle_id)
            .outerjoin(route, route.id == VehiclePositionRecord.route_id)
            .outerjoin(trip, trip.id == VehiclePositionRecord.trip_id)
            .where(Vehicle.is_active.is_(True))
        )
        if route_id is not None:
            statement = statement.where(route.gtfs_route_id == route_id)
        rows = self.session.execute(statement).all()
        return [
            VehiclePosition(
                vehicle_id=vehicle.source_vehicle_id,
                route_id=route_record.gtfs_route_id if route_record else None,
                trip_id=trip_record.gtfs_trip_id if trip_record else None,
                latitude=position.latitude,
                longitude=position.longitude,
                bearing=position.bearing,
                speed_kmh=position.speed_kmh,
                observed_at=position.observed_at.astimezone(UTC),
                status=_vehicle_status(position.speed_kmh),
            )
            for position, vehicle, route_record, trip_record in rows
        ]


class SqlArrivalPredictionProvider:
    """Adaptador SQL para o contrato público ArrivalPredictionProvider."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def predict_arrivals(
        self,
        stop_id: str,
        route_id: str | None = None,
        at: datetime | None = None,
    ) -> list[ArrivalPrediction]:
        at = (at or datetime.now(UTC)).astimezone(UTC)
        statement = (
            select(
                ArrivalPredictionRecord,
                TransitStop,
                TransitRoute,
                TransitTrip,
                Vehicle,
            )
            .join(TransitStop, TransitStop.id == ArrivalPredictionRecord.stop_id)
            .join(TransitRoute, TransitRoute.id == ArrivalPredictionRecord.route_id)
            .outerjoin(TransitTrip, TransitTrip.id == ArrivalPredictionRecord.trip_id)
            .outerjoin(Vehicle, Vehicle.id == ArrivalPredictionRecord.vehicle_id)
            .where(
                TransitStop.gtfs_stop_id == stop_id,
                ArrivalPredictionRecord.predicted_arrival >= at,
            )
            .order_by(ArrivalPredictionRecord.predicted_arrival)
        )
        if route_id is not None:
            statement = statement.where(TransitRoute.gtfs_route_id == route_id)
        return [
            ArrivalPrediction(
                stop_id=stop.gtfs_stop_id,
                route_id=route.gtfs_route_id,
                trip_id=trip.gtfs_trip_id if trip else None,
                vehicle_id=vehicle.source_vehicle_id if vehicle else None,
                predicted_arrival=prediction.predicted_arrival.astimezone(UTC),
                generated_at=prediction.generated_at.astimezone(UTC),
                uncertainty_seconds=prediction.uncertainty_seconds,
                model_version=prediction.model_version,
            )
            for prediction, stop, route, trip, vehicle in self.session.execute(statement)
        ]


def _vehicle_status(speed_kmh: float | None) -> str:
    if speed_kmh is None:
        return "unknown"
    return "stopped" if speed_kmh <= 1 else "in_transit"
