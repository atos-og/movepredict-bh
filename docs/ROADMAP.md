# Roadmap - MovePredict BH

## Fase 1 - Dados estáticos

- [x] Identificar e documentar a fonte GTFS da PBH.
- [x] Criar scripts de inspeção e download.
- [x] Consultar linhas, pontos, viagens, sequências e shapes.

## Fase 2 - Aplicação base

- [x] Modularizar a API FastAPI.
- [x] Implementar detalhes, filtros e paginação.
- [x] Padronizar respostas, erros, CORS e configuração.
- [x] Cobrir a API com testes automatizados.
- [x] Construir o frontend Next.js com Leaflet.
- [x] Adicionar busca por linha e ponto, loading e erros.
- [x] Configurar CI e contêineres.

## Fase 3 - Dados em tempo real (Vinicius)

- [ ] Implementar coleta confiável das posições.
- [ ] Definir PostgreSQL/PostGIS e migrações.
- [ ] Persistir histórico de posições.
- [ ] Implementar previsão inicial e métricas.

## Fase 4 - Integração

- [ ] Implementar adaptadores dos contratos de veículos e previsões.
- [ ] Expor endpoints de tempo real e chegada.
- [ ] Atualizar o mapa de forma periódica ou por stream.
- [ ] Adicionar testes integrados com banco.

## Fase 5 - Lançamento

- [ ] Escolher provedores e orçamento.
- [ ] Configurar secrets e observabilidade.
- [ ] Executar teste de carga e revisão de segurança.
- [ ] Publicar ambientes de homologação e produção com autorização.
- [ ] Finalizar case study e demonstração.
