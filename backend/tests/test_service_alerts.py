from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from google.transit import gtfs_realtime_pb2

from app.dependencies import get_service_alerts_service
from app.main import create_app
from app.schemas.alerts import ServiceAlertMeta, ServiceAlertResponse
from app.services.service_alerts import parse_alert_feed


def test_alert_parser_exposes_active_route_alert() -> None:
    now = datetime.now(UTC)
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.header.gtfs_realtime_version = "2.0"
    entity = feed.entity.add()
    entity.id = "alert-1"
    entity.alert.active_period.add(
        start=int((now - timedelta(minutes=5)).timestamp()),
        end=int((now + timedelta(hours=1)).timestamp()),
    )
    entity.alert.informed_entity.add(route_id="1170")
    entity.alert.header_text.translation.add(text="Desvio temporario", language="pt-BR")
    entity.alert.description_text.translation.add(text="Linha com itinerario alterado.")

    alerts = parse_alert_feed(feed.SerializeToString(), now)

    assert len(alerts) == 1
    assert alerts[0].title == "Desvio temporario"
    assert alerts[0].route_ids == ["1170"]


def test_alert_endpoint_preserves_unavailable_state() -> None:
    class AlertsService:
        async def list_alerts(self) -> ServiceAlertResponse:
            return ServiceAlertResponse(
                data=[],
                meta=ServiceAlertMeta(
                    generated_at=datetime.now(UTC),
                    count=0,
                    status="unavailable",
                    source_configured=False,
                ),
            )

    application = create_app()
    application.dependency_overrides[get_service_alerts_service] = AlertsService
    with TestClient(application) as client:
        response = client.get("/realtime/alerts")
    assert response.status_code == 200
    assert response.json()["meta"]["status"] == "unavailable"
