from pathlib import Path
import csv


def get_project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def get_raw_data_dir() -> Path:
    project_root = get_project_root()
    return project_root / "data-exploration" / "data" / "raw"


def read_gtfs_csv(file_name: str) -> list[dict[str, str]]:
    raw_data_dir = get_raw_data_dir()
    file_path = raw_data_dir / file_name

    if not file_path.exists():
        raise FileNotFoundError(
            f"Arquivo não encontrado: {file_path}. "
            "Baixe e extraia o GTFS antes de rodar este script."
        )

    with file_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        return list(reader)