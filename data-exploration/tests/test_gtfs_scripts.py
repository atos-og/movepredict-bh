import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import find_stops_by_trip  # noqa: E402
from gtfs_utils import index_rows, normalize, numeric  # noqa: E402


def test_gtfs_helpers_normalize_index_and_sort_values() -> None:
    assert normalize("  Linha   SÃO Pedro ") == "linha são pedro"
    assert numeric("12") == 12
    assert numeric("") == 0
    assert index_rows([{"route_id": "1"}, {"route_id": "1"}], "route_id") == {
        "1": [{"route_id": "1"}, {"route_id": "1"}]
    }


def test_stops_for_trip_joins_and_orders_stop_times(monkeypatch) -> None:
    fixtures = {
        "stop_times.txt": [
            {"trip_id": "T1", "stop_id": "B", "stop_sequence": "2"},
            {"trip_id": "T1", "stop_id": "A", "stop_sequence": "1"},
        ],
        "stops.txt": [
            {"stop_id": "A", "stop_name": "Primeiro"},
            {"stop_id": "B", "stop_name": "Segundo"},
        ],
    }
    monkeypatch.setattr(find_stops_by_trip, "read_gtfs_csv", fixtures.__getitem__)
    monkeypatch.setattr(find_stops_by_trip, "iter_gtfs_csv", lambda name: iter(fixtures[name]))

    result = find_stops_by_trip.stops_for_trip("T1")

    assert [stop["stop_id"] for stop in result] == ["A", "B"]
    assert [stop["stop_name"] for stop in result] == ["Primeiro", "Segundo"]
