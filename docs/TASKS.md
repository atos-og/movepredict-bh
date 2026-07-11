# Tasks - MovePredict BH

## Próximas - Atos

- [ ] Revisar o contrato com Vinicius usando payloads reais.
- [ ] Adicionar adapters HTTP/SQL quando as fontes estiverem disponíveis.
- [x] Criar testes de integração PostGIS.
- [ ] Definir provedor e ambiente de homologação.
- [ ] Adicionar métricas exportáveis e readiness check (logs estruturados já entregues).

## Próximas - Vinicius

- [x] Entregar contrato da fonte de posições em tempo real.
- [x] Definir schema e migrações PostgreSQL/PostGIS.
- [x] Persistir posições históricas com consumidor idempotente.
- [x] Entregar ETA baseline versionado e cálculo de MAE.
- [x] Implementar rotulagem automática de chegadas reais.
- [ ] Publicar métricas de ETA quando houver amostra temporal suficiente.
- [x] Implementar associação confiável de posição a `trip_id`.

## Concluídas - Aplicação

- [x] Revisar sem merge a branch de detalhe de ponto.
- [x] Separar routers, services e schemas.
- [x] Implementar linhas, pontos, trajetos, filtros e paginação.
- [x] Remover `/pontos` mockado.
- [x] Padronizar erros e configurar CORS/ambiente.
- [x] Criar testes FastAPI TestClient.
- [x] Criar frontend Next.js, TypeScript e Leaflet.
- [x] Definir contratos futuros de veículos e previsões.
- [x] Criar GitHub Actions.
- [x] Preparar Dockerfiles e Compose sem publicar.
- [x] Atualizar documentação principal.
