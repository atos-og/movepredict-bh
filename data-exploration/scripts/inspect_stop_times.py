from pathlib import Path
import csv


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    stop_times_file = (
        project_root / "data-exploration" / "data" / "raw" / "stop_times.txt"
    )

    print("MovePredict BH — Inspect GTFS Stop Times")
    print("----------------------------------------")

    if not stop_times_file.exists():
        print(f"Arquivo não encontrado: {stop_times_file}")
        print(
            "\nAntes de rodar este script com dados reais, é necessário baixar e extrair o GTFS em:"
        )
        print("data-exploration/data/raw/")
        return

    with stop_times_file.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        print("Campos encontrados:")
        print(reader.fieldnames)

        print("\nPrimeiros registros encontrados:")

        count = 0

        for row in reader:
            trip_id = row.get("trip_id", "")
            arrival_time = row.get("arrival_time", "")
            departure_time = row.get("departure_time", "")
            stop_id = row.get("stop_id", "")
            stop_sequence = row.get("stop_sequence", "")

            print(
                f"- trip_id={trip_id} | "
                f"arrival={arrival_time} | "
                f"departure={departure_time} | "
                f"stop_id={stop_id} | "
                f"sequence={stop_sequence}"
            )

            count += 1

            if count >= 10:
                break

    print("\nInspeção finalizada.")


if __name__ == "__main__":
    main()
