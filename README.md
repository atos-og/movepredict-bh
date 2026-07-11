# MovePredict BH

O MovePredict BH é uma aplicação para consultar linhas, pontos e trajetos do transporte coletivo de Belo Horizonte. A base atual usa GTFS estático da PBH e já deixa contratos definidos para posições de veículos e previsões de chegada.

## Estado atual

- API FastAPI modular com linhas, pontos, trajetos e viagens.
- Filtros, paginação, CORS, respostas tipadas e erros padronizados.
- Frontend Next.js mobile-first com mapa Leaflet, busca unificada, geolocalização contextual, linhas, pontos e favoritos locais.
- Testes automatizados do backend e validações de frontend.
- Pipeline de CI e imagens Docker prontas para avaliação.
- Sem publicação, credenciais ou infraestrutura externa provisionada.

## Responsabilidades

Atos mantém backend, frontend, integração, testes, CI, documentação e preparação de deploy.

Vinicius mantém exploração e obtenção dos dados em tempo real, PostgreSQL/PostGIS, histórico de posições e previsão de chegada. Essas partes não são implementadas aqui; a integração futura está definida pelos contratos `VehiclePositionProvider`, `ArrivalPredictionProvider`, `VehiclePosition` e `ArrivalPrediction`.

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
