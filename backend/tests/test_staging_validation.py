import json
from pathlib import Path

import pytest

from app.schemas.realtime import VehiclePositionResponse
from scripts.validate_staging import ProbeSample, build_report, validate_public_url
from scripts.validate_staging import validate_realtime_response as validate_response


def test_realtime_contract_validator_accepts_closed_contract() -> None:
    validate_response(
        {
            "data": [
                {
                    "vehicle_id": "40962",
                    "latitude": -19.925103,
                    "longitude": -43.919543,
                    "observed_at": "2026-07-11T15:30:20Z",
                    "status": "in_transit",
                }
            ],
            "meta": {
                "generated_at": "2026-07-11T15:30:22Z",
                "count": 1,
                "status": "live",
                "stale": False,
                "stale_after_seconds": 120,
            },
        },
        item_fields={"vehicle_id", "latitude", "longitude", "observed_at", "status"},
    )


def test_documented_real_vehicle_example_matches_pydantic_contract() -> None:
    example = Path(__file__).parents[2] / "docs" / "examples" / "realtime-vehicles-response.json"
    payload = json.loads(example.read_text(encoding="utf-8"))
    response = VehiclePositionResponse.model_validate(payload)
    assert response.meta.status == "live"
    assert response.data[0].vehicle_id == "40556"


def test_realtime_contract_validator_rejects_inconsistent_meta() -> None:
    with pytest.raises(ValueError, match="count"):
        validate_response(
            {
                "data": [],
                "meta": {
                    "generated_at": "2026-07-11T15:30:22Z",
                    "count": 1,
                    "status": "empty",
                    "stale": False,
                    "stale_after_seconds": 120,
                },
            },
            item_fields=set(),
        )


def test_staging_url_rejects_credentials_and_plain_http() -> None:
    assert validate_public_url("http://localhost:8000/", name="api") == "http://localhost:8000"
    with pytest.raises(ValueError):
        validate_public_url("http://staging.example.com", name="api")
    with pytest.raises(ValueError):
        validate_public_url("https://user:secret@example.com", name="api")


def test_report_summarizes_live_and_stale_samples() -> None:
    samples = [
        ProbeSample("now", "live", 10, 10, "empty", 0, "s1"),
        ProbeSample("later", "stale", 0, 0, "live", 2, "s1"),
    ]
    report = build_report(samples, started_at="start", finished_at="finish")
    assert report["sample_count"] == 2
    assert report["live_vehicle_samples"] == 1
    assert report["stale_vehicle_samples"] == 1
    assert report["maximum_vehicle_count"] == 10
