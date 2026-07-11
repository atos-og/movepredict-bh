# Integrações pendentes do frontend

O frontend usa somente dados reais disponíveis na API atual. Valores ausentes não são simulados.

## Suportado hoje

| Recurso | Fonte |
| --- | --- |
| Linhas e busca por linha | `GET /lines` |
| Pontos e busca por ponto | `GET /stops` |
| Pontos próximos | `GET /stops` com `min_lat`, `max_lat`, `min_lon` e `max_lon` |
| Sentidos disponíveis | `GET /lines/{route_id}/trips` |
| Sequência de pontos | `GET /lines/{route_id}/stops` |
| Geometria do trajeto | `GET /lines/{route_id}/route` |
| Posição do usuário | API de geolocalização do navegador |
| Distância até um ponto | cálculo Haversine no frontend, identificado como linha reta |

## Requer serviço externo ou novo adaptador

### Busca por destino

Termos como bairros, hospitais, estádios, lojas e endereços precisam de um serviço de
geocodificação. O contrato `DestinationProvider` está definido em `types/mobility.ts`. Nenhum
provedor ou chave foi escolhido nesta etapa.

### Planejamento de viagem

Melhor linha, baldeações, caminho a pé, duração total e rotas alternativas exigem um motor de
roteamento com GTFS e rede viária. O contrato `JourneyPlannerProvider` está definido em
`types/mobility.ts`.

## Requer exposição de novos dados pela API

- linhas que atendem um ponto, idealmente por um recurso equivalente a `/stops/{stop_id}/lines`;
- posições atuais de veículos usando o contrato `VehiclePosition`;
- previsões por ponto e linha usando o contrato `ArrivalPrediction`;
- alertas e indisponibilidades de serviço, caso essa fonte seja adicionada.

Os nomes de endpoints acima são sugestões de integração, não alterações realizadas no backend.
Os contratos de tempo real existentes foram preservados em `types/realtime.ts`.
