import os
import zipfile
from pathlib import Path
from urllib.request import urlretrieve


EXPECTED_GTFS_FILES = [
    "routes.txt",
    "stops.txt",
    "trips.txt",
    "stop_times.txt",
    "shapes.txt",
]


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
        print(
            '$env:PBH_GTFS_URL="https://s3.amazonaws.com/mobilibus-uploads/gtfs/GTFSBHTRANS.zip"'
        )
        return

    zip_file = raw_data_dir / "gtfs_pbh.zip"

    print("MovePredict BH — Download GTFS")
    print("------------------------------")
    print(f"URL: {gtfs_url}")
    print(f"Destino: {zip_file}")

    try:
        urlretrieve(gtfs_url, zip_file)
    except Exception as error:
        print("")
        print("Erro ao baixar o arquivo GTFS.")
        print(f"Detalhes: {error}")
        return

    print("")
    print("[OK] Download concluído.")
    print(f"Arquivo salvo em: {zip_file}")

    print("")
    print("Extraindo arquivos do GTFS...")

    try:
        with zipfile.ZipFile(zip_file, "r") as zip_ref:
            zip_ref.extractall(raw_data_dir)
    except zipfile.BadZipFile:
        print("Erro: o arquivo baixado não parece ser um ZIP válido.")
        return
    except Exception as error:
        print("Erro ao extrair o ZIP.")
        print(f"Detalhes: {error}")
        return

    print("")
    print("Verificando arquivos esperados:")

    for file_name in EXPECTED_GTFS_FILES:
        file_path = raw_data_dir / file_name

        if file_path.exists():
            print(f"[OK] {file_name}")
        else:
            print(f"[MISSING] {file_name}")

    print("")
    print("[OK] Processo finalizado.")


if __name__ == "__main__":
    main()