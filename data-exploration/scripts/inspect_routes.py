from pathlib import Path
import csv


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    routes_file = project_root / "data-exploration" / "data" / "raw" / "routes.txt"

    print("MovePredict BH — Inspect GTFS Routes")
    print("------------------------------------")

    if not routes_file.exists():
        print(f"Arquivo não encontrado: {routes_file}")
        print("\nAntes de rodar este script com dados reais, é necessário baixar e extrair o GTFS em:")
        print("data-exploration/data/raw/")
        return

    with routes_file.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        routes = list(reader)

    print(f"Total de linhas encontradas: {len(routes)}")
    print("\nPrimeiras linhas encontradas:")

    for route in routes[:10]:
        route_id = route.get("route_id", "")
        route_short_name = route.get("route_short_name", "")
        route_long_name = route.get("route_long_name", "")

        print(f"- {route_id} | {route_short_name} | {route_long_name}")


if __name__ == "__main__":
    main()