# API MovePredict BH

Base local: `http://localhost:8000`. OpenAPI: `/docs` e `/openapi.json`.

## Contratos

Recursos individuais usam `{ "data": {...} }`. Colecoes paginadas retornam `data` e
`meta` com `total`, `returned`, `limit` e `offset`. Erros seguem o envelope:

```json
{
  "error": {
    "code": "resource_not_found",
    "message": "Recurso nao encontrado.",
    "request_id": "...",
    "details": {}
  }
}
```

Todas as respostas recebem `X-Request-ID`, `Server-Timing` e cabecalhos basicos de
seguranca.

## Sistema

- `GET /`: identificacao e versao.
- `GET /health`: liveness; nao consulta dependencias.
- `GET /ready`: readiness; valida PostgreSQL.
- `GET /metrics`: metricas Prometheus, omitido do OpenAPI.

## Linhas

- `GET /lines`: `q`, `route_type`, `limit` e `offset`.
- `GET /lines/{route_id}`: detalhes da linha.
- `GET /lines/{route_id}/stops`: `direction_id` e `trip_id` opcionais.
- `GET /lines/{route_id}/route`: GeoJSON `LineString`.
- `GET /lines/{route_id}/trips`: viagens paginadas.

## Pontos

- `GET /stops`: `q`, caixa geografica, `limit` e `offset`.
- `GET /stops/{stop_id}`: detalhes e coordenadas.

## Tempo real

### `GET /realtime/vehicles`

Retorna a posicao mais recente de veiculos ativos. Parametros: `route_id`, `limit`
(ate 2.000) e `max_age_seconds`. Posicoes anteriores ao limite de frescor sao omitidas.

### `GET /realtime/stops/{stop_id}/arrivals`

Retorna previsoes futuras ordenadas por horario. Parametros: `route_id`, `limit` e
`max_age_seconds`. `meta.stale` impede que uma previsao antiga seja apresentada como atual.

Uma lista vazia e uma resposta valida quando nao ha veiculos recentes ou previsoes futuras.
`meta.status` possui contrato fechado: `live` indica dados atuais, `empty` indica que a fonte nao
retornou itens aplicaveis e `stale` indica que havia dados, mas eles ultrapassaram o limite de
frescor. `meta.stale` permanece como atalho booleano compativel e equivale a
`meta.status == "stale"`.

## Erros

- `404 resource_not_found`: recurso GTFS inexistente.
- `404 http_error`: rota HTTP inexistente.
- `422 validation_error`: parametros invalidos.
- `503 data_source_unavailable`: GTFS indisponivel.
- `503 database_unavailable`: PostgreSQL/PostGIS indisponivel.
