import csv
from collections import defaultdict
from pathlib import Path
from collections.abc import Iterable, Iterator


def get_project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def get_raw_data_dir() -> Path:
    project_root = get_project_root()
    return project_root / "data-exploration" / "data" / "raw"


def read_gtfs_csv(file_name: str) -> list[dict[str, str]]:
    return list(iter_gtfs_csv(file_name))


def iter_gtfs_csv(file_name: str) -> Iterator[dict[str, str]]:
    raw_data_dir = get_raw_data_dir()
    file_path = raw_data_dir / file_name

    if not file_path.exists():
        raise FileNotFoundError(
            f"Arquivo não encontrado: {file_path}. "
            "Baixe e extraia o GTFS antes de rodar este script."
        )

    with file_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        yield from reader


def normalize(value: str) -> str:
    return " ".join(value.casefold().split())


def find_routes(query: str) -> list[dict[str, str]]:
    needle = normalize(query)
    routes = read_gtfs_csv("routes.txt")
    exact = [
        route for route in routes if normalize(route.get("route_id", "")) == needle
    ]
    if exact:
        return exact
    return [
        route
        for route in routes
        if any(
            needle in normalize(route.get(field, ""))
            for field in ("route_id", "route_short_name", "route_long_name")
        )
    ]


def index_rows(
    rows: Iterable[dict[str, str]], key: str
) -> dict[str, list[dict[str, str]]]:
    result: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        result[row.get(key, "")].append(row)
    return dict(result)


def numeric(value: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def describe_route(route: dict[str, str]) -> str:
    return " | ".join(
        (
            route.get("route_id", ""),
            route.get("route_short_name", ""),
            route.get("route_long_name", ""),
        )
    )
