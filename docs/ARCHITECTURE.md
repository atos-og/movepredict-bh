# Arquitetura - MovePredict BH

## Visão atual

```text
Arquivos GTFS da PBH
        |
        v
GtfsService (adaptador local)
        |
        v
Services -> Schemas Pydantic -> Routers FastAPI
        |
        v
Cliente HTTP tipado -> Next.js -> Leaflet
```

Routers conhecem HTTP e validação de parâmetros. Services conhecem casos de uso e fontes de dados. Schemas formam o contrato compartilhado. `main.py` cuida de CORS, request ID e erros globais.

## Fronteira com a frente de dados

```text
Coleta PBH (20 s) ---------\
PostgreSQL -----------------> providers SQL -> API -> Frontend
ETA baseline + avaliação --/
```

O pipeline de coleta, histórico e previsão inicial está descrito em `docs/DATA_PIPELINE.md`. A fronteira é definida por:

- `VehiclePositionProvider.list_current_positions(route_id)`
- `ArrivalPredictionProvider.predict_arrivals(stop_id, route_id, at)`
- schemas `VehiclePosition` e `ArrivalPrediction`

Isso permite trocar o adaptador GTFS local por consultas ao PostgreSQL sem alterar os routers ou o mapa.

## Decisões de operação

- Dados GTFS não entram na imagem Docker; são montados como volume ou fornecidos por armazenamento externo.
- A URL da API do frontend é definida no build por ser uma variável pública do Next.js.
- O health check atual é de liveness. Readiness de banco será adicionada com o PostGIS.
