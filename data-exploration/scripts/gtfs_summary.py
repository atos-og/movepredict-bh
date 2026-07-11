from collections import Counter

from gtfs_utils import iter_gtfs_csv, read_gtfs_csv


def main() -> None:
    files = (
        "agency.txt",
        "routes.txt",
        "trips.txt",
        "stops.txt",
        "stop_times.txt",
        "shapes.txt",
        "calendar.txt",
        "calendar_dates.txt",
    )
    counts = {name: sum(1 for _ in iter_gtfs_csv(name)) for name in files}
    trips = read_gtfs_csv("trips.txt")
    calendar = read_gtfs_csv("calendar.txt")
    print("MovePredict BH — resumo do GTFS")
    for name, count in counts.items():
        print(f"- {name}: {count} registros")

    directions = Counter(trip.get("direction_id", "") for trip in trips)
    services = {trip.get("service_id", "") for trip in trips}
    print(f"- serviços referenciados: {len(services)}")
    print(f"- viagens por sentido: {dict(sorted(directions.items()))}")
    print(f"- período do calendário: {_calendar_period(calendar)}")


def _calendar_period(calendar: list[dict[str, str]]) -> str:
    starts = [row["start_date"] for row in calendar if row.get("start_date")]
    ends = [row["end_date"] for row in calendar if row.get("end_date")]
    return f"{min(starts)} a {max(ends)}" if starts and ends else "não informado"


if __name__ == "__main__":
    main()
