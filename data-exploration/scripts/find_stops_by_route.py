import argparse

from gtfs_utils import (
    describe_route,
    find_routes,
    index_rows,
    iter_gtfs_csv,
    read_gtfs_csv,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Lista pontos atendidos por uma linha."
    )
    parser.add_argument("query", help="route_id, número ou nome da linha")
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()

    routes = find_routes(args.query)
    if not routes:
        raise SystemExit(f"Nenhuma linha encontrada para: {args.query}")
    trips_by_route = index_rows(read_gtfs_csv("trips.txt"), "route_id")
    stops = {row["stop_id"]: row for row in read_gtfs_csv("stops.txt")}

    for route in routes:
        trip_ids = {
            trip["trip_id"] for trip in trips_by_route.get(route["route_id"], [])
        }
        ordered_ids: dict[str, None] = {}
        for stop_time in iter_gtfs_csv("stop_times.txt"):
            if stop_time.get("trip_id") in trip_ids:
                ordered_ids.setdefault(stop_time["stop_id"], None)
        print(f"\n{describe_route(route)} — {len(ordered_ids)} pontos únicos")
        for stop_id in list(ordered_ids)[: max(args.limit, 0)]:
            stop = stops.get(stop_id, {})
            print(f"- {stop_id} | {stop.get('stop_name', '')}")


if __name__ == "__main__":
    main()
