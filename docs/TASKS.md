# Tarefas MovePredict BH

## Atos

- [x] Integrar PR #34 na `main`.
- [x] Expor endpoints de veiculos e previsoes.
- [x] Integrar veiculos e chegadas ao mapa com polling controlado.
- [x] Tratar loading, vazio, atraso e indisponibilidade.
- [x] Conectar geocodificacao real configuravel.
- [x] Adicionar readiness, metricas, logs e seguranca basica.
- [x] Preparar smoke test manual de staging.
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

- [ ] Executar o sistema por periodo prolongado em staging.
- [ ] Fazer teste de campo com linhas reais de Belo Horizonte.
- [ ] Definir limiares minimos de qualidade do ETA.
- [ ] Revisar privacidade, termos das fontes e politica de retencao.
- [ ] Aprovar demonstracao publica e versao de producao.
