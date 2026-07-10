from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.dependencies import get_gtfs_service
from app.schemas.common import DataResponse, ErrorResponse, PageMeta, PageResponse
from app.schemas.transit import Stop
from app.services.gtfs_service import GtfsService

router = APIRouter(prefix="/stops", tags=["stops"])
Service = Annotated[GtfsService, Depends(get_gtfs_service)]


@router.get("", response_model=PageResponse[Stop])
def list_stops(
    service: Service,
    q: str | None = Query(default=None, min_length=1, max_length=100),
    min_lat: float | None = Query(default=None, ge=-90, le=90),
    max_lat: float | None = Query(default=None, ge=-90, le=90),
    min_lon: float | None = Query(default=None, ge=-180, le=180),
    max_lon: float | None = Query(default=None, ge=-180, le=180),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> PageResponse[Stop]:
    items, total = service.list_stops(
        search=q,
        min_lat=min_lat,
        max_lat=max_lat,
        min_lon=min_lon,
        max_lon=max_lon,
        limit=limit,
        offset=offset,
    )
    return PageResponse(
        data=items,
        meta=PageMeta(total=total, returned=len(items), limit=limit, offset=offset),
    )


@router.get(
    "/{stop_id}",
    response_model=DataResponse[Stop],
    responses={404: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
)
def get_stop(stop_id: str, service: Service) -> DataResponse[Stop]:
    return DataResponse(data=service.get_stop(stop_id))
