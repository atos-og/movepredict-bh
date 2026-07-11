# Decisões técnicas — MovePredict BH

Este arquivo registra decisões importantes do projeto.

## 001 — Usar monorepo

Decidimos manter backend, frontend, exploração de dados, documentação e infraestrutura em um único repositório.

### Motivo

Como o projeto será desenvolvido por duas pessoas e tem objetivo de aprendizado, um monorepo facilita a organização, a documentação e a visualização completa do produto.

## 002 — Começar pela exploração dos dados

Decidimos não começar pelo frontend.

### Motivo

Antes de criar telas, precisamos entender quais dados existem, como acessá-los e se eles são suficientes para construir o produto.

## 003 - Isolar fontes de dados atrás de services

Routers FastAPI não acessam arquivos, banco ou provedores diretamente. A implementação atual usa `GtfsService`; fontes futuras implementarão contratos equivalentes.

### Motivo

Atos pode evoluir API e frontend enquanto Vinicius desenvolve coleta, PostGIS e previsão, reduzindo conflitos e preservando o contrato público.

## 004 - Padronizar envelopes HTTP

Respostas individuais usam `data`, listas usam `data` e `meta`, e falhas usam `error` com código, mensagem e request ID.

### Motivo

O frontend e integrações futuras conseguem tratar paginação e falhas sem conhecer exceções internas do backend.

## 005 - PostgreSQL com PostGIS e índices espaciais

Pontos e posições armazenam latitude/longitude WGS84 e uma geografia gerada com índice GiST. O
histórico usa também BRIN temporal e índices compostos. A imagem oficial PostGIS é executada em
`linux/amd64` no Apple Silicon para manter o ambiente igual ao de produção e aos testes.

## 006 - Não inventar `trip_id` para posições da PBH

O feed oficial informa veículo, código operacional de linha, sentido e posição, mas não `trip_id`.
A posição pode ser ligada à linha por uma tabela oficial; a viagem permanece nula até existir um
classificador validado por calendário, horário e progressão espacial.
