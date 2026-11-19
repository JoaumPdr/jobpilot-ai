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
- **Problemas encontrados e soluções:** Docker daemon inicialmente não disponível; depois que ficou disponível, a porta 5432 estava ocupada pelo `com.docker.backend.exe` (Docker Desktop). Solução: mapear `5433:5432` no docker-compose.yml e atualizar `DATABASE_URL` no `.env.example` e `alembic.ini`. psycopg v3 não aceita prefixo `postgresql+psycopg://` (formato SQLAlchemy); solução: função `_psycopg_url()` converte para `postgresql://` antes de conectar. Config falha com erro claro (`ValidationError: database_url Field required`) quando `.env` ausente.
- **Testes adicionados / cobertura:** Testes manuais de carregamento de config, validação de erro, conexão com banco real via psycopg, `alembic upgrade head` e `downgrade -1` contra banco real, endpoint `/health` retornando `database.status = healthy`. Lint limpo.
- **Pendências / dívida técnica:** Nenhuma para esta tarefa. Todas as verificações com banco real foram concluídas com sucesso.

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

### F0-T06 — CI no GitHub Actions com uv (2026-11-14)
- **O que foi feito:** Criado `.github/workflows/ci.yml` com workflow disparado em push/PR para branches `main`, `develop` e `phase/*`. O CI: instala `uv` via `astral-sh/setup-uv@v3`, sincroniza dependências com `uv sync --locked` (falha se lock desatualizado), roda `ruff check`, executa `pytest` com serviço PostgreSQL 16 em container (porta 5433), e testa migração Alembic (`upgrade head` + `downgrade -1` + `upgrade head`).
- **Decisões e motivos:** Seguir o padrão definido no `GUIA_DOCS_E_GIT.md` seção B.8; usar porta 5433 no service container devido a conflito com Docker Desktop backend na porta 5432 do host.
- **Problemas encontrados e soluções:** Nenhum. YAML validado localmente; testes e lint passando.
- **Testes adicionados / cobertura:** Nenhum teste novo (CI testa testes existentes). Lint limpo, 4 testes passando.
- **Pendências / dívida técnica:** CI não foi executado no GitHub ainda (primeira execução será no próximo push/PR).

### F0-T07 — Docs-base: ADRs, privacy-and-sources, README (2026-11-14)
- **O que foi feito:** Criados ADRs 0001 (monólito modular), 0002 (FastAPI+SQLAlchemy+Alembic+Pydantic), 0003 (PostgreSQL), 0004 (LangGraph), 0005 (LLMProvider interface), 0006 (matching determinístico), 0007 (single-user MVP), 0009 (GitHub como remoto). Junto com 0008 (uv) e 0010 (UUID), totalizam 10 ADRs. Criado `docs/privacy-and-sources.md` com política LGPD e regras para fontes de vagas. README revisado: nome, link do repositório, badge de CI, descrição, objetivo, princípios, status, roadmap, pré-requisitos, instalação/ configuração/ execução via `uv`, testes e lint, arquitetura, estrutura de pastas, como contribuir/retomar, privacidade, licença.
- **Decisões e motivos:** Seguir o `GUIA_DOCS_E_GIT.md` seção A.1 e A.3 para garantir que todos os documentos obrigatórios existam antes do F0-GATE.
- **Problemas encontrados e soluções:** Nenhum.
- **Testes adicionados / cobertura:** Nenhum (tarefa de documentação). 4 testes existentes continuam passando; lint limpo.
- **Pendências / dívida técnica:** CHANGELOG.md será criado ao fazer a tag `fase-00` (F0-GATE).

### Correções de CI no F0-GATE (2026-11-14)
- **Sintoma:** `uv sync --locked` falhava no GitHub Actions com `Expected a Python module at: src/jobpilot_ai/__init__.py`, enquanto localmente passava.
- **Tentativas que NÃO resolveram:** `e9b5a54` removeu `[project.scripts]` (não era a causa) e `00060f2` adicionou `[tool.uv] no-build-package` (o uv ignora essa opção para o projeto raiz).
- **Causa raiz (dupla):**
  1. O `pyproject.toml` declarava `[build-system]` com `uv_build`. Quando existe build backend, o `uv` **sempre** tenta construir o projeto raiz — e o `uv_build` espera `src/jobpilot_ai/__init__.py` (ou `jobpilot_ai/`).
  2. Localmente o build passava **apenas** porque havia uma pasta `src/jobpilot_ai/` não versionada (sobra do `uv init`), inexistente no checkout do CI. Isso mascarava o erro por três execuções.
- **Solução:** removido `[build-system]` — o `uv` passa a tratar o projeto como **virtual** (não instala a si mesmo). Correto para o nosso caso, pois não distribuímos pacote/CLI: a app roda do diretório raiz via `uvicorn app.main:app`, os testes via `pythonpath = ["."]` e o Alembic via `prepend_sys_path = .`.
- **Ajuste de bônus:** `fastapi`, `structlog` e `uvicorn` estavam em `[dependency-groups] dev`, apesar de serem dependências de runtime; movidos para `[project] dependencies` (um `uv sync --no-dev` antes quebraria a app).
- **Verificação (por que agora acredito que passa):** criado um `git worktree` destacado em `HEAD` (árvore limpa, **sem** `src/`, igual ao CI) e executadas as quatro etapas do workflow: `uv sync --locked` sem etapa de build, `ruff check` limpo, `pytest` 4 passed, `alembic upgrade/downgrade/upgrade` OK. Worktree removido ao final.
- **Lição registrada:** qualquer validação "passa local / falha no CI" deve ser repetida em worktree limpo, nunca na árvore de trabalho com arquivos não versionados.
- **Inconsistência detectada na revisão do gate:** a tag `fase-00` foi criada em `3df13a3`, antes das correções de CI, ou seja, marcava um estado que falhou no CI. **Resolvido:** após o PR #4 ficar verde e ser mesclado, a tag local e remota foi apagada e recriada em `cbbeb65` (merge commit em `develop`).

### Higiene pós-gate e preparação da F1 (2026-11-14)
- **Incidente de fluxo:** o PR do fechamento da Fase 0 foi aberto contra `main` em vez de `develop`, deixando `develop` sem os commits de documentação. Correção por realinhamento: branch criada a partir de `main` e PR para `develop`, o que torna `main` ancestral de `develop` e mantém o fluxo normal nas próximas fases.
- **Skill de terceiros:** `.agents/skills/git-create-repo/` (origem `zc277584121/mygitplugin`) foi instalado por engano neste contexto — cria repositórios **públicos** por padrão e fixa outra conta do GitHub. Decisão: fica fora do versionamento (`.gitignore`) e `skills-lock.json` voltou ao estado versionado.
- **Formatação:** `ruff format --check` falhava em 11 arquivos (o hook existia no pre-commit, mas nunca rodou, e o CI só validava lint). Baseline aplicado antes de iniciar a F1 e verificação adicionada ao CI, conforme GUIA §B.8.
- **Preparação da F1-T01:** desenho das tabelas do perfil, constraints, migração, banco de teste dedicado (`jobpilot_test`) e arquivos previstos documentados no `STATUS.md`, sem escrever código.

---

## Fase 0 — Fundação (concluída)

**Gate de saída:** Todos os critérios do `PLANO.md` §11 atendidos:
- [x] Repositório GitHub privado (`JoaumPdr/jobpilot-ai`) com branches `main`, `develop`, `phase/00-fundacao`
- [x] Ambiente Python com `uv` (`pyproject.toml`, `.python-version`, `uv.lock` versionado)
- [x] Docker Compose PostgreSQL 16 funcionando (porta 5433 no host)
- [x] FastAPI `/health` respondendo 200 com verificação de banco
- [x] SQLAlchemy + Alembic com UUID, migração inicial
- [x] CI GitHub Actions com `uv sync --locked`, ruff, pytest, Alembic — verde no PR #4
- [x] ADRs 0001–0010 criados
- [x] PR `phase/00-fundacao` → `develop` mesclado com histórico (merge commit `cbbeb65`)
- [x] Tag `fase-00` publicada no remoto, apontando para `cbbeb65`

**Métricas:** 4 testes automatizados; 10 ADRs; 43 arquivos no merge da fase.

**Aprendizado principal:** validação "passa local, falha no CI" deve ser reproduzida em `git worktree` limpo — arquivos não versionados (no caso, `src/jobpilot_ai/` deixado pelo `uv init`) escondem erros de build por várias execuções.

**Próximo:** Fase 1 — criar `phase/01-nucleo-sem-ia` a partir de `develop` e iniciar F1-T01 (modelos do perfil).

---

## Fase 1 — Núcleo sem IA

### F1-T08 — Listagem e filtros de vagas (2026-11-19)
- **O que foi feito.** `GET /jobs` com filtros combináveis e paginação. Arquivadas e duplicatas confirmadas ficam ocultas por padrão e podem ser incluídas separadamente.
- **Decisões e motivos.** A ordenação por data de cadastro e UUID desempata vagas do mesmo lote. Buscar um item adicional permite calcular `has_more` na mesma consulta da página.
- **Testes.** 23 testes de API cobrem filtros, paginação, validação e a meta de 500 ms com 10 mil vagas em PostgreSQL.
- **Pendência.** O filtro por status de candidatura está previsto para a F1-T10, depois do modelo criado pela F1-T09.

### F1-T09 — Modelos e migração de candidaturas (2026-11-19)
- **O que foi feito.** Modelos de candidatura e histórico de status com a migração reversível `000000000004`.
- **Decisões e motivos.** A unicidade por candidato e vaga evita registros concorrentes duplicados. A exclusão de perfil remove seus históricos, e as vagas vinculadas podem ser arquivadas com o histórico preservado.
- **Testes.** 13 testes de constraints e 289 testes na suíte completa. O ciclo de migração validou a preservação de registros de perfil e vaga em PostgreSQL. A comparação do schema detectou somente duas diferenças de índices já presentes na revisão anterior.

## Fases 2–7

*(A serem preenchidas conforme avanço das fases)*
