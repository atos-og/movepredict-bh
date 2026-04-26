# Data Notes — MovePredict BH

Este arquivo registra descobertas sobre os dados públicos usados no projeto.

## Fontes oficiais

### GTFS PBH

Link:

Descrição:

Arquivos esperados:

- routes.txt
- stops.txt
- trips.txt
- trips.txt
- stop_times.txt
- shapes.txt

### Dados em tempo real

Link:

Descrição:

Frequência de atualização:

## Perguntas em aberto

- Como relacionar veículo com linha?
- Como identificar o sentido da viagem?
- Como saber se o ônibus já passou por um ponto?

## Scripts de exploração

### inspect_routes.py

Script criado para ler o arquivo `routes.txt` do GTFS e listar as linhas encontradas.

Caminho esperado do arquivo:

```txt
data-exploration/data/raw/routes.txt




