# Criterios minimos para lancamento

## Bloqueadores

- CI da `main` integralmente verde.
- Zero segredo versionado e CORS restrito ao frontend publicado.
- `/health` e `/ready` monitorados; backup e restauracao do banco testados.
- Pelo menos 24 horas consecutivas de coleta em staging, sem lacuna nao explicada acima de 5 min.
- Pelo menos 95% dos ciclos de coleta concluidos com sucesso.
- Mediana do atraso da fonte abaixo de 60 s e P95 abaixo de 120 s.
- Associacoes de viagem abaixo da confianca minima nunca exibidas como confirmadas.
- Nenhum erro critico nos fluxos de linha, ponto, mapa, localizacao e modo offline.

## Qualidade do ETA

Os limiares finais dependem da primeira amostra real. Como criterio inicial de demonstracao:

- minimo de 100 chegadas rotuladas, cinco linhas e dois periodos do dia;
- MAE global de ate 180 s;
- mediana de ate 120 s;
- P90 de ate 360 s;
- resultados publicados por linha, horario e horizonte, incluindo tamanho da amostra;
- previsoes fora desses requisitos devem aparecer como experimentais ou indisponiveis.

Os numeros devem ser revistos em conjunto depois do teste de campo. Nao se deve otimizar o modelo
contra o mesmo bloco temporal usado para aceite.

## Experiencia e operacao

- WCAG 2.2 AA nos fluxos principais e navegacao por teclado sem bloqueios.
- Sem overflow horizontal entre 320 px e 1440 px.
- P75 LCP abaixo de 2,5 s e CLS abaixo de 0,1 no ambiente publicado.
- Procedimentos de rollback, retencao, incidente e atribuicao da PBH documentados.
- Aprovacao explicita de Atos e Vinicius registrada antes da demonstracao publica com backend real.
