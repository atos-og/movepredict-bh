from pathlib import Path


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    raw_data_dir = project_root / "data-exploration" / "data" / "raw"

    print("MovePredict BH — GTFS Files Inspection")
    print("--------------------------------------")
    print(f"Project root: {project_root}")
    print(f"Raw data directory: {raw_data_dir}")

    if not raw_data_dir.exists():
        print("\n[MISSING] A pasta data-exploration/data/raw ainda não existe.")
        print("Crie essa pasta ou confirme a estrutura do projeto.")
        return

    files = list(raw_data_dir.iterdir())

    if not files:
        print("\n[INFO] Nenhum arquivo encontrado em data-exploration/data/raw.")
        print("Próximo passo: baixar o arquivo GTFS da PBH e salvar nessa pasta.")
        return

    print("\nArquivos encontrados:")

    for file in files:
        print(f"- {file.name}")


if __name__ == "__main__":
    main()