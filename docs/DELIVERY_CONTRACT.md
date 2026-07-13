# Contrato de entrega — dados, posições e ETA

**Versao publica:** `v1`, fechada em 13/07/2026. Alteracoes futuras devem ser aditivas ou receber
uma nova versao documentada.

## Fronteira de responsabilidade

Esta entrega não altera routers, frontend, `VehiclePosition`, `ArrivalPrediction` nem os Protocols
públicos. A integração entra exclusivamente pelos adaptadores:

- `SqlVehiclePositionProvider`, que implementa `VehiclePositionProvider`;
- `SqlArrivalPredictionProvider`, que implementa `ArrivalPredictionProvider`.

Os adaptadores retornam schemas Pydantic existentes e nunca expõem as chaves inteiras internas do
banco. Timestamps retornados estão em UTC. Conversão para `America/Sao_Paulo` pertence à camada de
apresentação.

## Contrato de `VehiclePositionProvider`

```python
list_current_positions(route_id: str | None = None) -> list[VehiclePosition]
```

- `route_id`: `routes.txt.route_id`, nunca o número comercial nem `NL` da PBH;
- `vehicle_id`: campo `NV` do feed oficial;
- `trip_id`: `trips.txt.trip_id` quando a inferência estiver validada; caso contrário, `null`;
- `observed_at`: horário `HR` da fonte convertido de São Paulo para UTC;
- posição mais recente por veículo ativo;
- `status`: `stopped` até 1 km/h, `in_transit` acima disso e `unknown` sem velocidade.

## Contrato de `ArrivalPredictionProvider`

```python
predict_arrivals(
    stop_id: str,
    route_id: str | None = None,
    at: datetime | None = None,
) -> list[ArrivalPrediction]
```

- `stop_id`: `stops.txt.stop_id`;
- `route_id`: `routes.txt.route_id`;
- `trip_id`: `trips.txt.trip_id` ou `null`;
- `vehicle_id`: `NV` da PBH ou `null`;
- `generated_at` e `predicted_arrival`: UTC;
- `model_version`: obrigatório nos registros persistidos;
- `uncertainty_seconds`: incerteza simétrica aproximada em segundos;
- resultados ordenados por chegada prevista e filtrados a partir de `at`.

## Envelope realtime

Os endpoints retornam `data` e `meta`. `meta.status` e um enum fechado:

- `live`: existe pelo menos um item dentro do limite de frescor;
- `empty`: nao existe item aplicavel, sem evidencia de dado antigo descartado;
- `stale`: a fonte possui dados, mas o item mais novo ultrapassou `stale_after_seconds`.

`meta.count` sempre corresponde ao tamanho de `data`. `meta.stale` e verdadeiro somente quando
`status` e `stale`. Falha de banco ou provider nao usa esses estados: responde HTTP 503 no envelope
padrao de erro.

## Mapeamento de IDs

| Origem | Campo externo | Persistência | Campo público | Regra |
| --- | --- | --- | --- | --- |
| PBH tempo real | `NV` | `vehicles.source_vehicle_id` | `vehicle_id` | identidade exata |
| PBH tempo real | `NL` | `route_source_codes.source_code` | — | código operacional bruto |
| Conversão PBH | `Linha` | `route_source_codes.public_line_code` | — | número/variante comercial |
| GTFS | `routes.route_id` | `transit_routes.gtfs_route_id` | `route_id` | igualdade exata após conversão validada |
| GTFS | `trips.trip_id` | `transit_trips.gtfs_trip_id` | `trip_id` | inferido por linha, sentido, serviço, horário e shape |
| GTFS | `stops.stop_id` | `transit_stops.gtfs_stop_id` | `stop_id` | usado em programação e previsão |

O fallback de linha remove somente o sufixo operacional após `-` e zeros à esquerda. Se mais de uma
linha GTFS continuar possível, `route_id` fica nulo. O sistema preserva `NL` para auditoria.

`trip_id` não é inventado. A inferência implementada exige, em conjunto:

1. linha já associada;
2. compatibilidade de `SV` 1/2 com `direction_id` 0/1 quando o sentido está disponível;
3. serviço ativo no calendário;
4. janela do horário programado;
5. proximidade ao shape e progressão coerente;
6. pontuação mínima e diferença suficiente para o segundo melhor candidato.

O matching registra `route-direction-calendar-time-shape-v1`, confiança e progressão no shape.
Casos ambíguos ou fracos são marcados como rejeitados e permanecem sem viagem. `stop_id` entra pelo
GTFS; a chegada é rotulada por proximidade, baixa velocidade e aproximação ao ponto.

## Timestamps

- `observed_at`: instante da fonte (`HR`), convertido de `America/Sao_Paulo` para UTC;
- `ingested_at`: relógio UTC do consumidor depois do download e antes da persistência;
- `generated_at`: instante UTC de geração da previsão;
- `actual_arrival`: chegada real rotulada em UTC;
- `America/Sao_Paulo`: somente apresentação e segmentação por faixa horária local.

## Exemplo real compatível

Veja `docs/examples/vehicle-position.json`. Ele foi produzido pelo adaptador SQL a partir de uma
posição oficial coletada em 11/07/2026. `trip_id` é nulo intencionalmente.
`arrival-prediction.json` e um fixture de desenvolvimento e nao deve ser apresentado como medicao
real. Uma previsao somente vira evidencia real depois de receber `actual_arrival` no banco.

## Critério de aceite

- migrations aplicam do zero em PostgreSQL/PostGIS;
- consumidor executa com retry, backoff, timeout e idempotência;
- coleta registra métricas e desaparecimento;
- histórico respeita retenção configurável;
- adaptadores retornam os schemas públicos existentes;
- testes unitários e de integração PostgreSQL passam;
- ETA possui baseline versionada e avaliação temporal sem vazamento;
- associação de viagem, geração de ETA e detecção de chegada rodam no pipeline periódico;
- nenhum segredo ou `.env` real é versionado.
