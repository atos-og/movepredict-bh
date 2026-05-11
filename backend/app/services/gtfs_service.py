import csv
from pathlib import Path


def get_project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def get_routes_file_path() -> Path:
    project_root = get_project_root()
    return project_root / "data-exploration" / "data" / "raw" / "routes.txt"


def list_lines() -> list[dict]:
    routes_file = get_routes_file_path()

    if not routes_file.exists():
        raise FileNotFoundError(
            "Arquivo routes.txt não encontrado. "
            "Rode o download/extract do GTFS antes de chamar este endpoint."
        )

    lines = []

    with routes_file.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            lines.append(
                {
                    "route_id": row.get("route_id"),
                    "route_short_name": row.get("route_short_name"),
                    "route_long_name": row.get("route_long_name"),
                    "route_type": row.get("route_type"),
                }
            )

    return lines