from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import engine, get_db
from app.services.geocoding import NominatimGeocodingService
from app.services.gtfs_service import GtfsService
from app.services.journey_planner import OpenTripPlannerService
from app.services.service_alerts import GtfsRealtimeAlertsService
from app.services.sql_providers import SqlArrivalPredictionProvider, SqlVehiclePositionProvider


@lru_cache
def get_gtfs_service() -> GtfsService:
    return GtfsService(get_settings().gtfs_data_dir, engine=engine)


def get_vehicle_position_provider(
    session: Annotated[Session, Depends(get_db)],
) -> SqlVehiclePositionProvider:
    return SqlVehiclePositionProvider(session)


def get_arrival_prediction_provider(
    session: Annotated[Session, Depends(get_db)],
) -> SqlArrivalPredictionProvider:
    return SqlArrivalPredictionProvider(session)


@lru_cache
def get_geocoding_service() -> NominatimGeocodingService:
    settings = get_settings()
    return NominatimGeocodingService(
        settings.geocoding_url,
        settings.geocoding_user_agent,
        settings.geocoding_timeout_seconds,
        settings.geocoding_cache_seconds,
    )


@lru_cache
def get_journey_planner_service() -> OpenTripPlannerService:
    settings = get_settings()
    return OpenTripPlannerService(
        settings.journey_planner_url,
        settings.journey_planner_timeout_seconds,
    )


@lru_cache
def get_service_alerts_service() -> GtfsRealtimeAlertsService:
    settings = get_settings()
    return GtfsRealtimeAlertsService(
        settings.gtfs_rt_alerts_url,
        settings.realtime_timeout_seconds,
    )
