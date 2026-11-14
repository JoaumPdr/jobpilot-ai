# JobPilot AI — STATUS (estado vivo)

> Vira `docs/STATUS.md`. **Atualizar ao final de toda sessão** (e após cada tarefa concluída).
> Objetivo: qualquer agente ou pessoa retoma o trabalho em menos de 2 minutos lendo só este arquivo.
> Só o Orquestrador (ou o agente único) edita este arquivo.

---

## 1. Retomada rápida

| Campo | Valor |
|-------|-------|
| **Última atualização** | 2026-11-14 03:05 (UTC) |
| **Fase atual** | Fase 1 — Núcleo sem IA (**terreno pronto, F1-T01 não iniciada**) |
| **Branch da fase** | `phase/01-nucleo-sem-ia` (criada a partir de `develop` e publicada) |
| **Tarefa atual** | F1-T01 — Modelos e migração do perfil (aguardando sinal verde do JP) |
| **Branch da tarefa** | a criar: `feat/f1-t01-modelos-perfil` |
| **Estado da tarefa** | não iniciada (desenho e ambiente prontos) |
| **Último commit** | `ff60748` — Merge pull request #6 from JoaumPdr/chore/f0-higiene-desenvolvimento |
| **Testes** | verdes (4 passed) |
| **CI** | verde no PR #4; verifica lint **e** `ruff format --check` (GUIA §B.8) |
| **Repositório remoto** | `https://github.com/JoaumPdr/jobpilot-ai` |
| **Sincronização com o remoto** | em dia |
| **Último push** | 2026-11-14 03:05 (UTC) — branch `phase/01-nucleo-sem-ia` |
| **PR aberto** | nenhum |
| **Última tag publicada** | `fase-00` → aponta para `cbbeb65` (merge commit em `develop`, CI verde) |
| **MCP do GitHub** | indisponível (usando git local) |

### Próxima ação exata (uma frase, imperativa)

> Criar `feat/f1-t01-modelos-perfil` a partir de `phase/01-nucleo-sem-ia` e implementar os modelos, a migração e os testes de constraint do perfil.

---

## 2. O que foi feito na última sessão

- F0-T01 concluída: repositório GitHub criado, branches enviadas, estrutura de docs e arquivos base commitados.
- F0-T02 concluída: ambiente Python configurado com `uv`, dependências de dev, pre-commit, teste de sanidade e ADR 0008.
- F0-T03 concluída: `docker-compose.yml` com PostgreSQL 16 (porta 5433 no host devido a conflito com Docker Desktop backend na 5432), `.env.example` e `alembic.ini` atualizados para porta 5433, `app/core/config.py` com validação de ambiente, `app/api/routes/health.py` com conversão de URL SQLAlchemy para psycopg v3. Verificado com banco real: container saudável, `alembic upgrade head` + `downgrade -1` funcionam, `/health` retorna 200 com database.status = healthy.
- F0-T04 concluída: `app/main.py` com FastAPI, middleware `request_id`, handler global de exceções; `app/api/routes/health.py` com `GET /health`; `app/core/logging.py` com structlog JSON; `tests/api/test_health.py` com 3 testes de API. 4 testes passando, lint limpo.
- F0-T05 concluída: `app/models/base.py` com Base declarativa (UUID, __tablename__ automático), `app/core/database.py` com engine/SessionLocal/get_db, Alembic inicializado, ADR 0010 (UUID) registrado.
- F0-T06 concluída: `.github/workflows/ci.yml` com `uv sync --locked`, ruff, pytest com serviço PostgreSQL, teste de migração Alembic.
- F0-T07 concluída: ADRs 0001–0007 e 0009 criados (total de 10 ADRs incluindo 0008 e 0010), `docs/privacy-and-sources.md` criado, README revisado e completo conforme GUIA_DOCS_E_GIT.md.
- F0-GATE **concluído**: PR #4 (`phase/00-fundacao` → `develop`) mesclado com CI verde e merge commit `cbbeb65`; tag `fase-00` recriada nesse commit (a tag anterior apontava para `3df13a3`, que falhou no CI); `PR_BODY_F0.md` removido da raiz.
- Higiene pós-gate: skill de terceiros ignorado no `.gitignore` (permanece instalado localmente), `skills-lock.json` restaurado, baseline de `ruff format` aplicado e `ruff format --check` adicionado ao CI. Preparação da F1-T01 documentada, sem código.

---

## 3. O que falta na tarefa atual (lista concreta)

- [x] Abrir PR `phase/00-fundacao` → `develop` ✅
- [x] Conferir CI verde no GitHub antes de mesclar ✅
- [x] Mesclar com **"Create a merge commit"** (PR #4 → `cbbeb65`) ✅
- [x] Tag `fase-00` recriada no merge commit e publicada no remoto ✅
- [x] Seção da Fase 0 no `RELATORIO.md` ✅
- [x] Resolver skill de terceiros (`.gitignore` + `skills-lock.json` restaurado) ✅
- [x] Baseline de formatação (`ruff format`) + `ruff format --check` no CI ✅
- [x] Mesclar a higiene em `develop` ✅ (PR #6 entrou em `main`; `develop` foi fast-forwarded para `ff60748`)
- [x] Criar `phase/01-nucleo-sem-ia` a partir de `develop` e publicar ✅
- [x] Verificar ambiente (uv sync, ruff, pytest, Alembic) e banco na porta 5433 ✅
- [ ] Iniciar F1-T01 (modelos e migração do perfil) — **aguardando sinal verde do JP**

### Plano da F1-T01 (desenho pronto; nenhum código escrito)

**Arquivos previstos**
- `app/models/candidate.py` — `Candidate` (`name`, `email` opcional, `resume_text`, `headline`, `education` JSONB, `languages` JSONB, timestamps)
- `app/models/preferences.py` — `CandidatePreference` (1:1 por `candidate_id` único)
- `app/models/skill.py` — `Skill` (`canonical_name` único, `category`, `aliases` JSONB) e `CandidateSkill` (único `(candidate_id, skill_id)`)
- `app/models/experience.py` — `CandidateExperience` (FK, `start_date`/`end_date`, `description`, `skills_used` JSONB)
- `app/models/__init__.py` — exportar modelos para o Alembic enxergar o metadata
- `migrations/versions/000000000002_profile_tables.py` — migração reversível
- `tests/db/conftest.py` — fixture de banco de teste dedicado (`jobpilot_test`)
- `tests/db/test_profile_constraints.py` — constrains (únicos, FKs, CHECK)
- `docs/data-model.md` — tabelas, relações, constraints, enums, diagrama

**Decisões de desenho já tomadas**
- `candidate_skills.level`: `VARCHAR` + `CHECK` (iniciante/intermediário/avançado) — evita `ALTER TYPE` do ENUM nativo em evoluções
- `min_salary`: `Numeric(12, 2)`; sem coluna de moeda por ora (registrado no data-model)
- `skills.category`: texto livre até a taxonomia da F2-T01
- FKs com `ON DELETE CASCADE`; `end_date >= start_date` via CHECK; `years >= 0`
- Banco de teste dedicado `jobpilot_test`, criado por fixture a partir de `TEST_DATABASE_URL` (default derivado de `DATABASE_URL`), com `alembic upgrade head` na sessão

**Fora do escopo da F1-T01:** rotas, serviços e validação Pydantic dos JSONB (F1-T02) e tabelas de vagas (F1-T03).

### Itens fora do escopo da Fase 0 (resolvido)

- ~~`skills-lock.json` modificado e `.agents/skills/git-create-repo/` não versionado~~ → skill de terceiros ignorado no `.gitignore` e lock restaurado ao estado versionado (decisão registrada na seção 6).

---

## 4. Progresso por fase

| Fase | Estado | Tag | Gate |
|------|--------|-----|------|
| 0 — Fundação | concluída | `fase-00` (`cbbeb65`) | ✅ PR #4 mesclado com CI verde |
| 1 — Núcleo sem IA | em preparação (F1-T01 não iniciada) | — | — |
| 2 — Matching | não iniciada | — | — |
| 3 — Camada LLM | não iniciada | — | — |
| 4 — Orquestração (MVP v0.1.0) | não iniciada | — | — |
| 5 — Assistente de currículo | não iniciada | — | — |
| 6 — Dashboard e analytics | não iniciada | — | — |
| 7 — Hardening e release (v1.0.0) | não iniciada | — | — |

*(Estados: não iniciada · em andamento · gate pendente · concluída)*

---

## 5. Problemas, bloqueios e dívida técnica

| Data | Tipo (bloqueio/bug/dívida/dúvida) | Descrição | Tarefa | Situação |
|------|-----------------------------------|-----------|--------|----------|
| 2026-11-14 | processo | PRs #5 e #6 foram abertos com base `main` em vez de `develop` (o GitHub mantém `main` como base padrão); corrigido por fast-forward de `develop` até `main`. **Mitigação:** abrir PRs sempre pela URL com base explícita (`/compare/develop...branch`) | F0-GATE | resolvido |
| 2026-11-14 | dívida | `app/main.py` usa `@app.on_event` (depreciado no FastAPI); migrar para `lifespan` | F1 | aberto |
| 2026-11-14 | dívida | `.agents/skills/alethe` versionado (~1,5 MB de assets) infla o repositório; reavaliar se precisa ficar versionado | — | aberto |

*(Testes vermelhos ou `xfail` ativos devem ser listados aqui com o motivo.)*

---

## 6. Decisões tomadas (resumo; detalhe em ADR quando relevante)

| Data | Decisão | Motivo | ADR |
|------|---------|--------|-----|
| 2026-11-10 | Repositório GitHub: `JoaumPdr/jobpilot-ai` privado | Nome sugerido no PLANO.md, conta do JP | — |
| 2026-11-10 | Branch strategy: `main` → `develop` → `phase/*` | Modularidade, resiliência, gates por fase | 0009 (sincronização GitHub) |
| 2026-11-13 | Gerenciador de dependências: `uv` | Performance, lock file, grupos de dependências | 0008 |
| 2026-11-14 | Skills de agentes: versionar apenas o Alethe; skills de terceiros ficam fora do repo (`.gitignore`) | plugin de terceiros criava repositórios **públicos** por padrão e fixava outra conta do GitHub, inadequado a repo privado | — |
| 2026-11-14 | `ruff format --check` passa a rodar no CI | GUIA §B.8 exige lint **e** formatação; baseline aplicado antes de iniciar a F1 | — |

---

## 7. Perguntas pendentes para o JP

- [ ] Confirmar se deseja configurar proteção de branch no GitHub (requer plano pago ou settings de admin) ou seguir por disciplina registrada no STATUS.md
- [ ] Decidir se `phase/00-fundacao` deve ser apagada após o gate (hoje preservada no remoto)

---

## 8. Observações

- Divergências entre este arquivo e o estado do Git (se houver): STATUS.md estava desatualizado (mostrava F0-T01 como não iniciada), corrigido agora para refletir o estado real do Git.
- Variáveis de ambiente novas desde a última sessão: nenhuma (`.env.example` já existe).

---

## 9. Checklist de encerramento de sessão (conferir antes de parar)

- [ ] Testes verdes **ou** falhas isoladas e listadas em §5
- [ ] Tudo commitado (`chore(wip)` se incompleto)
- [ ] Push feito e **verificado** (`git status -sb` sem `ahead`; branch visível no GitHub)
- [ ] Campos de sincronização da §1 atualizados (remoto, último push, PR aberto, CI no GitHub)
- [ ] §1 e §3 atualizados com a próxima ação exata
- [ ] `BACKLOG.md` marcado
- [ ] `RELATORIO.md` com nota curta da tarefa (se concluída)
- [ ] `.env.example` sincronizado (se houve nova variável)
- [ ] `uv.lock` commitado junto com o `pyproject.toml` (se houve mudança de dependência)