# Tarefas MovePredict BH

## Atos

- [x] Integrar PR #34 na `main`.
- [x] Expor endpoints de veiculos e previsoes.
- [x] Integrar veiculos e chegadas ao mapa com polling controlado.
- [x] Tratar loading, vazio, atraso e indisponibilidade.
- [x] Conectar geocodificacao real configuravel.
- [x] Adicionar readiness, metricas, logs e seguranca basica.
- [x] Preparar smoke test manual de staging.
- [x] Fechar contrato JSON com estados `live`, `empty` e `stale`.
- [x] Automatizar coleta de evidencias de smoke/soak test.
- [x] Preparar criterios de lancamento, teste de campo e demonstracao.
- [ ] Escolher/provisionar motor de roteamento publico e credencial.
- [ ] Validar staging depois da autorizacao de URLs e secrets.
- [ ] Concluir testes de carga e auditoria com ambiente completo.

## Vinicius

- [x] Entregar fonte e contrato de posicoes.
- [x] Criar schema e migracoes PostgreSQL/PostGIS.
- [x] Persistir posicoes historicas.
- [x] Associar posicoes a viagens GTFS.
- [x] Gerar e rotular previsoes de chegada.
- [x] Criar avaliador temporal.
- [ ] Coletar amostra suficiente e publicar metricas de ETA.

## Trabalho conjunto

- [x] Fechar o contrato JSON de veiculos e previsoes.
- [x] Definir criterios minimos iniciais para lancamento.
- [x] Revisar no repositorio privacidade, termos da fonte e retencao.
- [x] Preparar protocolos de staging, campo e demonstracao.
- [ ] Validar endpoints publicados com payloads reais e guardar a evidencia.
- [ ] Executar o sistema por periodo prolongado em staging.
- [ ] Fazer teste de campo com linhas reais de Belo Horizonte.
- [ ] Comparar previsoes com chegadas reais e aprovar os limiares finais.
- [ ] Corrigir associacoes ou apresentacoes identificadas pela amostra real.
- [ ] Aprovar demonstracao publica e versao de producao.
