# Protocolo de teste de campo

## Escopo minimo

Testar pelo menos duas linhas em sentidos diferentes, dois aparelhos celulares e tres pontos de BH.
Uma pessoa observa o app; outra registra apenas eventos operacionais, sem nomes, telefones ou
localizacao historica de usuarios.

## Antes de sair

- confirmar commit e ambiente em teste;
- executar smoke test de staging;
- confirmar permissao de localizacao concedida e negada em aparelhos diferentes;
- sincronizar relogios dos aparelhos;
- escolher pontos seguros e horarios diurno e de pico;
- preparar a planilha sem dados pessoais.

## Registro por observacao

| Campo | Descricao |
| --- | --- |
| instante | UTC e horario local |
| linha/sentido | codigo publico e direcao observada |
| ponto | `stop_id` GTFS |
| veiculo | identificador publico quando exibido |
| ETA exibido | minutos e incerteza |
| chegada real | instante em que o onibus atende o ponto |
| erro | diferenca absoluta entre ETA e chegada |
| apresentacao | mapa, linha, ponto e estado exibidos corretamente |
| observacao | atraso de feed, GPS ruim ou associacao duvidosa |

## Cenarios

1. Localizacao concedida, negada e indisponivel.
2. Linha com veiculo ao vivo e linha sem veiculo.
3. Ponto com previsao, sem previsao e previsao atrasada.
4. Troca entre Wi-Fi e rede movel e perda temporaria de conexao.
5. App instalado como PWA e aberto pelo navegador.
6. Ida e volta da mesma linha, verificando shape e ordem das paradas.

## Aceite

O teste so e aprovado quando nao houver associacao comprovadamente incorreta exibida como certa,
os estados vazios/atrasados estiverem claros e os criterios de `LAUNCH_CRITERIA.md` forem atendidos.
