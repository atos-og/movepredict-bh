from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.observability import prometheus_metrics
from app.schemas.common import DataResponse, StatusData

router = APIRouter(tags=["system"])


@router.get("/", response_model=DataResponse[StatusData])
def root() -> DataResponse[StatusData]:
    return DataResponse(
        data=StatusData(status="running", service="MovePredict BH API", version="0.1.0")
    )


@router.get("/health", response_model=DataResponse[StatusData])
def health_check() -> DataResponse[StatusData]:
    return DataResponse(data=StatusData(status="ok"))


@router.get("/ready", response_model=DataResponse[StatusData])
def readiness(session: Annotated[Session, Depends(get_db)]) -> DataResponse[StatusData]:
    session.execute(text("SELECT 1"))
    return DataResponse(data=StatusData(status="ready"))


@router.get("/metrics", response_class=PlainTextResponse, include_in_schema=False)
def metrics() -> str:
    return prometheus_metrics()
