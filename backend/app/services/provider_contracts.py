from datetime import datetime
from typing import Protocol

from app.schemas.realtime import ArrivalPrediction, VehiclePosition


class VehiclePositionProvider(Protocol):
    def list_current_positions(self, route_id: str | None = None) -> list[VehiclePosition]: ...


class ArrivalPredictionProvider(Protocol):
    def predict_arrivals(
        self,
        stop_id: str,
        route_id: str | None = None,
        at: datetime | None = None,
    ) -> list[ArrivalPrediction]: ...
