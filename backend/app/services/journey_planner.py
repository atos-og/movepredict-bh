from datetime import UTC, datetime
from typing import Literal

import httpx

from app.exceptions import JourneyPlannerUnavailableError
from app.schemas.mobility import (
    Coordinates,
    JourneyPlan,
    JourneyStep,
    JourneyStop,
)

JourneyPreference = Literal["quickest", "less_walking", "fewer_transfers"]

PLAN_QUERY = """
query PlanJourney(
  $from: InputCoordinates!
  $to: InputCoordinates!
  $numItineraries: Int!
  $transferPenalty: Int!
  $walkReluctance: Float!
) {
  plan(
    from: $from
    to: $to
    numItineraries: $numItineraries
    maxTransfers: 2
    transferPenalty: $transferPenalty
    walkReluctance: $walkReluctance
    locale: "pt"
  ) {
    itineraries {
      duration
      start
      end
      walkTime
      walkDistance
      numberOfTransfers
      legs {
        mode
        duration
        distance
        headsign
        transitLeg
        realTime
        startTime
        endTime
        from { name lat lon stop { gtfsId name } }
        to { name lat lon stop { gtfsId name } }
        route { gtfsId shortName longName }
        trip { gtfsId }
        intermediateStops { gtfsId name lat lon }
        legGeometry { points }
      }
    }
    routingErrors { code description inputField }
  }
}
"""


class OpenTripPlannerService:
    def __init__(self, endpoint: str, timeout_seconds: float) -> None:
        self.endpoint = endpoint
        self.timeout_seconds = timeout_seconds

    async def plan(
        self,
        origin: Coordinates,
        destination: Coordinates,
        preference: JourneyPreference,
        limit: int = 3,
    ) -> list[JourneyPlan]:
        transfer_penalty, walk_reluctance = _preference_weights(preference)
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(
                    self.endpoint,
                    json={
                        "query": PLAN_QUERY,
                        "operationName": "PlanJourney",
                        "variables": {
                            "from": {"lat": origin.latitude, "lon": origin.longitude},
                            "to": {
                                "lat": destination.latitude,
                                "lon": destination.longitude,
                            },
                            "numItineraries": limit,
                            "transferPenalty": transfer_penalty,
                            "walkReluctance": walk_reluctance,
                        },
                    },
                    headers={"Accept": "application/json", "Content-Type": "application/json"},
                )
                response.raise_for_status()
                payload = response.json()
        except (httpx.HTTPError, ValueError) as error:
            raise JourneyPlannerUnavailableError(
                "O planejador de viagens esta temporariamente indisponivel."
            ) from error

        if payload.get("errors"):
            raise JourneyPlannerUnavailableError(
                "O planejador nao conseguiu processar esta viagem.",
                details={"provider_errors": payload["errors"][:3]},
            )
        plan = (payload.get("data") or {}).get("plan") or {}
        itineraries = plan.get("itineraries") or []
        plans = [_to_plan(item, preference, index) for index, item in enumerate(itineraries)]
        return sorted(plans, key=lambda item: _preference_sort_key(item, preference))


def _preference_weights(preference: JourneyPreference) -> tuple[int, float]:
    if preference == "less_walking":
        return 120, 8.0
    if preference == "fewer_transfers":
        return 900, 2.5
    return 0, 2.0


def _preference_sort_key(
    plan: JourneyPlan,
    preference: JourneyPreference,
) -> tuple[int, int, int]:
    if preference == "less_walking":
        return (
            plan.walking_distance_meters,
            plan.total_duration_minutes,
            plan.transfer_count,
        )
    if preference == "fewer_transfers":
        return (
            plan.transfer_count,
            plan.total_duration_minutes,
            plan.walking_distance_meters,
        )
    return (
        plan.total_duration_minutes,
        plan.transfer_count,
        plan.walking_distance_meters,
    )


def _to_plan(item: dict, preference: JourneyPreference, index: int) -> JourneyPlan:
    steps = [_to_step(leg, leg_index) for leg_index, leg in enumerate(item.get("legs") or [])]
    return JourneyPlan(
        id=f"otp-{preference}-{index}",
        preference=preference,
        total_duration_minutes=_minutes(item.get("duration")),
        walking_duration_minutes=_minutes(item.get("walkTime")),
        walking_distance_meters=round(float(item.get("walkDistance") or 0)),
        transfer_count=max(0, int(item.get("numberOfTransfers") or 0)),
        scheduled_departure=_datetime(item.get("start")),
        estimated_arrival=_datetime(item.get("end")),
        steps=steps,
    )


def _to_step(leg: dict, index: int) -> JourneyStep:
    is_walk = str(leg.get("mode", "")).upper() == "WALK"
    route = leg.get("route") or {}
    from_place = leg.get("from") or {}
    to_place = leg.get("to") or {}
    route_name = route.get("shortName") or route.get("longName")
    from_name = _friendly_place_name(from_place.get("name"), "sua localizacao")
    to_name = _friendly_place_name(to_place.get("name"), "o proximo ponto")
    title = f"Caminhe ate {to_name}" if is_walk else f"Linha {route_name or 'onibus'}"
    description = (
        f"Saindo de {from_name}" if is_walk else leg.get("headsign") or route.get("longName")
    )
    return JourneyStep(
        id=f"leg-{index}",
        kind="walk" if is_walk else "bus",
        title=title,
        description=description,
        duration_minutes=_minutes(leg.get("duration")),
        distance_meters=round(float(leg.get("distance") or 0)),
        route_id=_strip_feed_id(route.get("gtfsId")),
        route_short_name=route.get("shortName"),
        route_long_name=route.get("longName"),
        trip_id=_strip_feed_id((leg.get("trip") or {}).get("gtfsId")),
        headsign=leg.get("headsign"),
        from_stop=_place_to_stop(from_place),
        to_stop=_place_to_stop(to_place),
        intermediate_stops=[
            stop
            for row in (leg.get("intermediateStops") or [])
            if (stop := _place_to_stop({**row, "stop": row})) is not None
        ],
        scheduled_start=_millis_datetime(leg.get("startTime")),
        scheduled_end=_millis_datetime(leg.get("endTime")),
        geometry=(leg.get("legGeometry") or {}).get("points"),
        realtime=bool(leg.get("realTime")),
    )


def _place_to_stop(place: dict) -> JourneyStop | None:
    stop = place.get("stop") or {}
    stop_id = _strip_feed_id(stop.get("gtfsId"))
    if not stop_id:
        return None
    return JourneyStop(
        stop_id=stop_id,
        name=str(stop.get("name") or place.get("name") or "Ponto"),
        coordinates=Coordinates(
            latitude=float(place.get("lat") or 0),
            longitude=float(place.get("lon") or 0),
        ),
    )


def _friendly_place_name(value: str | None, fallback: str) -> str:
    normalized = str(value or "").strip()
    aliases = {
        "origin": "sua localizacao",
        "destination": "o destino",
    }
    return aliases.get(normalized.casefold(), normalized or fallback)


def _strip_feed_id(value: str | None) -> str | None:
    if not value:
        return None
    return value.split(":", 1)[-1]


def _minutes(seconds: int | float | None) -> int:
    return max(0, round(float(seconds or 0) / 60))


def _datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _millis_datetime(value: int | None) -> datetime | None:
    return datetime.fromtimestamp(value / 1000, tz=UTC) if value else None
