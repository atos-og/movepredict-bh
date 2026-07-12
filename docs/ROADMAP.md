# Roadmap MovePredict BH

## Fase 1 - Dados estaticos

- [x] Identificar e documentar GTFS da PBH.
- [x] Inspecionar linhas, pontos, viagens e shapes.
- [x] Expor consultas estaticas pela API.

## Fase 2 - Aplicacao base

- [x] Modularizar FastAPI e padronizar contratos.
- [x] Criar frontend Next.js mobile-first com Leaflet.
- [x] Adicionar testes, CI, Docker e GitHub Pages.
- [x] Disponibilizar PWA instalavel.

## Fase 3 - Dados em tempo real

- [x] Coletar posicoes oficiais periodicamente.
- [x] Criar PostgreSQL/PostGIS e migracoes.
- [x] Persistir historico idempotente.
- [x] Associar posicao, linha e viagem GTFS.
- [x] Gerar ETA baseline e detectar chegadas.
- [x] Criar avaliador de MAE, mediana, P90 e P95.
- [ ] Publicar resultados com amostra temporal suficiente.

## Fase 4 - Integracao

- [x] Implementar providers SQL.
- [x] Expor veiculos e chegadas pela API.
- [x] Atualizar mapa e previsoes a cada 20 segundos.
- [x] Cobrir contratos com testes unitarios e PostGIS.
- [x] Conectar geocodificacao configuravel.
- [ ] Integrar motor real de roteamento de transporte publico.
- [ ] Validar coleta prolongada em staging.

## Fase 5 - Entrega

- [x] Preparar readiness, metricas, logs e smoke tests.
- [ ] Escolher provedores e orcamento.
- [ ] Configurar secrets apenas no ambiente autorizado.
- [ ] Executar testes de carga e auditoria final.
- [ ] Publicar staging e producao mediante autorizacao.
- [ ] Finalizar resultados de ETA e case study.
