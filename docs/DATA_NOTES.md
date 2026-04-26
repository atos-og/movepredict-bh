# Data Notes — MovePredict BH

Este arquivo registra descobertas sobre os dados públicos usados no projeto.

## Fontes oficiais

### GTFS estático

Link: https://dados.pbh.gov.br/dataset/gtfs

Descrição:
Conjunto de arquivos no padrão GTFS com a especificação dos serviços do sistema de transporte convencional, incluindo MOVE e suplementar. Segundo o Portal de Dados Abertos da PBH, o conjunto é atualizado semanalmente, e a URL de download é fixa, com arquivo disponível atualizado diariamente.

Arquivos esperados:

- routes.txt
- stops.txt
- trips.txt
- stop_times.txt
- shapes.txt

### GTFS RT

Link: https://dados.pbh.gov.br/dataset/gtfs-rt

Descrição:
Conjunto de arquivos no padrão GTFS RT com atualizações em tempo real para transporte público. Inclui informações como alertas de serviço, horários de partida e chegada em tempo real e posição de veículos.

Recursos esperados:

- Atualizações de viagem
- Posição de veículos
- Alertas de serviço

### Tempo Real Ônibus — Coordenada atualizada

Link: https://dados.pbh.gov.br/dataset/?organization=superintendencia-de-mobilidade

Descrição:
Arquivos para download com as últimas coordenadas dos ônibus em operação nas linhas do sistema de transporte convencional municipal, incluindo MOVE. O portal indica atualização a cada 20 segundos.

Formatos encontrados:

- LOG
- JSON
- CSV

### Pontos de ônibus

Link: https://dados.pbh.gov.br/dataset/?organization=superintendencia-de-mobilidade

Descrição:
Base com a localização dos pontos destinados ao embarque e desembarque de passageiros do transporte coletivo por ônibus no município de Belo Horizonte.

## O que precisamos descobrir

- Qual URL direta usar para baixar o GTFS.
- Qual URL direta usar para obter posições dos veículos.
- Como relacionar veículo com linha.
- Como identificar o sentido da viagem.
- Como saber qual ponto está mais próximo de um ônibus.
- Como saber se o ônibus já passou ou ainda vai passar por um ponto.

## Próximos passos

- Criar script para baixar os dados GTFS.
- Criar script para inspecionar linhas.
- Criar script para inspecionar pontos.
- Criar script para testar dados em tempo real.