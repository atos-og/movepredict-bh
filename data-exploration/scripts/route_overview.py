import argparse
from collections import Counter

from gtfs_utils import (
    describe_route,
    find_routes,
    index_rows,
    iter_gtfs_csv,
    read_gtfs_csv,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Resume linhas, viagens, pontos e traçados.")
    parser.add_argument("query", help="route_id, número ou nome da linha")
    args = parser.parse_args()
    routes = find_routes(args.query)
    if not routes:
        raise SystemExit(f"Nenhuma linha encontrada para: {args.query}")

    trips_by_route = index_rows(read_gtfs_csv("trips.txt"), "route_id")
    for route in routes:
        trips = trips_by_route.get(route["route_id"], [])
        trip_ids = {trip["trip_id"] for trip in trips}
        stop_ids = {
            stop_time["stop_id"]
            for stop_time in iter_gtfs_csv("stop_times.txt")
            if stop_time.get("trip_id") in trip_ids
        }
        shapes = {trip.get("shape_id", "") for trip in trips if trip.get("shape_id")}
        directions = Counter(trip.get("direction_id", "") for trip in trips)
        services = {trip.get("service_id", "") for trip in trips}
        print(f"\n{describe_route(route)}")
        print(f"- viagens: {len(trips)}")
        print(f"- sentidos: {dict(sorted(directions.items()))}")
        print(f"- serviços: {len(services)}")
        print(f"- pontos únicos: {len(stop_ids)}")
        print(f"- traçados únicos: {len(shapes)}")


if __name__ == "__main__":
    main()
