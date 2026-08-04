from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies import get_service_alerts_service
from app.schemas.alerts import ServiceAlertResponse
from app.services.service_alerts import GtfsRealtimeAlertsService

router = APIRouter(prefix="/realtime", tags=["realtime"])
AlertsService = Annotated[GtfsRealtimeAlertsService, Depends(get_service_alerts_service)]


@router.get("/alerts", response_model=ServiceAlertResponse)
async def list_service_alerts(service: AlertsService) -> ServiceAlertResponse:
    return await service.list_alerts()
