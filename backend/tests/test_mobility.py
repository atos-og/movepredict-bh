from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from app.dependencies import get_geocoding_service, get_journey_planner_service
from app.main import create_app
from app.schemas.mobility import Coordinates, GeocodedDestination
from app.services.geocoding import GeocodingResult
from app.services.journey_planner import _to_plan


def test_geocoding_endpoint_exposes_stable_contract() -> None:
    class Geocoder:
        async def search(self, query: str, limit: int):
            assert query == "Mineirao"
            assert limit == 4
            return GeocodingResult(
                destinations=[
                    GeocodedDestination(
                        id="osm-1",
                        kind="landmark",
                        label="Mineirao",
                        description="Estadio Mineirao, Belo Horizonte, Minas Gerais",
                        coordinates=Coordinates(latitude=-19.8658, longitude=-43.9711),
                    )
                ],
                cached=True,
            )

    application = create_app()
    application.dependency_overrides[get_geocoding_service] = Geocoder
    with TestClient(application) as client:
        response = client.get("/geocoding/search", params={"q": "Mineirao", "limit": 4})

    assert response.status_code == 200
    assert response.json()["data"][0]["kind"] == "landmark"
    assert response.json()["meta"] == {
        "provider": "nominatim",
        "attribution": "OpenStreetMap contributors",
        "cached": True,
    }


def test_journey_endpoint_forwards_preference() -> None:
    class Planner:
        async def plan(self, origin, destination, preference, limit):
            assert origin.latitude == -19.92
            assert destination.longitude == -43.97
            assert preference == "less_walking"
            assert limit == 2
            return []

    application = create_app()
    application.dependency_overrides[get_journey_planner_service] = Planner
    with TestClient(application) as client:
        response = client.get(
            "/journeys/plan",
            params={
                "origin_lat": -19.92,
                "origin_lon": -43.94,
                "destination_lat": -19.86,
                "destination_lon": -43.97,
                "preference": "less_walking",
                "limit": 2,
            },
        )

    assert response.status_code == 200
    assert response.json()["data"] == []
    assert response.json()["meta"]["provider"] == "opentripplanner"


def test_otp_payload_is_normalized_for_the_frontend() -> None:
    departure = datetime(2026, 7, 15, 12, tzinfo=UTC)
    plan = _to_plan(
        {
            "duration": 1_800,
            "walkTime": 420,
            "walkDistance": 510.4,
            "numberOfTransfers": 0,
            "start": departure.isoformat(),
            "end": (departure + timedelta(minutes=30)).isoformat(),
            "legs": [
                {
                    "mode": "BUS",
                    "duration": 1_200,
                    "distance": 6_200,
                    "headsign": "Savassi",
                    "startTime": int(departure.timestamp() * 1000),
                    "endTime": int((departure + timedelta(minutes=20)).timestamp() * 1000),
                    "route": {
                        "gtfsId": "PBH:562252",
                        "shortName": "1170",
                        "longName": "Santa Lucia / Mangabeiras",
                    },
                    "trip": {"gtfsId": "PBH:trip-1"},
                    "from": {
                        "name": "Av. Amazonas",
                        "lat": -19.92,
                        "lon": -43.94,
                        "stop": {"gtfsId": "PBH:stop-1", "name": "Av. Amazonas"},
                    },
                    "to": {
                        "name": "Savassi",
                        "lat": -19.94,
                        "lon": -43.94,
                        "stop": {"gtfsId": "PBH:stop-2", "name": "Savassi"},
                    },
                    "intermediateStops": [],
                    "legGeometry": {"points": "encoded"},
                    "realTime": False,
                }
            ],
        },
        "quickest",
        0,
    )

    assert plan.total_duration_minutes == 30
    assert plan.walking_distance_meters == 510
    assert plan.steps[0].route_id == "562252"
    assert plan.steps[0].from_stop.stop_id == "stop-1"
    assert plan.steps[0].geometry == "encoded"
