# JobPilot AI — Relatório Técnico

> Diário técnico por fase. Nota curta ao fechar cada tarefa; seção completa ao fechar cada fase.

---

## Fase 0 — Fundação

### F0-T01 — Criar repositório e estrutura de docs (2026-11-10)
- **O que foi feito:** Inicializado repositório Git local, criado `.gitignore`, `LICENSE`, `.github/PULL_REQUEST_TEMPLATE.md`, `README.md`, `.env.example`, `design.md`. Docs do pacote já presentes em `docs/`.
- **Decisões e motivos:** Repositório sugerido `JoaumPdr/jobpilot-ai` (privado). Branch padrão `main`. Estrutura de branches: `main` → `develop` → `phase/00-fundacao`.
- **Problemas encontrados e soluções:** GitHub CLI não disponível localmente; usará MCP do GitHub no VS Code ou git local para criar o remoto.
- **Testes adicionados / cobertura:** N/A (fase de fundação).
- **Pendências / dívida técnica:** Criar repositório remoto no GitHub, configurar `origin`, enviar branches, configurar proteções, milestones e labels.

### F0-T02 — Ambiente Python com uv (2026-11-13)
- **O que foi feito:** Inicializado projeto com `uv init --python 3.12`, adicionadas dependências de desenvolvimento (`pytest`, `ruff`, `pre-commit`), criado `.python-version`, `.pre-commit-config.yaml` com hooks do Ruff, teste de sanidade em `tests/test_sanity.py`, ADR 0008 registrado em `docs/adr/0008-gerenciamento-com-uv.md`, `uv.lock` gerado e versionado.
- **Decisões e motivos:** `uv` escolhido por performance superior, lock file nativo, suporte a grupos de dependências (dev/prod) e integração com CI via `uv sync --locked`.
- **Problemas encontrados e soluções:** Nenhum. `uv sync`, `uv run pytest` e `uv run ruff check` funcionam corretamente.
- **Testes adicionados / cobertura:** 1 teste trivial (`test_sanity.py`) passando; lint limpo.
- **Pendências / dívida técnica:** Nenhuma para esta tarefa.

### F0-T03 — Docker Compose PostgreSQL e configuração tipada (2026-11-13)
- **O que foi feito:** Criado `docker-compose.yml` com PostgreSQL 16-alpine, healthcheck, volume persistente e porta 5432. Criado `app/core/config.py` com `Settings` usando `pydantic-settings` (BaseSettings) para configuração tipada e validada. Adicionadas dependências de produção `pydantic-settings` e `psycopg[binary]`. `.env.example` já continha `DATABASE_URL` correta.
- **Decisões e motivos:** PostgreSQL 16 como base; `pydantic-settings` para validação automática e tipagem; `psycopg[binary]` como driver assíncrono moderno.
- **Problemas encontrados e soluções:** Docker daemon não rodando no ambiente de execução, mas `docker compose config` valida sintaxe corretamente. Config falha com erro claro (`ValidationError: database_url Field required`) quando `.env` ausente.
- **Testes adicionados / cobertura:** Testes manuais de carregamento de config e validação de erro; lint limpo.
- **Pendências / dívida técnica:** Subir Docker daemon no ambiente para testes de integração completos.

### F0-T04 — Esqueleto FastAPI: /health, logging estruturado, tratamento de erros (2026-11-13)
- **O que foi feito:** Criado `app/main.py` com instância FastAPI, middleware de `request_id` (injetado via `contextvars` do structlog e retornado no cabeçalho `X-Request-ID`), handler global de exceções com formato JSON padronizado, e eventos de startup/shutdown com logging. Criado `app/api/routes/health.py` com rota `GET /health` que retorna status da aplicação e verifica conexão com o banco via psycopg. Criado `app/core/logging.py` com configuração structlog (JSON, timestamp, nível, stack trace). Criado `app/__init__.py`, `app/api/__init__.py`, `app/api/routes/__init__.py`. Testes de API em `tests/api/test_health.py` (3 testes: status 200, schema da resposta, cabeçalho X-Request-ID).
- **Decisões e motivos:** FastAPI escolhido por ser leve e assíncrono; structlog para logs estruturados JSON; psycopg diretamente para verificação de banco (SQLAlchemy vem na F0-T05); `/health` sempre retorna 200 com status `healthy` ou `degradado` do banco, nunca 500 por falha de conexão.
- **Problemas encontrados e soluções:** Módulo `app` não encontrado pelo pytest inicialmente — resolvido criando `app/__init__.py` e configurando `pythonpath = ["."]` no `pyproject.toml`.
- **Testes adicionados / cobertura:** 3 testes de API em `tests/api/test_health.py`; total de 4 testes passando (incluindo `test_sanity.py`); lint limpo.
- **Pendências / dívida técnica:** Docker daemon não disponível no ambiente para teste de integração com banco real; testado com `docker compose config` para validar sintaxe.

### F0-T05 — SQLAlchemy + Alembic com UUID e migração inicial (2026-11-13)
- **O que foi feito:** Criado `app/models/base.py` com Base declarativa SQLAlchemy (id UUID, `__tablename__` automático em snake_case), `app/core/database.py` com engine, SessionLocal e dependency `get_db()`, inicializado Alembic (`alembic.ini` com DATABASE_URL, `migrations/env.py` importando `Base.metadata`), migração inicial `000000000001` criada, ADR 0010 registrado em `docs/adr/0010-tipo-de-id-uuid.md`. Adicionadas dependências de produção `sqlalchemy` e `alembic`.
- **Decisões e motivos:** UUID escolhido como tipo de chave primária (segurança contra enumeração, fusão de dados facilitada). SQLAlchemy 2.x com estilo DeclarativeBase e `mapped_column`. Alembic para migrações versionadas.
- **Problemas encontrados e soluções:** `alembic revision --autogenerate` falhou por tentar conectar ao banco (Docker não disponível). Solução: criada migração inicial manualmente vazia; `alembic history` confirma que a migração é reconhecida.
- **Testes adicionados / cobertura:** Nenhum teste novo (banco não disponível para teste de integração). Lint limpo, testes existentes (4) continuam passando.
- **Pendências / dívida técnica:** Teste de integração com `upgrade`/`downgrade` contra banco real depende do Docker daemon estar disponível.

---

## Fases 1–7

*(A serem preenchidas conforme avanço das fases)*