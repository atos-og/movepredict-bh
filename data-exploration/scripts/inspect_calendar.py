import csv
from pathlib import Path


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    calendar_file = project_root / "data-exploration" / "data" / "raw" / "calendar.txt"

    print("MovePredict BH — Inspect GTFS Calendar")
    print("--------------------------------------")

    if not calendar_file.exists():
        print(f"Arquivo não encontrado: {calendar_file}")
        print(
            "\nAntes de rodar este script com dados reais, é necessário baixar e extrair o GTFS em:"
        )
        print("data-exploration/data/raw/")
        return

    with calendar_file.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        print("Campos encontrados:")
        print(reader.fieldnames)

        print("\nPrimeiros registros encontrados:")

        for index, row in enumerate(reader):
            service_id = row.get("service_id", "")
            monday = row.get("monday", "")
            tuesday = row.get("tuesday", "")
            wednesday = row.get("wednesday", "")
            thursday = row.get("thursday", "")
            friday = row.get("friday", "")
            saturday = row.get("saturday", "")
            sunday = row.get("sunday", "")
            start_date = row.get("start_date", "")
            end_date = row.get("end_date", "")

            print(
                f"- service_id={service_id} | "
                f"seg={monday} ter={tuesday} qua={wednesday} qui={thursday} "
                f"sex={friday} sab={saturday} dom={sunday} | "
                f"start={start_date} | end={end_date}"
            )

            if index >= 9:
                break

    print("\nInspeção finalizada.")


if __name__ == "__main__":
    main()
