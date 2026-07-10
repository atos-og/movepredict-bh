from pathlib import Path

from fastapi.testclient import TestClient

from app.dependencies import get_gtfs_service
from app.main import create_app
from app.services.gtfs_service import GtfsService


def test_root_and_health(client: TestClient) -> None:
    root = client.get("/")
    health = client.get("/health")

    assert root.status_code == 200
    assert root.json()["data"]["service"] == "MovePredict BH API"
    assert health.json() == {"data": {"status": "ok", "service": None, "version": None}}
    assert root.headers["X-Request-ID"]


def test_list_lines_filters_and_paginates(client: TestClient) -> None:
    response = client.get("/lines", params={"q": "shopping", "limit": 1, "offset": 0})

    assert response.status_code == 200
    assert response.json()["data"][0]["route_id"] == "r1"
    assert response.json()["meta"] == {
        "total": 1,
        "returned": 1,
        "limit": 1,
        "offset": 0,
    }


def test_get_line_and_not_found_error(client: TestClient) -> None:
    assert client.get("/lines/r1").json()["data"]["route_short_name"] == "5106"

    response = client.get("/lines/missing")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "resource_not_found"
    assert response.json()["error"]["details"] == {"route_id": "missing"}


def test_list_stops_filters_by_text_and_bounds(client: TestClient) -> None:
    response = client.get(
        "/stops",
        params={"q": "afonso", "min_lat": -20, "max_lat": -19.9},
    )

    assert response.status_code == 200
    assert response.json()["meta"]["total"] == 1
    assert response.json()["data"][0]["stop_id"] == "s2"


def test_get_stop(client: TestClient) -> None:
    response = client.get("/stops/s1")

    assert response.status_code == 200
    assert response.json()["data"]["stop_lat"] == -19.9191


def test_list_line_stops_uses_selected_trip(client: TestClient) -> None:
    response = client.get("/lines/r1/stops", params={"direction_id": "0"})

    assert response.status_code == 200
    assert [stop["stop_id"] for stop in response.json()["data"]] == ["s1", "s2"]
    assert response.json()["data"][1]["stop_sequence"] == 2


def test_get_line_route_returns_geojson(client: TestClient) -> None:
    response = client.get("/lines/r1/route", params={"trip_id": "t1"})

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["geometry"]["type"] == "LineString"
    assert data["geometry"]["coordinates"][0] == [-43.9386, -19.9191]


def test_list_trips_preserves_existing_feature(client: TestClient) -> None:
    response = client.get("/lines/r1/trips", params={"direction_id": "1"})

    assert response.status_code == 200
    assert response.json()["meta"]["total"] == 1
    assert response.json()["data"][0]["trip_id"] == "t2"


def test_mock_endpoint_was_removed(client: TestClient) -> None:
    response = client.get("/pontos")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "http_error"


def test_validation_errors_use_standard_envelope(client: TestClient) -> None:
    response = client.get("/lines", params={"limit": 0})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_missing_gtfs_file_is_service_unavailable(tmp_path: Path) -> None:
    application = create_app()
    application.dependency_overrides[get_gtfs_service] = lambda: GtfsService(tmp_path)

    with TestClient(application) as client:
        response = client.get("/lines")

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "data_source_unavailable"


def test_cors_allows_configured_frontend(client: TestClient) -> None:
    response = client.options(
        "/lines",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
