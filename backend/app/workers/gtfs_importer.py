import argparse
import csv
import io
import logging
from collections import defaultdict
from collections.abc import Iterable, Iterator
from datetime import datetime
from pathlib import Path

import httpx
from sqlalchemy import select, text, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import SessionLocal
from app.models import (
    RouteSourceCode,
    ServiceCalendar,
    ServiceException,
    TransitRoute,
    TransitStop,
    TransitTrip,
    TripStop,
)

logger = logging.getLogger("movepredict.gtfs_import")


def read_csv(path: Path) -> Iterator[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as file:
        yield from csv.DictReader(file)


def batches(rows: Iterable[dict], size: int = 5_000) -> Iterator[list[dict]]:
    batch = []
    for row in rows:
        batch.append(row)
        if len(batch) >= size:
            yield batch
            batch = []
    if batch:
        yield batch


def import_static_gtfs(session: Session, gtfs_dir: Path, *, include_stop_times: bool) -> None:
    _upsert(
        session,
        TransitRoute,
        (
            {
                "gtfs_route_id": row["route_id"],
                "short_name": row.get("route_short_name") or None,
                "long_name": row.get("route_long_name") or None,
            }
            for row in read_csv(gtfs_dir / "routes.txt")
        ),
        "gtfs_route_id",
    )
    _upsert(
        session,
        TransitStop,
        (
            {
                "gtfs_stop_id": row["stop_id"],
                "name": row.get("stop_name", ""),
                "latitude": float(row["stop_lat"]),
                "longitude": float(row["stop_lon"]),
            }
            for row in read_csv(gtfs_dir / "stops.txt")
        ),
        "gtfs_stop_id",
    )
    _import_calendars(session, gtfs_dir)
    _import_shapes(session, gtfs_dir / "shapes.txt")
    routes = {
        gtfs_route_id: route_id
        for gtfs_route_id, route_id in session.execute(
            select(TransitRoute.gtfs_route_id, TransitRoute.id)
        )
    }
    _upsert(
        session,
        TransitTrip,
        (
            {
                "gtfs_trip_id": row["trip_id"],
                "route_id": routes[row["route_id"]],
                "service_id": row.get("service_id") or None,
                "direction_id": _int_or_none(row.get("direction_id")),
                "headsign": row.get("trip_headsign") or None,
                "shape_id": row.get("shape_id") or None,
            }
            for row in read_csv(gtfs_dir / "trips.txt")
        ),
        "gtfs_trip_id",
    )
    _import_schedule(
        session,
        gtfs_dir / "stop_times.txt",
        include_stop_times=include_stop_times,
    )
    session.commit()


def import_line_mapping(session: Session, url: str) -> tuple[int, int]:
    response = httpx.get(
        url,
        timeout=30,
        follow_redirects=True,
        headers={"User-Agent": "MovePredict-BH/0.1 (+https://github.com/atos-og/movepredict-bh)"},
    )
    response.raise_for_status()
    text = response.content.decode("latin-1")
    routes_by_short: dict[str, list[int]] = {}
    routes_by_base: dict[str, list[int]] = {}
    for short_name, route_id in session.execute(
        select(TransitRoute.short_name, TransitRoute.id).where(TransitRoute.short_name.is_not(None))
    ).tuples():
        routes_by_short.setdefault(_line_key(short_name), []).append(route_id)
        routes_by_base.setdefault(_line_base(short_name), []).append(route_id)
    matched = 0
    mappings = []
    for row in csv.DictReader(io.StringIO(text), delimiter=";"):
        candidates = routes_by_short.get(_line_key(row["Linha"]), [])
        if len(candidates) != 1:
            candidates = routes_by_base.get(_line_base(row["Linha"]), [])
        route_id = candidates[0] if len(candidates) == 1 else None
        matched += route_id is not None
        mappings.append(
            {
                "source_code": row["NumeroLinha"].strip(),
                "public_line_code": row["Linha"].strip(),
                "source_name": row.get("Nome", "").strip() or None,
                "route_id": route_id,
            }
        )
    _upsert(session, RouteSourceCode, mappings, "source_code")
    session.commit()
    return len(mappings), matched


def _import_calendars(session: Session, gtfs_dir: Path) -> None:
    _upsert(
        session,
        ServiceCalendar,
        (
            {
                "service_id": row["service_id"],
                **{day: row.get(day) == "1" for day in _WEEKDAYS},
                "start_date": _gtfs_date(row["start_date"]),
                "end_date": _gtfs_date(row["end_date"]),
            }
            for row in read_csv(gtfs_dir / "calendar.txt")
        ),
        "service_id",
    )
    exceptions = [
        {
            "service_id": row["service_id"],
            "service_date": _gtfs_date(row["date"]),
            "exception_type": int(row["exception_type"]),
        }
        for row in read_csv(gtfs_dir / "calendar_dates.txt")
    ]
    if exceptions:
        statement = insert(ServiceException).values(exceptions)
        session.execute(
            statement.on_conflict_do_update(
                constraint="uq_service_exception",
                set_={"exception_type": statement.excluded.exception_type},
            )
        )
        session.commit()


def _import_shapes(session: Session, path: Path) -> None:
    points: dict[str, list[tuple[int, float, float]]] = defaultdict(list)
    for row in read_csv(path):
        points[row["shape_id"]].append(
            (
                int(row["shape_pt_sequence"]),
                float(row["shape_pt_lon"]),
                float(row["shape_pt_lat"]),
            )
        )
    statement = text(
        """
        INSERT INTO transit_shapes (gtfs_shape_id, point_count, path, length_meters)
        VALUES (
            :shape_id,
            :point_count,
            ST_GeomFromText(:wkt, 4326),
            ST_Length(ST_GeomFromText(:wkt, 4326)::geography)
        )
        ON CONFLICT (gtfs_shape_id) DO UPDATE SET
            point_count = EXCLUDED.point_count,
            path = EXCLUDED.path,
            length_meters = EXCLUDED.length_meters
        """
    )
    for shape_id, shape_points in points.items():
        ordered = sorted(shape_points)
        coordinates = ",".join(f"{lon} {lat}" for _, lon, lat in ordered)
        session.execute(
            statement,
            {
                "shape_id": shape_id,
                "point_count": len(ordered),
                "wkt": f"LINESTRING({coordinates})",
            },
        )
    session.commit()


def _import_schedule(session: Session, path: Path, *, include_stop_times: bool) -> None:
    trips = {
        gtfs_trip_id: trip_id
        for gtfs_trip_id, trip_id in session.execute(
            select(TransitTrip.gtfs_trip_id, TransitTrip.id)
        )
    }
    stops = {
        gtfs_stop_id: stop_id
        for gtfs_stop_id, stop_id in session.execute(
            select(TransitStop.gtfs_stop_id, TransitStop.id)
        )
    }
    schedule_bounds: dict[int, list[int]] = {}
    stop_rows: list[dict] = []
    for row in read_csv(path):
        trip_id = trips.get(row["trip_id"])
        stop_id = stops.get(row["stop_id"])
        if trip_id is None or stop_id is None:
            continue
        arrival = _time_seconds(row.get("arrival_time"))
        departure = _time_seconds(row.get("departure_time"))
        values = [value for value in (arrival, departure) if value is not None]
        if values:
            bounds = schedule_bounds.setdefault(trip_id, [min(values), max(values)])
            bounds[0] = min(bounds[0], *values)
            bounds[1] = max(bounds[1], *values)
        if include_stop_times:
            stop_rows.append(
                {
                    "trip_id": trip_id,
                    "stop_id": stop_id,
                    "stop_sequence": int(row["stop_sequence"]),
                    "scheduled_arrival_seconds": arrival,
                    "scheduled_departure_seconds": departure,
                }
            )
            if len(stop_rows) >= 5_000:
                _upsert_trip_stops(session, stop_rows)
                stop_rows = []
    if stop_rows:
        _upsert_trip_stops(session, stop_rows)
    for batch in batches(
        (
            {"id": trip_id, "start_time_seconds": bounds[0], "end_time_seconds": bounds[1]}
            for trip_id, bounds in schedule_bounds.items()
        )
    ):
        session.execute(update(TransitTrip), batch)
        session.commit()
    if include_stop_times:
        session.execute(
            text(
                """
                UPDATE trip_stops AS ts
                SET shape_progress = ST_LineLocatePoint(sh.path, st.location::geometry)
                FROM transit_trips AS t, transit_shapes AS sh, transit_stops AS st
                WHERE ts.trip_id = t.id
                  AND ts.stop_id = st.id
                  AND t.shape_id = sh.gtfs_shape_id
                  AND ts.shape_progress IS NULL
                """
            )
        )
        session.commit()


def _upsert_trip_stops(session: Session, rows: list[dict]) -> None:
    statement = insert(TripStop).values(rows)
    session.execute(
        statement.on_conflict_do_update(
            constraint="uq_trip_stop_sequence",
            set_={
                "stop_id": statement.excluded.stop_id,
                "scheduled_arrival_seconds": statement.excluded.scheduled_arrival_seconds,
                "scheduled_departure_seconds": statement.excluded.scheduled_departure_seconds,
            },
        )
    )
    session.commit()


def _upsert(session: Session, model, rows: Iterable[dict], conflict_column: str) -> None:
    table = model.__table__
    for batch in batches(rows):
        statement = insert(table).values(batch)
        updates = {
            column.name: getattr(statement.excluded, column.name)
            for column in table.columns
            if column.name not in {"id", conflict_column}
        }
        session.execute(
            statement.on_conflict_do_update(index_elements=[conflict_column], set_=updates)
        )
        session.commit()


def _line_key(value: str) -> str:
    return value.strip().upper().replace(" ", "")


def _line_base(value: str) -> str:
    base = _line_key(value).split("-", 1)[0]
    return base.lstrip("0") or "0"


def _int_or_none(value: str | None) -> int | None:
    return int(value) if value and value.strip() else None


def _time_seconds(value: str | None) -> int | None:
    if not value:
        return None
    hours, minutes, seconds = (int(part) for part in value.split(":"))
    return hours * 3600 + minutes * 60 + seconds


def _gtfs_date(value: str):
    return datetime.strptime(value, "%Y%m%d").date()


_WEEKDAYS = (
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Importa GTFS e códigos de linha para PostgreSQL.")
    parser.add_argument("--include-stop-times", action="store_true")
    args = parser.parse_args()
    settings = get_settings()
    logging.basicConfig(level=logging.INFO)
    with SessionLocal() as session:
        import_static_gtfs(
            session,
            settings.gtfs_data_dir,
            include_stop_times=args.include_stop_times,
        )
        total, matched = import_line_mapping(session, settings.realtime_line_mapping_url)
    logger.info("GTFS importado; códigos PBH relacionados: %s/%s", matched, total)


if __name__ == "__main__":
    main()
