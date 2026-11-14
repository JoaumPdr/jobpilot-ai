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

---

## Fases 1–7

*(A serem preenchidas conforme avanço das fases)*