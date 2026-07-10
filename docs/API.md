# API - MovePredict BH

Base local: `http://localhost:8000`. OpenAPI: `/docs` e `/openapi.json`.

## Formato das respostas

Recursos individuais usam:

```json
{ "data": { "route_id": "561787" } }
```

Coleções paginadas usam:

```json
{
  "data": [],
  "meta": { "total": 0, "returned": 0, "limit": 50, "offset": 0 }
}
```

Erros usam:

```json
{
  "error": {
    "code": "resource_not_found",
    "message": "Linha 'x' não encontrada.",
    "request_id": "...",
    "details": { "route_id": "x" }
  }
}
```

O cabeçalho `X-Request-ID` é aceito e devolvido em todas as respostas.

## Endpoints

### `GET /`

Identificação e versão da API.

### `GET /health`

Liveness da aplicação. Não valida banco ou provedor externo.

### `GET /lines`

Lista linhas. Parâmetros:

- `q`: busca em ID, número e nome.
- `route_type`: filtro pelo tipo GTFS.
- `limit`: 1 a 200, padrão 50.
- `offset`: deslocamento, padrão 0.

### `GET /lines/{route_id}`

Retorna os dados de uma linha.

### `GET /lines/{route_id}/stops`

Retorna a sequência de pontos de uma viagem representativa. Aceita `direction_id` (`0` ou `1`) e `trip_id` para seleção explícita.

### `GET /lines/{route_id}/route`

Retorna o trajeto como GeoJSON `LineString`. Aceita `direction_id` e `trip_id`.

### `GET /lines/{route_id}/trips`

Endpoint auxiliar preservado do trabalho anterior. Aceita `direction_id`, `limit` e `offset`.

### `GET /stops`

Lista pontos. Parâmetros:

- `q`: busca em ID, código e nome.
- `min_lat`, `max_lat`, `min_lon`, `max_lon`: caixa geográfica.
- `limit`: 1 a 200, padrão 50.
- `offset`: deslocamento, padrão 0.

### `GET /stops/{stop_id}`

Retorna os dados e coordenadas de um ponto.

## Códigos de erro

- `404 resource_not_found`: linha, ponto, viagem ou shape inexistente.
- `404 http_error`: rota HTTP inexistente, incluindo o removido `/pontos`.
- `422 validation_error`: parâmetros inválidos.
- `503 data_source_unavailable`: arquivo GTFS necessário não está disponível.

## Interfaces futuras

Posições e previsões não têm endpoints ativos nesta etapa. Os contratos estão em `backend/app/schemas/realtime.py` e `backend/app/services/provider_contracts.py`. A implementação de Vinicius deverá satisfazer esses contratos antes da exposição HTTP.
