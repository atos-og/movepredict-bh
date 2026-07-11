from pathlib import Path
import csv


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    shapes_file = project_root / "data-exploration" / "data" / "raw" / "shapes.txt"

    print("MovePredict BH — Inspect GTFS Shapes")
    print("------------------------------------")

    if not shapes_file.exists():
        print(f"Arquivo não encontrado: {shapes_file}")
        print(
            "\nAntes de rodar este script com dados reais, é necessário baixar e extrair o GTFS em:"
        )
        print("data-exploration/data/raw/")
        return

    with shapes_file.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        print("Campos encontrados:")
        print(reader.fieldnames)

        print("\nPrimeiros registros encontrados:")

        count = 0

        for row in reader:
            shape_id = row.get("shape_id", "")
            shape_pt_lat = row.get("shape_pt_lat", "")
            shape_pt_lon = row.get("shape_pt_lon", "")
            shape_pt_sequence = row.get("shape_pt_sequence", "")

            print(
                f"- shape_id={shape_id} | "
                f"lat={shape_pt_lat} | "
                f"lon={shape_pt_lon} | "
                f"sequence={shape_pt_sequence}"
            )

            count += 1

            if count >= 10:
                break

    print("\nInspeção finalizada.")


if __name__ == "__main__":
    main()
