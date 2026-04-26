import os
from pathlib import Path
from urllib.request import urlretrieve


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    raw_data_dir = project_root / "data-exploration" / "data" / "raw"

    raw_data_dir.mkdir(parents=True, exist_ok=True)

    gtfs_url = os.getenv("PBH_GTFS_URL")

    if not gtfs_url:
        print("Erro: variável de ambiente PBH_GTFS_URL não foi definida.")
        print("Defina a URL direta do arquivo GTFS antes de rodar o script.")
        print("")
        print("Exemplo no PowerShell:")
        print('$env:PBH_GTFS_URL="COLE_A_URL_DIRETA_DO_GTFS_AQUI"')
        return

    output_file = raw_data_dir / "gtfs_pbh.zip"

    print("MovePredict BH — Download GTFS")
    print("------------------------------")
    print(f"URL: {gtfs_url}")
    print(f"Destino: {output_file}")

    try:
        urlretrieve(gtfs_url, output_file)
    except Exception as error:
        print("")
        print("Erro ao baixar o arquivo GTFS.")
        print(f"Detalhes: {error}")
        return

    print("")
    print("[OK] Download concluído.")
    print(f"Arquivo salvo em: {output_file}")


if __name__ == "__main__":
    main()