# Relatório operacional de dados em tempo real

Gerado em `2026-07-15T00:55:58.094674+00:00` para a janela de 7 dias.

## Coleta

- ciclos: 3232 (3223 sucessos, 9 falhas);
- disponibilidade observada: 99.72%;
- gaps operacionais: 23;
- indisponibilidade estimada: 224988 s;
- lag médio/máximo da fonte: 0.01 / 10.91 s;
- erros de parse: 0; duplicatas: 80.19%.

## Qualidade e associação

- posições: 10257241; veículos: 2669;
- linha GTFS associada: 97.87%;
- viagem associada: 0.02%;
- veículos com última posição associada: 90/2669 (3.37%);
- posições ainda não avaliadas: 9507728;
- atrasadas >90 s: 323492; fora do envelope de BH: 4104.

## ETA

- previsões: 2673; chegadas reais rotuladas: 24;
- MAE, mediana, P90 e P95 permanecem não publicáveis enquanto não houver amostra rotulada.

## Pipeline

- ciclos: 4; falhas: 0;
- matching: 425/1000; chegadas: 71;
- previsões criadas/rotuladas: 1102/3.

## Banco

| relação | linhas estimadas | total | tabela | índices |
| --- | ---: | ---: | ---: | ---: |
| vehicle_positions | 10313378 | 5.1 GiB | 1.6 GiB | 3.5 GiB |
| trip_stops | 6672551 | 762.6 MiB | 384.1 MiB | 378.3 MiB |
| arrival_predictions | 5480 | 1.8 MiB | 792.0 KiB | 992.0 KiB |
| collection_runs | 3243 | 816.0 KiB | 432.0 KiB | 344.0 KiB |
| arrival_events | 283 | 200.0 KiB | 32.0 KiB | 144.0 KiB |
| pipeline_runs | 14 | 64.0 KiB | 8.0 KiB | 48.0 KiB |

## Limitações

- Taxas descrevem somente a janela coletada; períodos sem processo ativo aparecem como gaps.
- MAE e percentis só devem ser publicados quando labeled_predictions for suficiente.
- Validação de campo exige observação humana e não é inferida automaticamente.
