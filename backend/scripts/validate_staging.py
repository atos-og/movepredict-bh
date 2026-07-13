"""Validate MovePredict staging contracts and optionally sample them over time."""

from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ProbeSample:
    collected_at: str
    vehicle_status: str
    vehicle_count: int
    unique_vehicle_count: int
    arrival_status: str
    arrival_count: int
    stop_id: str | None


def validate_public_url(value: str, *, name: str) -> str:
    url = value.rstrip("/")
    parsed = urllib.parse.urlparse(url)
    is_local = parsed.hostname in {"localhost", "127.0.0.1", "::1"}
    if parsed.scheme not in ({"http", "https"} if is_local else {"https"}) or not parsed.netloc:
        raise ValueError(f"{name} must use HTTPS, except for localhost.")
    if parsed.username or parsed.password:
        raise ValueError(f"{name} must not contain credentials.")
    return url


def get_json(url: str, *, timeout: float = 20) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": "MovePredict-Staging-Probe/1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.load(response)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
        raise RuntimeError(f"Request failed for {url}: {error}") from error
    if not isinstance(payload, dict):
        raise ValueError(f"Expected a JSON object from {url}.")
    return payload


def validate_realtime_response(payload: dict[str, Any], *, item_fields: set[str]) -> None:
    data = payload.get("data")
    meta = payload.get("meta")
    if not isinstance(data, list) or not isinstance(meta, dict):
        raise ValueError("Realtime response must contain data[] and meta{}.")
    required_meta = {"generated_at", "count", "status", "stale", "stale_after_seconds"}
    if not required_meta.issubset(meta):
        raise ValueError(f"Realtime meta is missing: {sorted(required_meta - set(meta))}")
    if meta["status"] not in {"live", "empty", "stale"}:
        raise ValueError("Realtime status must be live, empty or stale.")
    if meta["count"] != len(data):
        raise ValueError("Realtime meta.count does not match data length.")
    if meta["stale"] != (meta["status"] == "stale"):
        raise ValueError("Realtime stale flag and status disagree.")
    for index, item in enumerate(data):
        if not isinstance(item, dict) or not item_fields.issubset(item):
            missing = item_fields - set(item) if isinstance(item, dict) else item_fields
            raise ValueError(f"Realtime item {index} is missing: {sorted(missing)}")


def probe_once(api_url: str) -> ProbeSample:
    health = get_json(f"{api_url}/health")
    ready = get_json(f"{api_url}/ready")
    if health.get("data", {}).get("status") != "ok":
        raise ValueError("API liveness is not ok.")
    if ready.get("data", {}).get("status") != "ready":
        raise ValueError("API readiness is not ready.")

    lines = get_json(f"{api_url}/lines?limit=1")
    stops = get_json(f"{api_url}/stops?limit=1")
    if not isinstance(lines.get("data"), list) or not lines["data"]:
        raise ValueError("No GTFS line is available in staging.")
    if not isinstance(stops.get("data"), list) or not stops["data"]:
        raise ValueError("No GTFS stop is available in staging.")

    vehicles = get_json(f"{api_url}/realtime/vehicles?limit=200")
    validate_realtime_response(
        vehicles,
        item_fields={"vehicle_id", "latitude", "longitude", "observed_at", "status"},
    )
    stop_id = str(stops["data"][0]["stop_id"])
    arrivals = get_json(
        f"{api_url}/realtime/stops/{urllib.parse.quote(stop_id, safe='')}/arrivals?limit=100"
    )
    validate_realtime_response(
        arrivals,
        item_fields={"stop_id", "route_id", "predicted_arrival", "generated_at"},
    )
    vehicle_ids = {item["vehicle_id"] for item in vehicles["data"]}
    return ProbeSample(
        collected_at=datetime.now(UTC).isoformat(),
        vehicle_status=vehicles["meta"]["status"],
        vehicle_count=len(vehicles["data"]),
        unique_vehicle_count=len(vehicle_ids),
        arrival_status=arrivals["meta"]["status"],
        arrival_count=len(arrivals["data"]),
        stop_id=stop_id,
    )


def validate_frontend(web_url: str) -> None:
    request = urllib.request.Request(
        web_url, headers={"User-Agent": "MovePredict-Staging-Probe/1.0"}
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            content = response.read(500_000).decode("utf-8", errors="replace")
    except (urllib.error.URLError, TimeoutError) as error:
        raise RuntimeError(f"Frontend request failed: {error}") from error
    if "MovePredict" not in content:
        raise ValueError("Frontend response does not identify MovePredict.")


def build_report(
    samples: list[ProbeSample], *, started_at: str, finished_at: str
) -> dict[str, Any]:
    return {
        "started_at": started_at,
        "finished_at": finished_at,
        "sample_count": len(samples),
        "live_vehicle_samples": sum(sample.vehicle_status == "live" for sample in samples),
        "stale_vehicle_samples": sum(sample.vehicle_status == "stale" for sample in samples),
        "empty_vehicle_samples": sum(sample.vehicle_status == "empty" for sample in samples),
        "maximum_vehicle_count": max((sample.vehicle_count for sample in samples), default=0),
        "maximum_arrival_count": max((sample.arrival_count for sample in samples), default=0),
        "samples": [asdict(sample) for sample in samples],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-url", required=True)
    parser.add_argument("--web-url")
    parser.add_argument("--duration-minutes", type=int, default=0)
    parser.add_argument("--interval-seconds", type=int, default=20)
    parser.add_argument("--output", type=Path, default=Path("staging-validation.json"))
    parser.add_argument("--require-live-data", action="store_true")
    args = parser.parse_args()
    if args.duration_minutes < 0 or not 5 <= args.interval_seconds <= 300:
        parser.error("duration must be non-negative and interval must be between 5 and 300 seconds")

    api_url = validate_public_url(args.api_url, name="api-url")
    web_url = validate_public_url(args.web_url, name="web-url") if args.web_url else None
    started_at = datetime.now(UTC).isoformat()
    deadline = time.monotonic() + args.duration_minutes * 60
    samples: list[ProbeSample] = []
    while True:
        samples.append(probe_once(api_url))
        if web_url:
            validate_frontend(web_url)
        if time.monotonic() >= deadline:
            break
        time.sleep(min(args.interval_seconds, max(0, deadline - time.monotonic())))

    report = build_report(
        samples,
        started_at=started_at,
        finished_at=datetime.now(UTC).isoformat(),
    )
    args.output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps({key: value for key, value in report.items() if key != "samples"}, indent=2))
    if args.require_live_data and report["live_vehicle_samples"] == 0:
        raise SystemExit("No live vehicle sample was observed.")


if __name__ == "__main__":
    main()
