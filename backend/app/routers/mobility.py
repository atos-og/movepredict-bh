from datetime import UTC, datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query

from app.dependencies import get_geocoding_service, get_journey_planner_service
from app.schemas.common import ErrorResponse
from app.schemas.mobility import (
    Coordinates,
    GeocodingMeta,
    GeocodingResponse,
    JourneyPlanMeta,
    JourneyPlanResponse,
)
from app.services.geocoding import NominatimGeocodingService
from app.services.journey_planner import OpenTripPlannerService

router = APIRouter(tags=["mobility"])
Geocoder = Annotated[NominatimGeocodingService, Depends(get_geocoding_service)]
Planner = Annotated[OpenTripPlannerService, Depends(get_journey_planner_service)]


@router.get(
    "/geocoding/search",
    response_model=GeocodingResponse,
    responses={503: {"model": ErrorResponse}},
)
async def search_destinations(
    service: Geocoder,
    q: str = Query(min_length=2, max_length=160),
    limit: int = Query(default=6, ge=1, le=10),
) -> GeocodingResponse:
    result = await service.search(q, limit)
    return GeocodingResponse(
        data=result.destinations,
        meta=GeocodingMeta(cached=result.cached),
    )


@router.get(
    "/journeys/plan",
    response_model=JourneyPlanResponse,
    responses={503: {"model": ErrorResponse}},
)
async def plan_journey(
    service: Planner,
    origin_lat: float = Query(ge=-90, le=90),
    origin_lon: float = Query(ge=-180, le=180),
    destination_lat: float = Query(ge=-90, le=90),
    destination_lon: float = Query(ge=-180, le=180),
    preference: Literal["quickest", "less_walking", "fewer_transfers"] = "quickest",
    limit: int = Query(default=3, ge=1, le=6),
) -> JourneyPlanResponse:
    plans = await service.plan(
        Coordinates(latitude=origin_lat, longitude=origin_lon),
        Coordinates(latitude=destination_lat, longitude=destination_lon),
        preference,
        limit,
    )
    return JourneyPlanResponse(
        data=plans,
        meta=JourneyPlanMeta(generated_at=datetime.now(UTC)),
    )
