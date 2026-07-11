from pathlib import Path
import csv


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    stops_file = project_root / "data-exploration" / "data" / "raw" / "stops.txt"

    print("MovePredict BH — Inspect GTFS Stops")
    print("-----------------------------------")

    if not stops_file.exists():
        print(f"Arquivo não encontrado: {stops_file}")
        print(
            "\nAntes de rodar este script com dados reais, é necessário baixar e extrair o GTFS em:"
        )
        print("data-exploration/data/raw/")
        return

    with stops_file.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        stops = list(reader)

    print(f"Total de pontos encontrados: {len(stops)}")
    print("\nPrimeiros pontos encontrados:")

    for stop in stops[:10]:
        stop_id = stop.get("stop_id", "")
        stop_name = stop.get("stop_name", "")
        stop_lat = stop.get("stop_lat", "")
        stop_lon = stop.get("stop_lon", "")

        print(f"- {stop_id} | {stop_name} | lat={stop_lat} | lon={stop_lon}")


if __name__ == "__main__":
    main()
