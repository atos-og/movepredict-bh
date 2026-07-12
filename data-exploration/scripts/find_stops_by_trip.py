import argparse

from gtfs_utils import iter_gtfs_csv, numeric, read_gtfs_csv


def stops_for_trip(trip_id: str) -> list[dict[str, str]]:
    stop_times = [
        row for row in iter_gtfs_csv("stop_times.txt") if row.get("trip_id") == trip_id
    ]
    stops = {row["stop_id"]: row for row in read_gtfs_csv("stops.txt")}
    result = []
    for stop_time in sorted(
        stop_times, key=lambda row: numeric(row.get("stop_sequence", ""))
    ):
        result.append({**stop_time, **stops.get(stop_time.get("stop_id", ""), {})})
    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Lista os pontos de uma viagem na ordem."
    )
    parser.add_argument("trip_id")
    args = parser.parse_args()
    stops = stops_for_trip(args.trip_id)
    if not stops:
        raise SystemExit(f"Viagem sem pontos ou inexistente: {args.trip_id}")
    print(f"Viagem {args.trip_id} — {len(stops)} paradas")
    for stop in stops:
        print(
            f"- {stop.get('stop_sequence', '')}: {stop.get('stop_id', '')} | "
            f"{stop.get('stop_name', '')} | chegada={stop.get('arrival_time', '')}"
        )


if __name__ == "__main__":
    main()
