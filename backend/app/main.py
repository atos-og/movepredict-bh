from pathlib import Path
import csv
from fastapi import FastAPI, HTTPException
from app.services.gtfs_service import list_lines

from fastapi import FastAPI, HTTPException

app = FastAPI(title="MovePredict BH API")


def get_project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def get_raw_data_dir() -> Path:
    project_root = get_project_root()
    return project_root / "data-exploration" / "data" / "raw"


def read_gtfs_csv(file_name: str) -> list[dict[str, str]]:
    file_path = get_raw_data_dir() / file_name

    if not file_path.exists():
        raise FileNotFoundError(
            f"Arquivo não encontrado: {file_path}. "
            "Baixe e extraia o GTFS antes de rodar este endpoint."
        )

    with file_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        return list(reader)


@app.get("/")
def root():
    return {
        "message": "MovePredict BH API",
        "status": "running",
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok",
    }


@app.get("/pontos")
def listar_pontos_mockados():
    return [
        {
            "id": 1,
            "nome": "Ponto de teste 1",
            "latitude": -23.55052,
            "longitude": -46.633308,
        },
        {
            "id": 2,
            "nome": "Ponto de teste 2",
            "latitude": -22.906847,
            "longitude": -43.172897,
        },
    ]


@app.get("/lines")
def list_lines(limit: int = 20):
    try:
        routes = read_gtfs_csv("routes.txt")
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))

    result = []

    for route in routes[:limit]:
        result.append(
            {
                "route_id": route.get("route_id", ""),
                "short_name": route.get("route_short_name", ""),
                "long_name": route.get("route_long_name", ""),
            }
        )

    return {
        "total_returned": len(result),
        "lines": result,
    }
@app.get("/lines")
def get_lines():
    try:
        return list_lines()
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))