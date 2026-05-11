import csv
from pathlib import Path


def get_project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def get_raw_data_dir() -> Path:
    project_root = get_project_root()
    return project_root / "data-exploration" / "data" / "raw"


def get_routes_file_path() -> Path:
    return get_raw_data_dir() / "routes.txt"


def get_stops_file_path() -> Path:
    return get_raw_data_dir() / "stops.txt"


def read_gtfs_csv(file_path: Path) -> list[dict[str, str]]:
    if not file_path.exists():
        raise FileNotFoundError(
            f"Arquivo não encontrado: {file_path}. "
            "Baixe e extraia o GTFS antes de chamar este endpoint."
        )

    with file_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        return list(reader)


def list_lines() -> list[dict[str, str | None]]:
    routes = read_gtfs_csv(get_routes_file_path())

    lines = []

    for route in routes:
        lines.append(
            {
                "route_id": route.get("route_id"),
                "route_short_name": route.get("route_short_name"),
                "route_long_name": route.get("route_long_name"),
                "route_type": route.get("route_type"),
            }
        )

    return lines


def list_stops() -> list[dict[str, str | None]]:
    stops_rows = read_gtfs_csv(get_stops_file_path())

    stops = []

    for stop in stops_rows:
        stops.append(
            {
                "stop_id": stop.get("stop_id"),
                "stop_name": stop.get("stop_name"),
                "stop_lat": stop.get("stop_lat"),
                "stop_lon": stop.get("stop_lon"),
            }
        )

    return stops

