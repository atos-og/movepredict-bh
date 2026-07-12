import argparse

from gtfs_utils import read_gtfs_csv


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspeciona viagens do GTFS.")
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()
    trips = read_gtfs_csv("trips.txt")

    print(f"Total de viagens: {len(trips)}")
    for trip in trips[: max(args.limit, 0)]:
        print(
            "- trip_id={trip_id} | route_id={route_id} | sentido={direction_id} | "
            "destino={trip_headsign} | shape_id={shape_id} | service_id={service_id}".format(
                **trip
            )
        )


if __name__ == "__main__":
    main()
