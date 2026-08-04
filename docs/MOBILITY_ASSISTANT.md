# Assistente de mobilidade

## Fluxo principal

1. O usuario autoriza a localizacao.
2. A busca explicita converte o destino em coordenadas reais dentro de Belo Horizonte.
3. O OpenTripPlanner combina caminhada, GTFS e malha viaria e retorna alternativas.
4. O frontend enriquece o primeiro embarque com ETA real quando o banco possui previsao `live`.
5. Ao iniciar, a rota e salva no aparelho e o navegador acompanha a posicao em primeiro plano.
6. Tres leituras consecutivas a mais de 250 metros da geometria disparam recálculo, com intervalo
   minimo de dois minutos.
7. A 600 metros do desembarque, o app mostra alerta, vibra e envia notificacao se houver permissao.

## Estados honestos

- Sem localizacao: solicita permissao e explica como libera-la.
- Sem OTP: preserva o destino e informa indisponibilidade do planejador.
- Sem rota: declara que nenhuma combinacao foi encontrada naquele horario.
- Sem ETA: mostra horario programado e informa que a posicao do onibus nao esta disponivel.
- Sem veiculo: mantem o trajeto e informa que nao existe veiculo visivel.
- Sem internet: usa instrucoes e geometria persistidas; o mapa-base pode ficar indisponivel.
- Sem alertas configurados: o endpoint informa `unavailable`, sem inventar ocorrencias.

## Identidade PWA

O simbolo original e um M formado por uma linha de trajeto, com um ponto de localizacao laranja.
O SVG mestre gera favicon, Apple Touch Icon, PWA 192 e 512, variante maskable e monocromatica.
O desenho nao possui texto nem ilustracao de onibus e continua legivel em tamanho pequeno.

## Limites de validacao

O software pode ser testado automaticamente fora de Belo Horizonte. A precisao do ETA, o
matching em operacao, o momento do alerta de desembarque e o recálculo em ruas reais exigem o
protocolo de `docs/FIELD_TEST.md`. MAE, mediana, P90 e P95 so devem ser publicados quando o
avaliador atingir a amostra minima definida pelo projeto.
