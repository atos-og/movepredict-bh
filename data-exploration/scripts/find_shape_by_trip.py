import argparse

from gtfs_utils import index_rows, numeric, read_gtfs_csv


def main() -> None:
    parser = argparse.ArgumentParser(description="Localiza o traçado de uma viagem.")
    parser.add_argument("trip_id")
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()
    trip = next(
        (row for row in read_gtfs_csv("trips.txt") if row.get("trip_id") == args.trip_id),
        None,
    )
    if not trip:
        raise SystemExit(f"Viagem inexistente: {args.trip_id}")
    shape_id = trip.get("shape_id", "")
    points = index_rows(read_gtfs_csv("shapes.txt"), "shape_id").get(shape_id, [])
    points.sort(key=lambda row: numeric(row.get("shape_pt_sequence", "")))
    print(f"Viagem {args.trip_id} | shape={shape_id} | {len(points)} pontos")
    for point in points[: max(args.limit, 0)]:
        print(
            f"- {point.get('shape_pt_sequence', '')}: "
            f"{point.get('shape_pt_lat', '')},{point.get('shape_pt_lon', '')} | "
            f"distância={point.get('shape_dist_traveled', '')}"
        )


if __name__ == "__main__":
    main()
