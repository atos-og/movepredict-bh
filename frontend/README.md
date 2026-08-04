# Frontend

Aplicação Next.js do MovePredict BH, construída com TypeScript, React Leaflet e componentes Lucide.

## Fundação visual

A interface preserva a identidade azul-escura e verde do projeto. Os tokens semânticos ficam em
`app/globals.css`, e as primitivas reutilizáveis ficam em `components/ui`.

Princípios adotados:

- mapa como superfície principal;
- ações primárias fáceis de identificar;
- informação revelada progressivamente;
- controles compactos e áreas de toque confortáveis;
- estados de foco visíveis e suporte a movimento reduzido;
- nenhuma indicação programada apresentada como dado em tempo real.

As referências de Citymapper, Apple Maps, Google Maps e Moovit orientam hierarquia e interação,
sem reprodução direta de suas interfaces.

## Experiência atual

- mapa como superfície principal em desktop e mobile;
- busca unificada por linhas e pontos da base GTFS;
- exploração paginada de todas as linhas e pontos;
- solicitação automática de geolocalização com estados de permissão, erro e indisponibilidade;
- pontos próximos calculados a partir do filtro geográfico da API;
- detalhes de linha com sentido, trajeto e sequência de pontos;
- detalhes de ponto sem apresentar previsões ou rotas inexistentes;
- buscas recentes armazenadas somente no navegador.

A distância entre o usuário e um ponto é calculada em linha reta e aparece explicitamente com
essa descrição. Ela não representa caminho ou tempo de caminhada.

Consulte [INTEGRATIONS.md](INTEGRATIONS.md) para as fronteiras de geocodificação, roteamento,
linhas por ponto, veículos e previsões.

## Execução

```powershell
Copy-Item .env.example .env.local
pnpm install
pnpm dev
```

## Variáveis

- `NEXT_PUBLIC_API_URL`: prefixo acessado pelo navegador; use `/api` no app completo.
- `API_PROXY_TARGET`: URL do FastAPI acessada pelo servidor Next.js (`http://localhost:8000`
  no desenvolvimento local ou `http://api:8000` no Docker Compose).
- `NEXT_PUBLIC_REALTIME_API_URL`: reservado para o adaptador futuro de veículos e previsões.

## Contrato futuro

`types/realtime.ts` define `VehiclePosition`, `ArrivalPrediction` e `RealtimeProvider`. A implementação do provedor poderá ser conectada sem alterar os componentes de mapa ou os contratos da API estática.

## Validação

```powershell
pnpm test
pnpm lint
pnpm typecheck
pnpm build
```
