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
| Favoritos de linhas e pontos | `localStorage`, sem envio de dados pessoais |

## Requer serviço externo ou novo adaptador

### Busca por destino

Termos como bairros, hospitais, estádios, lojas e endereços precisam de um serviço de
geocodificação. O contrato `DestinationProvider` está definido em `types/mobility.ts` e o adaptador
substituível em `lib/adapters/geocoding.ts`. Nenhum provedor ou chave foi escolhido nesta etapa.

### Planejamento de viagem

Melhor linha, baldeações, caminho a pé, duração total e rotas alternativas exigem um motor de
roteamento com GTFS e rede viária. O contrato `JourneyPlannerProvider` está definido em
`types/mobility.ts` e o adaptador substituível em `lib/adapters/journey-planner.ts`.

## Requer exposição de novos dados pela API

- linhas que atendem um ponto, idealmente por um recurso equivalente a `/stops/{stop_id}/lines`;
- posições atuais de veículos usando o contrato `VehiclePosition`;
- previsões por ponto e linha usando o contrato `ArrivalPrediction`;
- alertas e indisponibilidades de serviço, caso essa fonte seja adicionada.

Os nomes de endpoints acima são sugestões de integração, não alterações realizadas no backend.
Os contratos de tempo real existentes foram preservados em `types/realtime.ts`. O componente
`components/map/moving-bus-marker.tsx` já aceita posição, identificação e direção reais, mas nenhum
veículo é exibido até que um provedor GTFS-Realtime seja conectado.

## Preview visual e regressão

As telas de rota e viagem que dependem dessas integrações possuem fixtures exclusivamente em
`lib/preview/roadmap-fixtures.ts`. Elas só são habilitadas por `?preview=1` durante desenvolvimento;
o build de produção ignora o parâmetro e mostra o estado honesto de integração pendente.

Os testes em `tests/visual` cobrem as 12 telas do roadmap em `390 × 844` e verificam a Home também
em `360 × 800`, `375 × 812` e `414 × 896`. Durante screenshots, apenas os tiles raster externos do
OpenStreetMap são ocultados para evitar diferenças de rede; marcadores, trajetos e ônibus continuam
sendo comparados.
