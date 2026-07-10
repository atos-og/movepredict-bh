from fastapi import APIRouter

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
