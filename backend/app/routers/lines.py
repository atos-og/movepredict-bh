from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.dependencies import get_gtfs_service
from app.schemas.common import DataResponse, ErrorResponse, PageMeta, PageResponse
from app.schemas.transit import Line, LineRoute, LineStop, Trip
from app.services.gtfs_service import GtfsService

router = APIRouter(prefix="/lines", tags=["lines"])
Service = Annotated[GtfsService, Depends(get_gtfs_service)]


@router.get("", response_model=PageResponse[Line])
def list_lines(
    service: Service,
    q: str | None = Query(default=None, min_length=1, max_length=100),
    route_type: int | None = Query(default=None, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> PageResponse[Line]:
    items, total = service.list_lines(search=q, route_type=route_type, limit=limit, offset=offset)
    return PageResponse(
        data=items,
        meta=PageMeta(total=total, returned=len(items), limit=limit, offset=offset),
    )


@router.get(
    "/{route_id}/stops",
    response_model=DataResponse[list[LineStop]],
    responses={404: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
)
def list_line_stops(
    route_id: str,
    service: Service,
    direction_id: str | None = Query(default=None, pattern="^[01]$"),
    trip_id: str | None = Query(default=None, min_length=1),
) -> DataResponse[list[LineStop]]:
    return DataResponse(
        data=service.list_line_stops(route_id, direction_id=direction_id, trip_id=trip_id)
    )


@router.get(
    "/{route_id}/route",
    response_model=DataResponse[LineRoute],
    responses={404: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
)
def get_line_route(
    route_id: str,
    service: Service,
    direction_id: str | None = Query(default=None, pattern="^[01]$"),
    trip_id: str | None = Query(default=None, min_length=1),
) -> DataResponse[LineRoute]:
    return DataResponse(
        data=service.get_line_route(route_id, direction_id=direction_id, trip_id=trip_id)
    )


@router.get(
    "/{route_id}/trips",
    response_model=PageResponse[Trip],
    responses={404: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
)
def list_line_trips(
    route_id: str,
    service: Service,
    direction_id: str | None = Query(default=None, pattern="^[01]$"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> PageResponse[Trip]:
    items, total = service.list_trips(
        route_id, direction_id=direction_id, limit=limit, offset=offset
    )
    return PageResponse(
        data=items,
        meta=PageMeta(total=total, returned=len(items), limit=limit, offset=offset),
    )


@router.get(
    "/{route_id}",
    response_model=DataResponse[Line],
    responses={404: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
)
def get_line(route_id: str, service: Service) -> DataResponse[Line]:
    return DataResponse(data=service.get_line(route_id))
