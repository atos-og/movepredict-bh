from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.services.gtfs_service import GtfsService
from app.services.sql_providers import SqlArrivalPredictionProvider, SqlVehiclePositionProvider


@lru_cache
def get_gtfs_service() -> GtfsService:
    return GtfsService(get_settings().gtfs_data_dir)


def get_vehicle_position_provider(
    session: Annotated[Session, Depends(get_db)],
) -> SqlVehiclePositionProvider:
    return SqlVehiclePositionProvider(session)


def get_arrival_prediction_provider(
    session: Annotated[Session, Depends(get_db)],
) -> SqlArrivalPredictionProvider:
    return SqlArrivalPredictionProvider(session)
