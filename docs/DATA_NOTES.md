## Fontes oficiais

### GTFS PBH

Página oficial:

https://dados.pbh.gov.br/dataset/gtfs

URL de download:

https://s3.amazonaws.com/mobilibus-uploads/gtfs/GTFSBHTRANS.zip

Descrição:

Conjunto de arquivos em padrão GTFS contendo a especificação dos serviços do sistema de transporte convencional, incluindo MOVE, e suplementar.

Observação:

Segundo o portal da PBH, a URL de download do GTFS é fixa, embora o arquivo disponível seja atualizado diariamente.

## Resultado da inspeção de linhas

O script `inspect_routes.py` foi testado com o GTFS da PBH extraído em:

```txt
data-exploration/data/raw/

## Script de inspeção de pontos

O script `inspect_stops.py` foi criado para ler o arquivo `stops.txt` do GTFS e listar os primeiros pontos encontrados.

Campos lidos inicialmente:

- `stop_id`
- `stop_name`
- `stop_lat`
- `stop_lon`

Esse script será usado para entender como os pontos de ônibus são representados no GTFS da PBH.

## Inspeção do arquivo trips.txt

O arquivo `trips.txt` foi inspecionado para entender como o GTFS representa viagens associadas às linhas.

Campos encontrados:

- `route_id`: identifica a linha/rota associada à viagem.
- `service_id`: identifica o serviço/calendário daquela viagem.
- `trip_id`: identifica uma viagem específica.
- `trip_headsign`: indica o destino ou letreiro da viagem.
- `direction_id`: indica o sentido da viagem.
- `shape_id`: relaciona a viagem ao traçado geográfico em `shapes.txt`.

Esse arquivo será importante para conectar linhas (`routes.txt`) com viagens específicas e, depois, com horários e trajetos.

## Inspeção do arquivo stop_times.txt

O arquivo `stop_times.txt` foi inspecionado para entender como o GTFS conecta viagens e pontos.

Campos principais encontrados:

- `trip_id`: identifica a viagem.
- `arrival_time`: horário planejado de chegada no ponto.
- `departure_time`: horário planejado de saída do ponto.
- `stop_id`: identifica o ponto de ônibus.
- `stop_sequence`: indica a ordem do ponto dentro da viagem.

Esse arquivo é importante porque conecta as viagens de `trips.txt` com os pontos de `stops.txt`.

Na prática, ele permite entender por quais pontos uma viagem passa e em qual ordem.


