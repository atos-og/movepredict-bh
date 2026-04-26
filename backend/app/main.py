from fastapi import FastAPI

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
def listar_pontos():
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


