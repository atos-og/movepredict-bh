from fastapi import FastAPI, HTTPException

from app.services.gtfs_service import list_lines, list_stops

app = FastAPI(title="MovePredict BH API")


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
def get_lines():
    try:
        lines = list_lines()
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))

    return {
        "total_returned": len(lines),
        "lines": lines,
    }


@app.get("/stops")
def get_stops():
    try:
        stops = list_stops()
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))

    return {
        "total_returned": len(stops),
        "stops": stops,
    }