# Roteiro de demonstracao

## Preparacao

1. Registrar o commit demonstrado e executar CI e smoke test.
2. Abrir frontend, `/docs`, painel de logs e `staging-validation.json`.
3. Confirmar que nenhuma aba ou terminal mostra credenciais.
4. Ter o GitHub Pages como fallback visual; ele nao substitui o staging realtime.

## Demonstracao de 8 minutos

1. **Problema (45 s):** encontrar transporte em BH sem conhecer a estrutura do GTFS.
2. **Home (60 s):** destino primeiro, geolocalizacao opcional e mapa contextual.
3. **Linhas e pontos (90 s):** dados oficiais, itinerario, sentidos e paradas.
4. **Tempo real (90 s):** veiculos, atualizacao de 20 s e estados `live`, `empty` e `stale`.
5. **ETA (90 s):** previsao versionada, incerteza, chegada real e limites atuais.
6. **Engenharia (90 s):** FastAPI, Next.js, PostGIS, worker, testes e CI.
7. **Proximos passos (45 s):** amostra prolongada, teste de campo e motor de roteamento.

## Mensagem honesta

O produto ja demonstra consulta e monitoramento integrados. O ETA e experimental ate atingir os
criterios publicados. Planejamento porta a porta depende de um motor externo configurado e nunca e
simulado silenciosamente.

## Estrutura sugerida da apresentacao

1. MovePredict BH e problema.
2. Experiencia orientada ao destino.
3. Arquitetura e fonte oficial.
4. Pipeline realtime e PostGIS.
5. ETA, avaliacao e limitacoes.
6. Qualidade: testes, CI, seguranca e observabilidade.
7. Demonstracao.
8. Resultados, pendencias e roadmap.
