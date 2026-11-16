# JobPilot AI — STATUS (estado vivo)

> Vira `docs/STATUS.md`. **Atualizar ao final de toda sessão** (e após cada tarefa concluída).
> Objetivo: qualquer agente ou pessoa retoma o trabalho em menos de 2 minutos lendo só este arquivo.
> Só o Orquestrador (ou o agente único) edita este arquivo.

---

## 1. Retomada rápida

| Campo | Valor |
|-------|-------|
| **Última atualização** | 2026-11-16 (UTC) |
| **Fase atual** | Fase 1 — Núcleo sem IA (**em andamento: F1-T01 concluída**) |
| **Branch da fase** | `phase/01-nucleo-sem-ia` (criada a partir de `develop` e publicada) |
| **Tarefa atual** | F1-T01 — Modelos e migração do perfil (**concluída; integrada pelo PR #8**) |
| **Ficha da tarefa** | `docs/tasks/FASE-01/F1-T01.md` (planejamento e notas de retomada) |
| **Branch da tarefa** | `feat/f1-t01-modelos-perfil` (mesclada no PR #8; preservada) |
| **Estado da tarefa** | concluída — modelos, migração, testes e documentação integrados; CI verde |
| **Último commit** | `7326d67` — Merge pull request #8 (F1-T01) |
| **Testes** | verdes (21 passed: 4 API/sanidade + 17 de constraint) |
| **CI** | verde no PR #8 (run 43950994777); lint, formatação, pytest e migração |
| **Repositório remoto** | `https://github.com/JoaumPdr/jobpilot-ai` |
| **Sincronização com o remoto** | em dia |
| **Último push** | 2026-11-16 20:40 (UTC) — branch `phase/01-nucleo-sem-ia` |
| **PR aberto** | nenhum |
| **Última tag publicada** | `fase-00` → aponta para `cbbeb65` (tag anotada `28f5be7`, merge commit em `develop`, CI verde) |
| **MCP do GitHub** | indisponível; `gh` CLI autenticado usado como alternativa (PRs e CI consultados) |

### Próxima ação exata (uma frase, imperativa)

> Iniciar a F1-T02 (serviço e rotas do perfil), após autorização do JP: criar a ficha a partir do BACKLOG e seguir o ciclo da §3.

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
- Sessão de padronização documental (2026-11-16): divisão de responsabilidades entre `BACKLOG.md` (fonte canônica), `STATUS.md` (retomada) e fichas `docs/tasks/` (execução); política de fichas just-in-time formalizada em `ALETHE_INSTRUCOES.md` §3A; ficha `docs/tasks/FASE-01/F1-T01.md` criada com o plano antes detalhado aqui. PR #7 aberto (docs → `phase/01`) com CI verde. Nenhum código alterado.
- **F1-T01 implementada (2026-11-16):** 5 tabelas do perfil + migração reversível `000000000002`, `migrations/env.py` registrando todos os modelos, 17 testes de constraint contra PostgreSQL real com banco isolado `jobpilot_test` (salvaguarda `_test`), `docs/data-model.md` com Mermaid e `TEST_DATABASE_URL` documentada. PR #8 integrado por merge commit com CI verde.

---

## 3. O que falta na tarefa atual (lista concreta)

**Tarefa atual:** F1-T01 — modelos e migração do perfil · **concluída** · integrada pelo PR #8 (CI verde).
**Planejamento detalhado:** [`docs/tasks/FASE-01/F1-T01.md`](tasks/FASE-01/F1-T01.md). Critérios de aceitação canônicos: `docs/BACKLOG.md` → F1-T01.

- [x] Base da Fase 0 e higiene mescladas (`cbbeb65`, `ff60748`) ✅
- [x] Criar `phase/01-nucleo-sem-ia` a partir de `develop` e publicar ✅
- [x] Verificar ambiente (uv sync, ruff, pytest, Alembic) e banco na porta 5433 ✅
- [x] Padronizar documentação (BACKLOG/STATUS/fichas) — PR #7 mesclado ✅
- [x] Executar a ficha: modelos, migração, `migrations/env.py`, fixture e testes ✅
- [x] `docs/data-model.md` (Mermaid) e `TEST_DATABASE_URL` documentados ✅
- [x] Suíte verde (21 passed), lint/formatação limpos, migração upgrade/downgrade ✅
- [x] Mesclar o PR #8 (tarefa → fase) e marcar a F1-T01 no `BACKLOG.md` ✅
- [ ] Iniciar a F1-T02 (serviço e rotas do perfil) — aguardando autorização do JP

### Itens fora do escopo da Fase 0 (resolvido)

- ~~`skills-lock.json` modificado e `.agents/skills/git-create-repo/` não versionado~~ → skill de terceiros ignorado no `.gitignore` e lock restaurado ao estado versionado (decisão registrada na seção 6).

---

## 4. Progresso por fase

| Fase | Estado | Tag | Gate |
|------|--------|-----|------|
| 0 — Fundação | concluída | `fase-00` (`cbbeb65`) | ✅ PR #4 mesclado com CI verde |
| 1 — Núcleo sem IA | em andamento (F1-T01 concluída; próxima F1-T02) | — | — |
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
| 2026-11-16 | Divisão de responsabilidades documental: BACKLOG é fonte canônica das tarefas/critérios; ficha (`docs/tasks/`) detalha a execução; STATUS registra estado e retomada. Fichas são just-in-time e opcionais por complexidade; sem fichas retroativas para a F0 | eliminar ambiguidade e duplicação (o STATUS acumulava o plano da F1-T01) | — |
| 2026-11-16 | Perfil: e-mail único case-insensitive via `lower(email)`; `level` NULL = desconhecido; `years` em `candidate_skills` e `candidate_experiences` com CHECK; timestamps `TIMESTAMPTZ` com `now()` do servidor; `TEST_DATABASE_URL` isolada | decisões aprovadas pelo JP na preparação da F1-T01 | — |

---

## 7. Perguntas pendentes para o JP

- [ ] Confirmar se deseja configurar proteção de branch no GitHub (requer plano pago ou settings de admin) ou seguir por disciplina registrada no STATUS.md
- [ ] Decidir se `phase/00-fundacao` deve ser apagada após o gate (hoje preservada no remoto)

---

## 8. Observações

- **Divergência corrigida em 2026-11-16:** o §1 mostrava último commit `ff60748` e push 03:05 UTC; o Git/GitHub confirmam `9bc62d1` em `phase/01-nucleo-sem-ia`, push às 06:44 UTC (CI verde, run 43567810203). Corrigido; nenhum outro campo divergia.
- **MCP do GitHub:** indisponível nesta sessão; operações de consulta (PRs e CI) feitas com `gh` CLI autenticado. Git local segue como via de commits/push.
- Variáveis de ambiente novas desde a última sessão: `TEST_DATABASE_URL` (opcional; default deriva de `DATABASE_URL` + `_test`), documentada no `.env.example` e no README.
- **Divergência registrada (F1-T01):** o `PLANO.md` §5.1 prevê `years` em `candidate_skills`; a decisão de 2026-11-16 também alocou `years` em `candidate_experiences`. As duas colunas existem com CHECK `>= 0`; confirmar a duplicidade semântica antes da F1-T02.

---

## 9. Checklist de encerramento de sessão (conferir antes de parar)

- [ ] Testes verdes **ou** falhas isoladas e listadas em §5
- [ ] Tudo commitado (`chore(wip)` se incompleto)
- [ ] Push feito e **verificado** (`git status -sb` sem `ahead`; branch visível no GitHub)
- [ ] Campos de sincronização da §1 atualizados (remoto, último push, PR aberto, CI no GitHub)
- [ ] §1 e §3 atualizados com a próxima ação exata
- [ ] `BACKLOG.md` marcado
- [ ] Ficha da tarefa atual atualizada (se existir)
- [ ] `RELATORIO.md` com nota curta da tarefa (se concluída)
- [ ] `.env.example` sincronizado (se houve nova variável)
- [ ] `uv.lock` commitado junto com o `pyproject.toml` (se houve mudança de dependência)