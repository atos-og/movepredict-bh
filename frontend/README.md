# Frontend

Aplicação Next.js do MovePredict BH, construída com TypeScript, React Leaflet e componentes Lucide.

## Execução

```powershell
Copy-Item .env.example .env.local
pnpm install
pnpm dev
```

## Variáveis

- `NEXT_PUBLIC_API_URL`: URL pública da API FastAPI.
- `NEXT_PUBLIC_REALTIME_API_URL`: reservado para o adaptador futuro de veículos e previsões.

## Contrato futuro

`types/realtime.ts` define `VehiclePosition`, `ArrivalPrediction` e `RealtimeProvider`. A implementação do provedor poderá ser conectada sem alterar os componentes de mapa ou os contratos da API estática.

## Validação

```powershell
pnpm lint
pnpm typecheck
pnpm build
```
