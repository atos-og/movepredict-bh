import argparse

from gtfs_utils import describe_route, find_routes, index_rows, read_gtfs_csv


def main() -> None:
    parser = argparse.ArgumentParser(description="Lista viagens associadas a uma linha.")
    parser.add_argument("query", help="route_id, número ou nome da linha")
    parser.add_argument("--limit", type=int, default=30)
    args = parser.parse_args()

    routes = find_routes(args.query)
    if not routes:
        raise SystemExit(f"Nenhuma linha encontrada para: {args.query}")
    trips_by_route = index_rows(read_gtfs_csv("trips.txt"), "route_id")

    for route in routes:
        trips = trips_by_route.get(route["route_id"], [])
        print(f"\n{describe_route(route)} — {len(trips)} viagens")
        for trip in trips[: max(args.limit, 0)]:
            print(
                f"- {trip['trip_id']} | sentido={trip.get('direction_id', '')} | "
                f"destino={trip.get('trip_headsign', '')} | shape={trip.get('shape_id', '')}"
            )


if __name__ == "__main__":
    main()
