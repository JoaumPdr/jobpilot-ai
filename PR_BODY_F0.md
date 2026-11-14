## Fase
Fase 0 — Fundação (F0-T01 a F0-T07)

## O que mudou
- Repositório, branches (main, develop, phase/00-fundacao), .gitignore, licença e pacote de documentos em docs/
- Ambiente com uv (pyproject.toml, uv.lock, .python-version), Ruff, pytest e pre-commit
- Docker Compose do PostgreSQL, .env.example e configuração tipada
- Esqueleto FastAPI com /health, logging estruturado e tratamento padrão de erros
- SQLAlchemy + Alembic com migração inicial reversível
- CI no GitHub Actions (uv sync --locked, lint, testes, PostgreSQL, migração)
- Documentação base: README, design.md, RELATORIO.md, ADRs 0001 a 0010, privacy-and-sources.md
- `pyproject.toml`: projeto tratado como **virtual** (sem `[build-system]`), pois não distribuímos pacote/CLI; dependências de runtime (fastapi, structlog, uvicorn) movidas de `dev` para `project.dependencies`

## Critérios de aceitação (gate da Fase 0)
- [ ] CI verde com instalação por `uv sync --locked`
- [x] `uv sync` + `docker compose up` + `/health` respondendo 200 (app e banco)
- [x] `uv.lock` versionado e sincronizado com o `pyproject.toml`
- [x] Migração com upgrade e downgrade testados
- [x] ADRs 0001 a 0010 escritos
- [x] README inicial com link do repositório, badge de CI e objetivo do projeto

## Testes
- Novos: `tests/api/test_health.py` (3 testes: status 200, schema da resposta, cabeçalho X-Request-ID) + `tests/test_sanity.py` (1 teste trivial) = 4 testes no total
- Suíte completa verde: sim, localmente (`4 passed`), incluindo uma execução em **worktree limpo** (`git worktree add --detach HEAD`, sem `src/` e sem arquivos não versionados) que reproduz o checkout do CI: `uv sync --locked`, `ruff check`, `pytest` e `alembic upgrade/downgrade/upgrade` passaram. Link da execução do CI no GitHub: <preencher após o run>

## Docs atualizadas
- [x] README  [x] design.md  [x] RELATORIO.md  [ ] CHANGELOG.md  [x] STATUS.md  [x] BACKLOG.md  [x] ADRs

## Checklist de segurança/privacidade
- [x] Sem segredos  [x] Sem PII em logs  [x] .env fora do Git  [x] uv.lock sincronizado

## Riscos / pendências
- CI ainda não teve execução verde no GitHub (as 3 primeiras falharam por causa do build do pacote; causa raiz corrigida e validada em worktree limpo). Se falhar novamente, corrigir nesta branch e novo push — não mesclar.
- CHANGELOG.md ainda não existe (será criado na primeira release/tag de versão; a tag `fase-00` é de fase, não de release).
- Proteção de branch (PR obrigatório + CI verde) pode não estar disponível no plano do GitHub em uso; nesse caso seguimos por disciplina e isso fica registrado no `docs/STATUS.md`.
- `uv.lock` foi regenerado ao mover dependências de runtime; qualquer PR posterior deve rodar `uv sync --locked` antes de commitar.
