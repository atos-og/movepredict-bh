# Validacao de staging e soak test

## Objetivo

Gerar evidencia reproduzivel de que frontend, API, GTFS, PostgreSQL e pipeline realtime operam
juntos. O validador nunca considera uma resposta vazia como dado ao vivo e nao publica metricas de
ETA sem chegadas reais rotuladas.

## Pre-requisitos

- frontend e API publicados com HTTPS;
- `/ready` respondendo `ready`;
- GTFS importado com `--include-stop-times`;
- collector em execucao separado da API;
- CORS restrito ao dominio do frontend;
- nenhum segredo presente nas URLs.

## Smoke test

```bash
python backend/scripts/validate_staging.py \
  --api-url https://api.staging.example \
  --web-url https://staging.example \
  --output staging-validation.json
```

## Soak test

Para uma primeira janela controlada de duas horas:

```bash
python backend/scripts/validate_staging.py \
  --api-url https://api.staging.example \
  --web-url https://staging.example \
  --duration-minutes 120 \
  --interval-seconds 20 \
  --require-live-data \
  --output staging-validation-2h.json
```

O workflow manual `Staging smoke test` executa a mesma validacao por ate 30 minutos e anexa o JSON
como artefato. Janelas maiores devem rodar em uma maquina de operacao ou runner proprio.

## Evidencias obrigatorias

- JSON gerado pelo validador;
- logs do collector sem credenciais;
- total de ciclos, falhas, duplicatas, atraso e associacoes rejeitadas;
- saida do `eta_evaluator` somente depois de amostra suficiente;
- horario, versao/commit e configuracao nao secreta do teste.

Sem URL de staging provisionada, esta etapa permanece preparada, mas nao executada.
