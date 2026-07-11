from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


def default_gtfs_data_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "data-exploration" / "data" / "raw"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="MOVEPREDICT_",
        extra="ignore",
    )

    app_name: str = "MovePredict BH API"
    environment: str = "development"
    gtfs_data_dir: Path = default_gtfs_data_dir()
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    database_url: str = "postgresql+psycopg://movepredict:movepredict@localhost:5432/movepredict"
    realtime_positions_url: str = "https://temporeal.pbh.gov.br/?param=D"
    realtime_line_mapping_url: str = (
        "https://ckan.pbh.gov.br/dataset/730aaa4b-d14c-4755-aed6-433cb0ad9430/"
        "resource/150bddd0-9a2c-4731-ade9-54aa56717fb6/download/bhtrans_bdlinha.csv"
    )
    realtime_interval_seconds: int = 20
    realtime_timeout_seconds: float = 15.0
    realtime_max_retries: int = 4
    realtime_backoff_seconds: float = 1.0
    realtime_disappearance_seconds: int = 120
    trip_match_batch_size: int = 250
    arrival_detection_batch_size: int = 2_000
    position_retention_days: int = 90
    position_retention_batch_size: int = 50_000

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
