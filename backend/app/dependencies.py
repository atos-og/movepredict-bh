from functools import lru_cache

from app.config import get_settings
from app.services.gtfs_service import GtfsService


@lru_cache
def get_gtfs_service() -> GtfsService:
    return GtfsService(get_settings().gtfs_data_dir)
