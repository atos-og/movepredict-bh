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




