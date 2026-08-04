import asyncio
from dataclasses import dataclass
from time import monotonic

import httpx

from app.exceptions import GeocodingUnavailableError
from app.schemas.mobility import Coordinates, GeocodedDestination

BH_VIEWBOX = "-44.10,-19.75,-43.75,-20.05"


@dataclass
class GeocodingResult:
    destinations: list[GeocodedDestination]
    cached: bool


class NominatimGeocodingService:
    def __init__(
        self,
        base_url: str,
        user_agent: str,
        timeout_seconds: float,
        cache_seconds: int,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.user_agent = user_agent
        self.timeout_seconds = timeout_seconds
        self.cache_seconds = cache_seconds
        self._cache: dict[str, tuple[float, list[GeocodedDestination]]] = {}
        self._request_lock = asyncio.Lock()
        self._last_request_at = 0.0

    async def search(self, query: str, limit: int = 6) -> GeocodingResult:
        normalized = " ".join(query.casefold().split())
        cache_key = f"{normalized}:{limit}"
        cached = self._cache.get(cache_key)
        if cached and monotonic() - cached[0] < self.cache_seconds:
            return GeocodingResult(cached[1], cached=True)

        async with self._request_lock:
            cached = self._cache.get(cache_key)
            if cached and monotonic() - cached[0] < self.cache_seconds:
                return GeocodingResult(cached[1], cached=True)
            wait_seconds = 1.0 - (monotonic() - self._last_request_at)
            if wait_seconds > 0:
                await asyncio.sleep(wait_seconds)
            try:
                async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                    response = await client.get(
                        f"{self.base_url}/search",
                        params={
                            "q": f"{query.strip()}, Belo Horizonte, Minas Gerais",
                            "format": "jsonv2",
                            "addressdetails": 1,
                            "limit": limit,
                            "countrycodes": "br",
                            "viewbox": BH_VIEWBOX,
                            "bounded": 1,
                            "accept-language": "pt-BR",
                        },
                        headers={
                            "Accept": "application/json",
                            "User-Agent": self.user_agent,
                        },
                    )
                self._last_request_at = monotonic()
                response.raise_for_status()
                rows = response.json()
            except (httpx.HTTPError, ValueError) as error:
                raise GeocodingUnavailableError(
                    "A busca de enderecos esta temporariamente indisponivel."
                ) from error

            destinations = [_to_destination(row) for row in rows]
            self._cache[cache_key] = (monotonic(), destinations)
            if len(self._cache) > 256:
                oldest = min(self._cache, key=lambda key: self._cache[key][0])
                self._cache.pop(oldest, None)
            return GeocodingResult(destinations, cached=False)


def _to_destination(row: dict) -> GeocodedDestination:
    address = row.get("address") or {}
    label = (
        row.get("name")
        or address.get("attraction")
        or address.get("neighbourhood")
        or address.get("suburb")
        or str(row.get("display_name", "Destino")).split(",")[0]
    )
    place_type = str(row.get("type", ""))
    category = str(row.get("category", ""))
    if place_type in {"neighbourhood", "suburb", "quarter"}:
        kind = "neighborhood"
    elif place_type in {"house", "residential", "road"}:
        kind = "address"
    elif category in {"tourism", "amenity", "leisure", "historic"}:
        kind = "landmark"
    else:
        kind = "destination"
    return GeocodedDestination(
        id=str(row.get("place_id", f"{row.get('lat')}:{row.get('lon')}")),
        kind=kind,
        label=str(label),
        description=str(row.get("display_name", label)),
        coordinates=Coordinates(
            latitude=float(row["lat"]),
            longitude=float(row["lon"]),
        ),
    )
