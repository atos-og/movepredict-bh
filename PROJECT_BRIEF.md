# Project Brief — MovePredict BH

## Visão geral

O MovePredict BH é uma plataforma web para consultar ônibus de Belo Horizonte em tempo real, visualizar posições no mapa, salvar histórico de movimentação e estimar chegada dos veículos nos pontos.

## Problema

Usuários do transporte público muitas vezes não sabem com precisão onde o ônibus está, se ele está atrasado ou quanto tempo falta para chegar ao ponto.

## Solução proposta

Criar uma aplicação que use dados públicos de transporte para mostrar:

- ônibus em tempo real;
- busca por linha;
- busca por ponto;
- mapa com veículos;
- histórico de posições;
- previsão simples de chegada;
- rankings de confiabilidade das linhas.

## Objetivo de aprendizado

O projeto também serve como trilha prática de aprendizado. Queremos aprender:

- Git e GitHub;
- organização de projeto;
- Python;
- FastAPI;
- PostgreSQL;
- análise de dados com Pandas;
- dados geográficos;
- APIs;
- frontend com Next.js;
- TypeScript;
- mapas com Leaflet;
- testes;
- deploy;
- documentação;
- colaboração em dupla.

## Stack

- Frontend: Next.js + TypeScript
- Backend: Python + FastAPI
- Banco: PostgreSQL
- Geodados: PostGIS, depois do básico
- Dados/análise: Python + Pandas
- Modelo inicial: Scikit-learn, depois de termos histórico
- Mapas: Leaflet
- Deploy: Vercel, Render/Railway/Fly.io, Supabase/Neon/Railway

## Escopo inicial

Na primeira versão, queremos:

1. Explorar os dados públicos disponíveis.
2. Listar linhas de ônibus.
3. Listar pontos de ônibus.
4. Obter posições de veículos em tempo real.
5. Criar uma API simples.
6. Mostrar veículos em um mapa.
7. Salvar histórico básico.
8. Criar uma previsão simples de chegada.

## Fora do escopo inicial

Por enquanto, não vamos implementar:

- autenticação de usuários;
- aplicativo mobile nativo;
- machine learning avançado;
- microsserviços;
- Kafka;
- Kubernetes;
- sistema complexo de notificações;
- arquitetura exagerada.

## Regra principal

Nada entra no projeto se a dupla não consegue entender, rodar, testar e explicar.