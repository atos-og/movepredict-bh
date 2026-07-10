# Preparação de deploy

Nenhum recurso foi publicado e nenhuma credencial é necessária para validar esta configuração.

## Artefatos

- `backend/Dockerfile`: API em Python 3.12.
- `frontend/Dockerfile`: build standalone do Next.js em Node 22.
- `compose.yaml`: integração local com volume GTFS somente leitura.
- `.env.example`, `backend/.env.example` e `frontend/.env.example`: catálogo de configuração.

## Pré-requisitos para publicar

1. Escolher provedores de frontend, API e PostgreSQL/PostGIS.
2. Definir a URL pública da API em `NEXT_PUBLIC_API_URL` durante o build.
3. Definir a origem pública do frontend em `MOVEPREDICT_CORS_ORIGINS`.
4. Disponibilizar GTFS por volume/objeto ou concluir a migração da leitura para PostgreSQL.
5. Adicionar secrets somente no painel do provedor ou GitHub Environments.
6. Executar smoke tests em `/health`, `/lines` e no frontend.

## Estratégia sugerida

Enquanto o banco não estiver integrado, usar contêineres com volume GTFS persistente. Depois da entrega do PostGIS, substituir `GtfsService` por um adaptador de repositório SQL e manter os mesmos schemas públicos.

O workflow de CI apenas valida commits e pull requests; ele não contém etapa de deploy.
