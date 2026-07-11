# Pipeline de dados, histórico e ETA

## Fonte em tempo real validada

- Portal oficial: `https://dados.pbh.gov.br/dataset/tempo_real_onibus_-_coordenada`
- JSON: `https://temporeal.pbh.gov.br/?param=D`
- Fonte declarada: TRANSFÁCIL / Superintendência de Mobilidade da PBH.
- Licença declarada: Creative Commons Attribution.
- Frequência publicada: um novo arquivo a cada 20 segundos.

O consumidor envia um `User-Agent` identificável porque o servidor rejeita clientes HTTP sem essa
identificação. O processo usa timeout, retry com backoff exponencial, filtra `EV=105`, valida o
payload, deduplica por `(veículo, instante)` e mantém o código bruto de linha para auditoria.

## Dicionário do payload

| Campo | Uso |
| --- | --- |
| `EV` | tipo do evento; `105` representa posição |
| `HR` | instante local no formato `YYYYMMDDhhmmss` |
| `LT`, `LG` | latitude e longitude WGS84 |
| `NV` | identificador operacional do veículo |
| `VL` | velocidade instantânea em km/h |
| `NL` | código operacional da linha, não é `route_id` GTFS |
| `DG` | direção/bearing do veículo |
| `SV` | sentido operacional: normalmente 1 ida e 2 volta; 0/3/ausente também aparecem |
| `DT` | distância percorrida informada pela fonte |

## Relações

```text
route_source_codes.NL -> transit_routes.route_id -> transit_trips
                                                   -> trip_stops -> transit_stops
vehicles -> vehicle_positions -> linha e, quando inferível, viagem
arrival_predictions -> veículo + linha + viagem opcional + ponto
```

A tabela oficial de conversão contém variantes como `5201-03`, enquanto o GTFS pode consolidar a
linha como `5201`. O importador tenta igualdade exata e depois remove somente o sufixo operacional
após `-` e zeros à esquerda. Correspondências ambíguas permanecem nulas. O consumidor nunca copia
um `trip_id` inexistente na fonte. O estágio de associação cruza linha, sentido, calendário, janela
de horário e proximidade ao shape, persistindo método e confiança e rejeitando casos ambíguos.

## Banco e migrações

PostgreSQL 17 com PostGIS 3.5 é obrigatório. Pontos e posições possuem coluna `geography(Point,4326)`
gerada a partir de latitude/longitude e índice GiST. O histórico também possui BRIN em `observed_at`
e B-tree composto por veículo/linha/viagem e instante. No Mac Apple Silicon, a imagem oficial roda
sob `linux/amd64`; a migration e os testes foram validados nessa configuração.

```bash
docker compose up -d db
cd backend
.venv/bin/alembic upgrade head
.venv/bin/python -m app.workers.gtfs_importer --include-stop-times
.venv/bin/python -m app.workers.realtime_pipeline --once
```

Use `--include-stop-times` para carregar as paradas programadas e calcular sua progressão no shape.
Sem essa opção, a associação de viagens funciona, mas previsão por distância de trajeto e detecção
de chegada ficam incompletas.

Para coleta contínua:

```bash
docker compose up -d db collector
```

## ETA inicial e avaliação

`baseline-schedule-v1` usa o horário GTFS programado. `baseline-haversine-v1` é mantido para
comparação. O pipeline contínuo usa `baseline-shape-speed-v1`: estima a distância restante sobre o
shape, divide pela velocidade instantânea válida e usa a média recente da linha ou 18 km/h como
fallback. A incerteza cresce com o horizonte da previsão.

Chegadas são detectadas por proximidade ao ponto, baixa velocidade e aproximação em relação à
posição anterior. O evento rotula `actual_arrival` nas previsões correspondentes. Esse método é
auditável, mas ainda pode confundir paradas próximas e depende da qualidade do GPS.

O avaliador ordena por `generated_at`, usa o bloco final como validação temporal e calcula MAE,
mediana, P90 e P95, além de segmentos por linha, hora local e distância até o ponto:

```bash
cd backend
.venv/bin/python -m app.workers.eta_evaluator
```

O resultado é `N/A` até existirem previsões com `actual_arrival` rotulado. Não é correto publicar um
erro médio antes de coletar chegadas reais suficientes e separar avaliação temporal de treino.

## Limitações e operação

- O endpoint é um arquivo atualizado, não um stream e nem GTFS-Realtime protobuf.
- Podem existir duplicatas no mesmo snapshot; elas são removidas antes da persistência.
- Nem todos os códigos operacionais possuem associação inequívoca com o GTFS atual.
- O feed pode apresentar sentidos 0/3 ou ausentes além de 1/2.
- A retenção padrão é 90 dias, removida em lotes de 50 mil pelo worker `retention`.
- BRIN reduz o custo de varreduras temporais; particionamento mensal deve ser ativado antes de a
  tabela ultrapassar dezenas de milhões de posições ou quando a remoção em lotes afetar o autovacuum.
- Cada coleta persiste tentativas, status HTTP, contagens, lag, duração, erros e desaparecimentos.
- Cada ciclo emite log JSON com contagens de coleta, matching, chegadas e previsões.
- Recomenda-se alertar quando o feed estiver atrasado por mais de 90 segundos.
- O uso deve manter atribuição à PBH/TRANSFÁCIL conforme a licença publicada.
