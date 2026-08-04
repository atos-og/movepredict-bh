# MovePredict BH

O MovePredict BH é uma aplicação para consultar linhas, pontos e trajetos do transporte coletivo de Belo Horizonte. A base atual usa GTFS estático da PBH e já deixa contratos definidos para posições de veículos e previsões de chegada.

## Estado atual

- API FastAPI modular com linhas, pontos, trajetos e viagens.
- Filtros, paginação, CORS, respostas tipadas e erros padronizados.
- Frontend Next.js mobile-first com mapa Leaflet, busca unificada, geolocalização contextual, linhas, pontos e favoritos locais.
- Testes automatizados do backend e validações de frontend.
- Pipeline de CI e imagens Docker prontas para avaliação.
- PostgreSQL, migrações, importação GTFS e coleta oficial de posições a cada 20 segundos.
- Associação posição/viagem, ETA por shape e rotulagem de chegadas no pipeline periódico.
- Avaliação temporal de ETA com MAE, mediana, P90/P95 e segmentações.
- Sem publicação ou credenciais externas provisionadas.

## Responsabilidades

Atos mantém backend, frontend, integração, testes, CI, documentação e preparação de deploy.

Vinicius mantém exploração e obtenção dos dados em tempo real, PostgreSQL, histórico de posições e previsão de chegada. A implementação e suas limitações estão em `docs/DATA_PIPELINE.md`.

## Estrutura

```text
backend/          API FastAPI, schemas, services e testes
frontend/         Aplicação Next.js, TypeScript e Leaflet
data-exploration/ Scripts e dados locais da frente de dados
docs/             API, arquitetura, decisões, roadmap e tarefas
.github/          GitHub Actions
compose.yaml      Execução local em contêineres
```

## Desenvolvimento local

### API

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

O GTFS deve estar extraído em `data-exploration/data/raw`. A documentação interativa fica em `http://localhost:8000/docs`.

Para validar o ambiente e inspecionar rapidamente os arquivos GTFS:

```powershell
python data-exploration/scripts/check_environment.py
python data-exploration/scripts/inspect_routes.py
python data-exploration/scripts/inspect_stops.py
```

### Frontend

Requer Node.js 22 e pnpm 11.

```powershell
cd frontend
Copy-Item .env.example .env.local
pnpm install
pnpm dev
```

A aplicação fica em `http://localhost:3000` e espera a API em `http://localhost:8000`.

Rotas principais do frontend:

- `/`: experiência mobile orientada ao destino;
- `/linhas` e `/linha/{routeId}`: linhas e itinerários GTFS reais;
- `/pontos`: pontos próximos com consulta geográfica limitada;
- `/rota` e `/viagem`: contratos para planejamento e acompanhamento;
- `/explorar`: explorador técnico anterior, preservado integralmente.

## Validação

```powershell
cd backend
pytest
ruff check app tests
ruff format --check app tests

cd ../frontend
pnpm test
pnpm test:visual
pnpm lint
pnpm typecheck
pnpm build
```

## Contêineres

Com os dados GTFS locais disponíveis:

```powershell
docker compose up --build
```

Nenhuma configuração deste repositório publica serviços automaticamente. Consulte [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) antes de escolher um provedor.

## Documentação

- [API](docs/API.md)
- [Arquitetura](docs/ARCHITECTURE.md)
- [Deploy](docs/DEPLOYMENT.md)
- [Roadmap](docs/ROADMAP.md)
- [Tarefas](docs/TASKS.md)
- [Decisões técnicas](docs/DECISIONS.md)
- [Pipeline de dados e ETA](docs/DATA_PIPELINE.md)
- [Contrato de entrega e mapeamento de IDs](docs/DELIVERY_CONTRACT.md)
- [Validação operacional e soak test](docs/STAGING_VALIDATION.md)
- [Consultas SQL operacionais](docs/sql/operational_queries.sql)
- [Relatório real de qualidade, matching e volume](docs/reports/realtime-quality.md)
- [Validacao de staging](docs/STAGING_VALIDATION.md)
- [Criterios de lancamento](docs/LAUNCH_CRITERIA.md)
- [Teste de campo](docs/FIELD_TEST.md)
- [Privacidade e dados](docs/PRIVACY_AND_DATA.md)
- [Roteiro de demonstracao](docs/DEMO.md)
- [Resultado da verificacao](docs/VERIFICATION.md)

## Integracao em tempo real

Com PostgreSQL, importacao GTFS e coletor ativos, a API disponibiliza:

- `GET /realtime/vehicles`: posicoes recentes, opcionalmente filtradas por linha;
- `GET /realtime/stops/{stop_id}/arrivals`: proximas chegadas previstas;
- `GET /ready`: disponibilidade do banco;
- `GET /metrics`: contadores HTTP no formato Prometheus.

O frontend atualiza veiculos e previsoes a cada 20 segundos e diferencia dados vazios,
desatualizados e indisponiveis. Nenhuma rota, previsao ou alerta e inventado quando uma fonte
nao esta disponivel.

## Assistente porta a porta

A integracao atual centraliza geocodificacao e roteamento no backend. O frontend oferece busca
explicita de destinos em BH, tres preferencias de rota, alternativas, acompanhamento, recálculo
fora da rota, salvamento offline e aviso de desembarque. ETA real e usado apenas quando o
endpoint informa estado `live`; caso contrario, a interface identifica o horario programado.

Para preparar o OpenTripPlanner local pela primeira vez:

```powershell
python scripts/prepare_otp.py
docker compose --profile routing-tools run --rm otp-build
docker compose --profile routing up -d otp
docker compose up --build
```

O processo usa OSM e GTFS oficiais, nao exige credencial e nao gera custo de API. O grafo local
`routing/otp/graph.obj` e gerado em cada ambiente e nao e versionado. Consulte
[`docs/MOBILITY_ASSISTANT.md`](docs/MOBILITY_ASSISTANT.md) para contratos e limites.
