import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import httpx

PBH_TIMEZONE = ZoneInfo("America/Sao_Paulo")


@dataclass(frozen=True)
class PbhVehiclePosition:
    vehicle_id: str
    observed_at: datetime
    latitude: float
    longitude: float
    speed_kmh: float | None
    bearing: float | None
    source_line_code: str | None
    direction_code: int | None
    distance_traveled: float | None
    event_code: str


def parse_position(row: dict[str, str]) -> PbhVehiclePosition:
    observed_at = (
        datetime.strptime(row["HR"], "%Y%m%d%H%M%S").replace(tzinfo=PBH_TIMEZONE).astimezone(UTC)
    )
    latitude = float(row["LT"].replace(",", "."))
    longitude = float(row["LG"].replace(",", "."))
    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        raise ValueError("Coordenadas fora dos limites WGS84.")
    return PbhVehiclePosition(
        vehicle_id=row["NV"].strip(),
        observed_at=observed_at,
        latitude=latitude,
        longitude=longitude,
        speed_kmh=_optional_float(row.get("VL")),
        bearing=_optional_float(row.get("DG")),
        source_line_code=_optional_text(row.get("NL")),
        direction_code=_optional_int(row.get("SV")),
        distance_traveled=_optional_float(row.get("DT")),
        event_code=row.get("EV", "105"),
    )


class PbhRealtimeClient:
    def __init__(
        self,
        url: str,
        *,
        timeout: float = 15.0,
        max_retries: int = 4,
        backoff_seconds: float = 1.0,
        max_future_seconds: int = 300,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.url = url
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_seconds = backoff_seconds
        self.max_future_seconds = max_future_seconds
        self.transport = transport
        self.last_attempt_count = 0
        self.last_http_status: int | None = None
        self.last_fetched_count = 0
        self.last_parse_error_count = 0

    def fetch_positions(self) -> list[PbhVehiclePosition]:
        response = self._get_with_retry()
        payload = response.json()
        if not isinstance(payload, list):
            raise ValueError("O feed da PBH não retornou uma lista JSON.")
        self.last_fetched_count = len(payload)
        positions = []
        future_cutoff = datetime.now(UTC) + timedelta(seconds=self.max_future_seconds)
        for row in payload:
            if row.get("EV") != "105":
                continue
            try:
                position = parse_position(row)
                if position.observed_at > future_cutoff:
                    raise ValueError("Posição com horário futuro além da tolerância.")
                positions.append(position)
            except (KeyError, TypeError, ValueError):
                self.last_parse_error_count += 1
        return positions

    def _get_with_retry(self) -> httpx.Response:
        attempts = max(1, self.max_retries + 1)
        with httpx.Client(
            timeout=self.timeout,
            follow_redirects=True,
            headers={
                "User-Agent": "MovePredict-BH/0.1 (+https://github.com/atos-og/movepredict-bh)"
            },
            transport=self.transport,
        ) as client:
            for attempt in range(1, attempts + 1):
                self.last_attempt_count = attempt
                try:
                    response = client.get(self.url)
                    self.last_http_status = response.status_code
                    if response.status_code < 400:
                        return response
                    if response.status_code not in {408, 425, 429} and response.status_code < 500:
                        response.raise_for_status()
                    if attempt == attempts:
                        response.raise_for_status()
                except httpx.RequestError:
                    if attempt == attempts:
                        raise
                time.sleep(self.backoff_seconds * (2 ** (attempt - 1)))
        raise RuntimeError("Tentativas de coleta esgotadas.")


def _optional_text(value: str | None) -> str | None:
    return value.strip() if value and value.strip() else None


def _optional_float(value: str | None) -> float | None:
    text = _optional_text(value)
    return float(text.replace(",", ".")) if text is not None else None


def _optional_int(value: str | None) -> int | None:
    text = _optional_text(value)
    return int(text) if text is not None else None
