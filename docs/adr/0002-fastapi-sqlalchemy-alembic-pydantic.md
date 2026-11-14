# ADR 0002 — FastAPI + SQLAlchemy 2.x + Alembic + Pydantic v2
- Data: 2026-11-14
- Status: aceito

## Contexto
É necessário escolher o stack de backend para a API do JobPilot AI: framework web, ORM, ferramenta de migração e biblioteca de validação de dados.

## Decisão
Adotar:
- **FastAPI** como framework web (assíncrono, geração automática de OpenAPI/Swagger, tipagem estática).
- **SQLAlchemy 2.x** como ORM (maturidade, suporte a PostgreSQL, estilo 2.0 com `Mapped`/`mapped_column`).
- **Alembic** para migrações de banco de dados (integração nativa com SQLAlchemy, versionamento de esquema).
- **Pydantic v2** para validação de entrada/saída (integração nativa com FastAPI, performance, JSON Schema).

## Alternativas consideradas
- **Django + Django ORM:** Mais "baterias incluídas", mas menos flexível para arquitetura camadas e assíncrono nativo.
- **Flask + SQLAlchemy:** Mais leve, mas requer mais configuração manual para validação e OpenAPI.
- **Tortoise ORM / asyncpg:** Mais novo, menos ecossistema maduro que SQLAlchemy.

## Consequências
- Melhorias: Documentação automática da API via Swagger UI, tipagem forte em todo o backend, migrações versionadas e reversíveis.
- Piores: Curva de aprendizado do estilo SQLAlchemy 2.0 para desenvolvedores acostumados com 1.x.
