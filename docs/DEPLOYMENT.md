# Preparacao de deploy

Nenhum recurso e publicado automaticamente e nenhuma credencial fica no repositorio.

## Componentes

- Frontend Next.js/PWA: GitHub Pages para portfolio ou container para staging.
- API FastAPI: `backend/Dockerfile`.
- PostgreSQL 17 com PostGIS 3.5.
- Worker `python -m app.workers.realtime_pipeline`.
- Retencao `python -m app.workers.retention`.
- Importacao inicial `python -m app.workers.gtfs_importer --include-stop-times`.

## Variaveis obrigatorias

- `MOVEPREDICT_DATABASE_URL`
- `MOVEPREDICT_GTFS_DATA_DIR`
- `MOVEPREDICT_CORS_ORIGINS`
- `MOVEPREDICT_REALTIME_POSITIONS_URL`
- `NEXT_PUBLIC_API_URL`

Secrets devem existir somente no painel do provedor/GitHub Environment. O Nominatim publico
nao e usado para autocomplete: a API envia apenas buscas confirmadas, com cache, User-Agent
identificavel e limite de uma requisicao por segundo.

## Requisitos de staging

1. Banco persistente com extensao PostGIS.
2. Volume ou artefato GTFS acessivel a API e ao importador.
3. API e worker em processos separados.
4. HTTPS, CORS restrito e backups do banco.
5. Alertas para `/ready`, atraso da fonte e falha do worker.
6. Politica de retencao executada periodicamente.

## Validacao

O workflow `Staging smoke test` e manual e recebe apenas URLs publicas. Ele valida frontend,
liveness, readiness, GTFS e contrato realtime. A publicacao continua bloqueada ate autorizacao
explicita e provisionamento dos recursos externos.

## Configuracao do assistente

- `MOVEPREDICT_GEOCODING_URL`: endpoint Nominatim ou provedor compativel.
- `MOVEPREDICT_GEOCODING_USER_AGENT`: identificacao publica do projeto.
- `MOVEPREDICT_JOURNEY_PLANNER_URL`: GraphQL do OpenTripPlanner.
- `MOVEPREDICT_GTFS_RT_ALERTS_URL`: fonte opcional de alertas; nao versionar se contiver chave.

O frontend recebe apenas `NEXT_PUBLIC_API_URL`. Geocodificacao, OTP e alertas ficam atras da API.
O perfil Docker `routing` executa o OTP sem credencial e sem API paga. Gere o `graph.obj` com
`scripts/prepare_otp.py` e o perfil `routing-tools` antes da primeira inicializacao.
