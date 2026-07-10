import csv
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_gtfs_service
from app.main import create_app
from app.services.gtfs_service import GtfsService


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


@pytest.fixture
def gtfs_dir(tmp_path: Path) -> Path:
    write_csv(
        tmp_path / "routes.txt",
        [
            {
                "route_id": "r1",
                "route_short_name": "5106",
                "route_long_name": "Bandeirantes / BH Shopping",
                "route_type": "3",
                "route_color": "006B5E",
                "route_text_color": "FFFFFF",
            },
            {
                "route_id": "r2",
                "route_short_name": "MOVE 67",
                "route_long_name": "Estação Vilarinho / Centro",
                "route_type": "3",
                "route_color": "D72638",
                "route_text_color": "FFFFFF",
            },
        ],
    )
    write_csv(
        tmp_path / "stops.txt",
        [
            {
                "stop_id": "s1",
                "stop_code": "1001",
                "stop_name": "Praça Sete",
                "stop_lat": "-19.9191",
                "stop_lon": "-43.9386",
                "wheelchair_boarding": "1",
            },
            {
                "stop_id": "s2",
                "stop_code": "1002",
                "stop_name": "Avenida Afonso Pena",
                "stop_lat": "-19.9250",
                "stop_lon": "-43.9350",
                "wheelchair_boarding": "0",
            },
            {
                "stop_id": "s3",
                "stop_code": "1003",
                "stop_name": "Estação Vilarinho",
                "stop_lat": "-19.8150",
                "stop_lon": "-43.9550",
                "wheelchair_boarding": "1",
            },
        ],
    )
    write_csv(
        tmp_path / "trips.txt",
        [
            {
                "route_id": "r1",
                "service_id": "weekday",
                "trip_id": "t1",
                "trip_headsign": "BH Shopping",
                "direction_id": "0",
                "shape_id": "shape-1",
            },
            {
                "route_id": "r1",
                "service_id": "weekday",
                "trip_id": "t2",
                "trip_headsign": "Bandeirantes",
                "direction_id": "1",
                "shape_id": "shape-2",
            },
        ],
    )
    write_csv(
        tmp_path / "stop_times.txt",
        [
            {
                "trip_id": "t1",
                "arrival_time": "08:00:00",
                "departure_time": "08:00:30",
                "stop_id": "s1",
                "stop_sequence": "1",
            },
            {
                "trip_id": "t1",
                "arrival_time": "08:10:00",
                "departure_time": "08:10:30",
                "stop_id": "s2",
                "stop_sequence": "2",
            },
            {
                "trip_id": "t2",
                "arrival_time": "09:00:00",
                "departure_time": "09:00:30",
                "stop_id": "s2",
                "stop_sequence": "1",
            },
        ],
    )
    write_csv(
        tmp_path / "shapes.txt",
        [
            {
                "shape_id": "shape-1",
                "shape_pt_lat": "-19.9191",
                "shape_pt_lon": "-43.9386",
                "shape_pt_sequence": "1",
            },
            {
                "shape_id": "shape-1",
                "shape_pt_lat": "-19.9250",
                "shape_pt_lon": "-43.9350",
                "shape_pt_sequence": "2",
            },
            {
                "shape_id": "shape-2",
                "shape_pt_lat": "-19.9250",
                "shape_pt_lon": "-43.9350",
                "shape_pt_sequence": "1",
            },
        ],
    )
    return tmp_path


@pytest.fixture
def client(gtfs_dir: Path) -> Iterator[TestClient]:
    application = create_app()
    application.dependency_overrides[get_gtfs_service] = lambda: GtfsService(gtfs_dir)
    with TestClient(application) as test_client:
        yield test_client
