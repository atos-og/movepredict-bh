# Verificacao da entrega conjunta

Data: 13/07/2026. Branch: `codex/finish-joint-delivery`.

## Executado nesta maquina

- Feed oficial PBH: HTTP 200 em uma tentativa.
- Payload atual: 29.460 posicoes aceitas e zero erro de parsing.
- Campo mais recente observado: `2026-07-13T14:57:03Z`.
- Backend: 28 testes passaram e 2 foram pulados por dependerem de PostgreSQL/PostGIS.
- Ruff: lint e formatacao passaram em 60 arquivos.
- Frontend: 4 testes unitarios passaram.
- ESLint e TypeScript passaram.
- Build Next.js passou.
- Playwright portavel: 7 testes de teclado, acessibilidade e responsividade passaram.

Nenhum payload bruto da PBH foi adicionado ao Git. A verificacao registrou somente contagens,
status e estrutura dos campos.

## Nao executado

- Testes PostgreSQL/PostGIS locais: Docker nao esta instalado ou disponivel neste terminal.
- Endpoints publicados: nao existe URL de staging provisionada.
- Soak test de varias horas: depende do staging e do collector ativos.
- Comparacao ETA/chegada e teste de campo: dependem da amostra real e atividade presencial.

Esses itens nao devem ser marcados como concluidos apenas porque os scripts e protocolos existem.

## Atualizacao do assistente porta a porta - 15/07/2026

- Backend completo: 34 testes passaram e 2 testes PostGIS foram pulados.
- Ruff check e formatacao: 50 arquivos aprovados.
- Frontend: 5 testes unitarios passaram.
- Playwright: 9 testes de acessibilidade, teclado e responsividade passaram.
- ESLint, TypeScript e build de producao Next.js passaram.
- Busca real por `Mineirao`: Nominatim retornou coordenadas e atribuicao OSM pelo novo endpoint.
- Docker Desktop 29.6.1 respondeu e os perfis `routing` e `routing-tools` foram validados.
- O recorte OSM de Belo Horizonte foi validado pelo `osmium` (10,4 MB).
- O GTFS de roteamento preservou 6 servicos ativos e 51.470 viagens, sem alterar o feed fonte.
- O OpenTripPlanner 2.9.0 gerou um grafo de 104,2 MB com 9.866 pontos e 870 padroes.
- A consulta real Praca Sete -> Mineirao retornou 3 alternativas pelo endpoint
  `/journeys/plan`, com caminhada, embarque, baldeacao, desembarque e caminhada final.
- O pacote de icones foi inspecionado em 512 x 512 e permaneceu legivel sem texto.

Ainda depende de ambiente/operacao: executar soak test de varias horas, acumular a amostra minima
de ETA e realizar o teste fisico em BH. Alguns nomes do feed PBH contem o caractere de substituicao
Unicode na propria fonte; isso nao impede o roteamento, mas deve ser acompanhado com o provedor.

## Auditoria funcional local - 15/07/2026

Ambiente executado com Docker Compose: PostgreSQL/PostGIS, API, collector, retention,
OpenTripPlanner e frontend. O banco continha 327 linhas, 9.914 pontos, 113.621 viagens,
6.672.897 relacoes viagem/parada e 1.108 shapes. O collector processou um ciclo real da PBH
com 21.316 registros recebidos e 21.291 posicoes unicas inseridas.

- Backend: 36 testes passaram e 2 testes de integracao PostGIS opcionais foram pulados.
- Ruff: lint e formatacao passaram em 58 arquivos.
- Frontend: 5 testes unitarios passaram.
- Playwright: 21 testes passaram (9 de teclado/responsividade e 12 snapshots do roadmap).
- ESLint, TypeScript, build de producao Next.js e validacao do Docker Compose passaram.
- Viewports 360x800, 375x812, 390x844, 414x896, 768x1024 e 1440x900 foram inspecionados
  sem overflow horizontal.
- Fluxos reais validados: 327 linhas, busca sem resultado, detalhe e mapa da linha 1170,
  9.914 pontos, busca por endereco, previsoes por parada, favoritos e menu adicional.
- Rota real Praca Sete -> Mineirao validada com geocodificacao, tres preferencias,
  alternativas ordenadas, passo a passo, salvamento offline, inicio e encerramento da viagem.
- Estados validados: localizacao ausente/bloqueada, sem veiculo, dados programados, vazio,
  erro de linha e acompanhamento online. Nenhum erro ou aviso permaneceu no console.
- Endpoints reais de linhas, itinerario, veiculos e previsoes responderam com HTTP 200.

Correcoes feitas durante a auditoria: proxy de API de mesma origem para eliminar IP local
obsoleto, consultas GTFS pesadas movidas para PostgreSQL com fallback CSV, ordenacao de rotas
por preferencia, origem manual, remocao de distancias falsas sem geolocalizacao, estados de
busca/erro recuperaveis e traducao dos nomes genericos do OTP.

Continuam fora desta verificacao: soak test de varias horas, carga sustentada, publicacao de
staging, metricas ETA com amostra minima e validacao fisica em Belo Horizonte.
