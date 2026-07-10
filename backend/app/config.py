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

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
