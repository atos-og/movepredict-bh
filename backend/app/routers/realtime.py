from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.dependencies import get_arrival_prediction_provider, get_vehicle_position_provider
from app.schemas.common import ErrorResponse
from app.schemas.realtime import (
    ArrivalPredictionResponse,
    RealtimeMeta,
    VehiclePositionResponse,
)
from app.services.sql_providers import SqlArrivalPredictionProvider, SqlVehiclePositionProvider

router = APIRouter(prefix="/realtime", tags=["realtime"])
VehicleProvider = Annotated[SqlVehiclePositionProvider, Depends(get_vehicle_position_provider)]
ArrivalProvider = Annotated[SqlArrivalPredictionProvider, Depends(get_arrival_prediction_provider)]


@router.get(
    "/vehicles",
    response_model=VehiclePositionResponse,
    responses={503: {"model": ErrorResponse}},
)
def list_current_vehicles(
    provider: VehicleProvider,
    route_id: str | None = Query(default=None, min_length=1, max_length=100),
    limit: int = Query(default=500, ge=1, le=2_000),
    max_age_seconds: int = Query(default=120, ge=10, le=3_600),
) -> VehiclePositionResponse:
    now = datetime.now(UTC)
    cutoff = now - timedelta(seconds=max_age_seconds)
    candidates = provider.list_current_positions(route_id)
    newest = max((position.observed_at for position in candidates), default=None)
    positions = [position for position in candidates if position.observed_at >= cutoff][:limit]
    status = "stale" if newest is not None and newest < cutoff else "live" if positions else "empty"
    return VehiclePositionResponse(
        data=positions,
        meta=RealtimeMeta(
            generated_at=now,
            count=len(positions),
            status=status,
            stale=status == "stale",
            stale_after_seconds=max_age_seconds,
        ),
    )


@router.get(
    "/stops/{stop_id}/arrivals",
    response_model=ArrivalPredictionResponse,
    responses={503: {"model": ErrorResponse}},
)
def list_stop_arrivals(
    stop_id: str,
    provider: ArrivalProvider,
    route_id: str | None = Query(default=None, min_length=1, max_length=100),
    limit: int = Query(default=20, ge=1, le=100),
    max_age_seconds: int = Query(default=180, ge=10, le=3_600),
) -> ArrivalPredictionResponse:
    now = datetime.now(UTC)
    predictions = provider.predict_arrivals(stop_id, route_id=route_id, at=now)[:limit]
    newest = max((prediction.generated_at for prediction in predictions), default=None)
    status = (
        "stale"
        if newest is not None and newest < now - timedelta(seconds=max_age_seconds)
        else "live"
        if predictions
        else "empty"
    )
    return ArrivalPredictionResponse(
        data=predictions,
        meta=RealtimeMeta(
            generated_at=now,
            count=len(predictions),
            status=status,
            stale=status == "stale",
            stale_after_seconds=max_age_seconds,
        ),
    )
