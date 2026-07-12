import argparse

from gtfs_utils import describe_route, find_routes


def main() -> None:
    parser = argparse.ArgumentParser(description="Busca linhas no GTFS da PBH.")
    parser.add_argument("query", help="route_id, número ou parte do nome da linha")
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()

    routes = find_routes(args.query)
    print(f"Linhas encontradas: {len(routes)}")
    for route in routes[: max(args.limit, 0)]:
        print(f"- {describe_route(route)}")


if __name__ == "__main__":
    main()
