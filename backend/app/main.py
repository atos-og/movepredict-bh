from fastapi import FastAPI

app = FastAPI(title="API do Projeto")


@app.get("/")
def inicio():
    return {"mensagem": "Backend funcionando!"}


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
