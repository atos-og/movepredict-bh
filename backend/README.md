# Backend

API FastAPI do MovePredict BH. A aplicação lê GTFS estático por meio de `GtfsService`, isolando o transporte HTTP da fonte de dados.

## Instalação

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

## Configuração

| Variável | Padrão | Uso |
| --- | --- | --- |
| `MOVEPREDICT_ENVIRONMENT` | `development` | Identifica o ambiente. |
| `MOVEPREDICT_GTFS_DATA_DIR` | `../data-exploration/data/raw` | Diretório dos arquivos GTFS extraídos. |
| `MOVEPREDICT_CORS_ORIGINS` | URLs locais do frontend | Origens permitidas, separadas por vírgula. |

## Estrutura

```text
app/main.py                 criação da aplicação e handlers globais
app/routers/                endpoints HTTP
app/schemas/                contratos Pydantic
app/services/gtfs_service.py leitura e consulta do GTFS
app/services/provider_contracts.py interfaces futuras
tests/                      testes isolados com GTFS mínimo
```

## Testes

```powershell
pytest
ruff check app tests
ruff format --check app tests
```
