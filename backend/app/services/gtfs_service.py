import csv
from collections.abc import Iterator
from pathlib import Path

from app.exceptions import DataSourceUnavailableError, ResourceNotFoundError
from app.schemas.transit import GeoJsonLineString, Line, LineRoute, LineStop, Stop, Trip


class GtfsService:
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir

    def list_lines(
        self,
        *,
        search: str | None = None,
        route_type: int | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Line], int]:
        lines = [self._line_from_row(row) for row in self._read_rows("routes.txt")]
        if search:
            needle = search.casefold()
            lines = [
                line
                for line in lines
                if needle
                in " ".join(
                    filter(
                        None,
                        [line.route_id, line.route_short_name, line.route_long_name],
                    )
                ).casefold()
            ]
        if route_type is not None:
            lines = [line for line in lines if line.route_type == route_type]
        lines.sort(key=lambda line: (line.route_short_name or "", line.route_id))
        return lines[offset : offset + limit], len(lines)

    def get_line(self, route_id: str) -> Line:
        for row in self._iter_rows("routes.txt"):
            if row.get("route_id") == route_id:
                return self._line_from_row(row)
        raise ResourceNotFoundError(f"Linha '{route_id}' não encontrada.", {"route_id": route_id})

    def list_stops(
        self,
        *,
        search: str | None = None,
        min_lat: float | None = None,
        max_lat: float | None = None,
        min_lon: float | None = None,
        max_lon: float | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Stop], int]:
        stops = [self._stop_from_row(row) for row in self._read_rows("stops.txt")]
        if search:
            needle = search.casefold()
            stops = [
                stop
                for stop in stops
                if needle in f"{stop.stop_id} {stop.stop_code or ''} {stop.stop_name}".casefold()
            ]
        if min_lat is not None:
            stops = [stop for stop in stops if stop.stop_lat >= min_lat]
        if max_lat is not None:
            stops = [stop for stop in stops if stop.stop_lat <= max_lat]
        if min_lon is not None:
            stops = [stop for stop in stops if stop.stop_lon >= min_lon]
        if max_lon is not None:
            stops = [stop for stop in stops if stop.stop_lon <= max_lon]
        stops.sort(key=lambda stop: (stop.stop_name, stop.stop_id))
        return stops[offset : offset + limit], len(stops)

    def get_stop(self, stop_id: str) -> Stop:
        for row in self._iter_rows("stops.txt"):
            if row.get("stop_id") == stop_id:
                return self._stop_from_row(row)
        raise ResourceNotFoundError(f"Ponto '{stop_id}' não encontrado.", {"stop_id": stop_id})

    def list_trips(
        self,
        route_id: str,
        *,
        direction_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Trip], int]:
        self.get_line(route_id)
        trips = [
            self._trip_from_row(row)
            for row in self._iter_rows("trips.txt")
            if row.get("route_id") == route_id
            and (direction_id is None or row.get("direction_id") == direction_id)
        ]
        trips.sort(key=lambda trip: trip.trip_id)
        return trips[offset : offset + limit], len(trips)

    def list_line_stops(
        self,
        route_id: str,
        *,
        direction_id: str | None = None,
        trip_id: str | None = None,
    ) -> list[LineStop]:
        trip = self._select_trip(route_id, direction_id=direction_id, trip_id=trip_id)
        stop_times = [
            row for row in self._iter_rows("stop_times.txt") if row.get("trip_id") == trip.trip_id
        ]
        stop_times.sort(key=lambda row: self._required_int(row.get("stop_sequence")))
        stop_ids = {row.get("stop_id") for row in stop_times}
        stops = {
            row.get("stop_id"): self._stop_from_row(row)
            for row in self._iter_rows("stops.txt")
            if row.get("stop_id") in stop_ids
        }
        result: list[LineStop] = []
        for row in stop_times:
            stop_id_value = row.get("stop_id")
            stop = stops.get(stop_id_value)
            if stop is None:
                continue
            result.append(
                LineStop(
                    **stop.model_dump(),
                    stop_sequence=self._required_int(row.get("stop_sequence")),
                    arrival_time=row.get("arrival_time") or None,
                    departure_time=row.get("departure_time") or None,
                )
            )
        return result

    def get_line_route(
        self,
        route_id: str,
        *,
        direction_id: str | None = None,
        trip_id: str | None = None,
    ) -> LineRoute:
        trip = self._select_trip(route_id, direction_id=direction_id, trip_id=trip_id)
        if not trip.shape_id:
            raise ResourceNotFoundError(
                f"A viagem '{trip.trip_id}' não possui trajeto associado.",
                {"trip_id": trip.trip_id},
            )
        points = [
            row for row in self._iter_rows("shapes.txt") if row.get("shape_id") == trip.shape_id
        ]
        points.sort(key=lambda row: self._required_int(row.get("shape_pt_sequence")))
        coordinates = [
            (
                self._required_float(row.get("shape_pt_lon")),
                self._required_float(row.get("shape_pt_lat")),
            )
            for row in points
        ]
        if not coordinates:
            raise ResourceNotFoundError(
                f"Geometria do shape '{trip.shape_id}' não encontrada.",
                {"shape_id": trip.shape_id},
            )
        return LineRoute(
            route_id=route_id,
            trip_id=trip.trip_id,
            shape_id=trip.shape_id,
            direction_id=trip.direction_id,
            geometry=GeoJsonLineString(coordinates=coordinates),
        )

    def _select_trip(
        self,
        route_id: str,
        *,
        direction_id: str | None,
        trip_id: str | None,
    ) -> Trip:
        self.get_line(route_id)
        for row in self._iter_rows("trips.txt"):
            if row.get("route_id") != route_id:
                continue
            if trip_id is not None and row.get("trip_id") != trip_id:
                continue
            if direction_id is not None and row.get("direction_id") != direction_id:
                continue
            return self._trip_from_row(row)
        raise ResourceNotFoundError(
            "Nenhuma viagem corresponde aos filtros informados.",
            {"route_id": route_id, "direction_id": direction_id, "trip_id": trip_id},
        )

    def _path(self, filename: str) -> Path:
        path = self.data_dir / filename
        if not path.is_file():
            raise DataSourceUnavailableError(
                f"Arquivo GTFS '{filename}' indisponível.",
                {"filename": filename},
            )
        return path

    def _read_rows(self, filename: str) -> list[dict[str, str]]:
        return list(self._iter_rows(filename))

    def _iter_rows(self, filename: str) -> Iterator[dict[str, str]]:
        with self._path(filename).open("r", encoding="utf-8-sig", newline="") as file:
            yield from csv.DictReader(file)

    @staticmethod
    def _line_from_row(row: dict[str, str]) -> Line:
        return Line(
            route_id=row["route_id"],
            route_short_name=row.get("route_short_name") or None,
            route_long_name=row.get("route_long_name") or None,
            route_type=GtfsService._optional_int(row.get("route_type")),
            route_color=row.get("route_color") or None,
            route_text_color=row.get("route_text_color") or None,
        )

    @staticmethod
    def _stop_from_row(row: dict[str, str]) -> Stop:
        return Stop(
            stop_id=row["stop_id"],
            stop_code=row.get("stop_code") or None,
            stop_name=row.get("stop_name") or "Ponto sem nome",
            stop_lat=GtfsService._required_float(row.get("stop_lat")),
            stop_lon=GtfsService._required_float(row.get("stop_lon")),
            wheelchair_boarding=GtfsService._optional_int(row.get("wheelchair_boarding")),
        )

    @staticmethod
    def _trip_from_row(row: dict[str, str]) -> Trip:
        return Trip(
            route_id=row["route_id"],
            service_id=row.get("service_id") or None,
            trip_id=row["trip_id"],
            trip_headsign=row.get("trip_headsign") or None,
            direction_id=row.get("direction_id") or None,
            shape_id=row.get("shape_id") or None,
        )

    @staticmethod
    def _optional_int(value: str | None) -> int | None:
        return int(value) if value not in (None, "") else None

    @staticmethod
    def _required_int(value: str | None) -> int:
        return int(value or 0)

    @staticmethod
    def _required_float(value: str | None) -> float:
        return float(value or 0)
