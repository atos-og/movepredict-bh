from datetime import UTC, date, datetime, timedelta

import httpx
import pytest

from app.services.eta import (
    EvaluationRecord,
    calculate_metrics,
    estimate_arrival,
    mean_absolute_error_seconds,
    scheduled_datetime_utc,
    segmented_metrics,
    temporal_split,
)
from app.services.pbh_realtime import PbhRealtimeClient, parse_position


def test_parse_official_pbh_position_payload() -> None:
    position = parse_position(
        {
            "EV": "105",
            "HR": "20260711123020",
            "LT": "-19.925103",
            "LG": "-43.919543",
            "NV": "40962",
            "VL": "17",
            "NL": "1077",
            "DG": "73",
            "SV": "2",
            "DT": "11789",
        }
    )

    assert position.vehicle_id == "40962"
    assert position.source_line_code == "1077"
    assert position.direction_code == 2
    assert position.speed_kmh == 17
    assert position.observed_at.utcoffset().total_seconds() == 0
    assert position.observed_at.hour == 15


def test_baseline_eta_and_mean_absolute_error() -> None:
    observed = datetime(2026, 7, 11, 12, tzinfo=UTC)
    prediction, uncertainty = estimate_arrival(
        observed_at=observed,
        vehicle_latitude=-19.92,
        vehicle_longitude=-43.94,
        stop_latitude=-19.91,
        stop_longitude=-43.94,
        speed_kmh=36,
    )

    assert 100 <= (prediction - observed).total_seconds() <= 120
    assert uncertainty >= 60
    assert mean_absolute_error_seconds([(prediction, prediction)]) == 0
    assert mean_absolute_error_seconds([]) is None


def test_realtime_payload_rejects_invalid_coordinates() -> None:
    with pytest.raises(ValueError):
        parse_position(
            {
                "EV": "105",
                "HR": "20260711123020",
                "LT": "invalid",
                "LG": "-43.9",
                "NV": "1",
            }
        )


def test_realtime_client_retries_transient_failure() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(503, request=request)
        return httpx.Response(
            200,
            request=request,
            json=[
                {
                    "EV": "105",
                    "HR": "20260711123020",
                    "LT": "-19.9",
                    "LG": "-43.9",
                    "NV": "1",
                }
            ],
        )

    client = PbhRealtimeClient(
        "https://example.test/feed",
        max_retries=2,
        backoff_seconds=0,
        transport=httpx.MockTransport(handler),
    )

    assert len(client.fetch_positions()) == 1
    assert client.last_attempt_count == 2
    assert calls == 2


def test_realtime_client_rejects_positions_too_far_in_the_future() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            request=request,
            json=[
                {
                    "EV": "105",
                    "HR": "20990101120000",
                    "LT": "-19.9",
                    "LG": "-43.9",
                    "NV": "future-bus",
                }
            ],
        )

    client = PbhRealtimeClient("https://example.test/feed", transport=httpx.MockTransport(handler))

    assert client.fetch_positions() == []
    assert client.last_parse_error_count == 1


def test_schedule_baseline_and_temporal_evaluation() -> None:
    assert scheduled_datetime_utc(date(2026, 7, 11), 25 * 3600) == datetime(
        2026, 7, 12, 4, tzinfo=UTC
    )
    start = datetime(2026, 7, 11, 12, tzinfo=UTC)
    records = [
        EvaluationRecord(
            predicted=start + timedelta(seconds=index * 10),
            actual=start,
            generated_at=start + timedelta(hours=index),
            route_id="r1" if index < 3 else "r2",
            distance_meters=100 * index,
            horizon_seconds=index * 300,
        )
        for index in range(1, 6)
    ]

    train, validation = temporal_split(records, validation_fraction=0.4)
    metrics = calculate_metrics(validation)

    assert len(train) == 3
    assert len(validation) == 2
    assert metrics is not None
    assert metrics.mae_seconds == 45
    assert metrics.median_seconds == 45
    assert "r2" in segmented_metrics(validation)["route"]
    assert "15min+" in segmented_metrics(validation)["horizon"]
