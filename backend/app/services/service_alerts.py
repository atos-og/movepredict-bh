from datetime import UTC, datetime

import httpx
from google.transit import gtfs_realtime_pb2

from app.schemas.alerts import ServiceAlert, ServiceAlertMeta, ServiceAlertResponse


class GtfsRealtimeAlertsService:
    def __init__(self, url: str, timeout_seconds: float = 15.0) -> None:
        self.url = url.strip()
        self.timeout_seconds = timeout_seconds

    async def list_alerts(self) -> ServiceAlertResponse:
        now = datetime.now(UTC)
        if not self.url:
            return ServiceAlertResponse(
                data=[],
                meta=ServiceAlertMeta(
                    generated_at=now,
                    count=0,
                    status="unavailable",
                    source_configured=False,
                ),
            )
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.get(self.url, headers={"Accept": "application/x-protobuf"})
                response.raise_for_status()
            alerts = parse_alert_feed(response.content, now)
        except (httpx.HTTPError, ValueError):
            return ServiceAlertResponse(
                data=[],
                meta=ServiceAlertMeta(
                    generated_at=now,
                    count=0,
                    status="unavailable",
                    source_configured=True,
                ),
            )
        return ServiceAlertResponse(
            data=alerts,
            meta=ServiceAlertMeta(
                generated_at=now,
                count=len(alerts),
                status="live" if alerts else "empty",
                source_configured=True,
            ),
        )


def parse_alert_feed(payload: bytes, now: datetime | None = None) -> list[ServiceAlert]:
    feed = gtfs_realtime_pb2.FeedMessage()
    try:
        feed.ParseFromString(payload)
    except Exception as error:
        raise ValueError("Invalid GTFS-Realtime alert feed") from error
    current = now or datetime.now(UTC)
    result: list[ServiceAlert] = []
    for entity in feed.entity:
        if not entity.HasField("alert"):
            continue
        alert = entity.alert
        periods = list(alert.active_period)
        if periods and not any(_is_active(period, current) for period in periods):
            continue
        route_ids = sorted({item.route_id for item in alert.informed_entity if item.route_id})
        stop_ids = sorted({item.stop_id for item in alert.informed_entity if item.stop_id})
        starts = [period.start for period in periods if period.HasField("start")]
        ends = [period.end for period in periods if period.HasField("end")]
        result.append(
            ServiceAlert(
                id=entity.id,
                title=_translated(alert.header_text) or "Alteracao no transporte",
                description=_translated(alert.description_text),
                url=_translated(alert.url),
                cause=gtfs_realtime_pb2.Alert.Cause.Name(alert.cause),
                effect=gtfs_realtime_pb2.Alert.Effect.Name(alert.effect),
                route_ids=route_ids,
                stop_ids=stop_ids,
                active_from=datetime.fromtimestamp(min(starts), UTC) if starts else None,
                active_until=datetime.fromtimestamp(max(ends), UTC) if ends else None,
            )
        )
    return result


def _translated(value) -> str | None:
    if not value.translation:
        return None
    preferred = next(
        (item.text for item in value.translation if item.language in {"pt", "pt-BR"}), None
    )
    return preferred or value.translation[0].text or None


def _is_active(period, now: datetime) -> bool:
    timestamp = int(now.timestamp())
    starts_before = not period.HasField("start") or period.start <= timestamp
    ends_after = not period.HasField("end") or period.end >= timestamp
    return starts_before and ends_after
