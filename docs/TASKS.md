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
- [x] Provisionar OpenTripPlanner local sem credencial de API.
- [ ] Validar staging depois da autorizacao de URLs e secrets.
- [ ] Concluir testes de carga e auditoria com ambiente completo.

## Vinicius

- [x] Entregar fonte e contrato de posicoes.
- [x] Criar schema e migracoes PostgreSQL/PostGIS.
- [x] Persistir posicoes historicas.
- [x] Associar posicoes a viagens GTFS.
- [x] Gerar e rotular previsoes de chegada.
- [x] Criar avaliador temporal.
- [x] Persistir métricas operacionais e disponibilizar relatório de qualidade/banco.
- [x] Priorizar matching online por veículo e impedir starvation da detecção de chegada.
- [ ] Coletar amostra suficiente e publicar métricas de ETA por linha, horário e horizonte.

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
- [ ] Regenerar o relatório operacional após 24 horas com o pipeline corrigido.
- [ ] Aprovar demonstracao publica e versao de producao.

## Nucleo porta a porta

- [x] Implementar busca de destino real sem autocomplete abusivo.
- [x] Preparar roteamento local com OpenTripPlanner.
- [x] Exibir melhor rota, alternativas e ausencia de previsao com clareza.
- [x] Implementar acompanhamento, recálculo e alerta de desembarque.
- [x] Implementar rota offline e pacote completo de icones PWA.
- [x] Preparar integracao de alertas operacionais GTFS-Realtime.
- [ ] Validar no iPhone com trajeto real em Belo Horizonte.
- [ ] Executar soak test com OTP, API, banco, collector e frontend juntos.
