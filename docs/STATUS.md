# JobPilot AI — STATUS (estado vivo)

> Vira `docs/STATUS.md`. **Atualizar ao final de toda sessão** (e após cada tarefa concluída).
> Objetivo: qualquer agente ou pessoa retoma o trabalho em menos de 2 minutos lendo só este arquivo.
> Só o Orquestrador (ou o agente único) edita este arquivo.

---

## 1. Retomada rápida

| Campo | Valor |
|-------|-------|
| **Última atualização** | 2026-11-17 (UTC) |
| **Fase atual** | Fase 1 — Núcleo sem IA (**em andamento: F1-T01, F1-T02-a, F1-T02-b, F1-T03 e F1-T04 concluídas e integradas; próxima: F1-T05**) |
| **Branch da fase** | `phase/01-nucleo-sem-ia` (criada a partir de `develop` e publicada) |
| **Tarefa atual** | F1-T05 — Cadastro manual de vaga (serviço + rota, usando normalização e dedup) |
| **Ficha da tarefa** | `docs/tasks/FASE-01/F1-T05.md` (a criar ao iniciar) |
| **Branch da tarefa** | `feat/f1-t05-cadastro-manual` (a criar a partir da fase) |
| **Estado da tarefa** | não iniciada — ficha e branch a criar |
| **Último commit** | `396e851` — Merge pull request #12 (F1-T04) |
| **Testes** | verdes (184 passed no merge da F1-T04) |
| **CI** | verde no merge do PR #12 na `phase/01-nucleo-sem-ia` (run `44191309228`) |
| **Repositório remoto** | `https://github.com/JoaumPdr/jobpilot-ai` |
| **Sincronização com o remoto** | em dia |
| **Último push** | 2026-11-17 22:34 (UTC) — merge do PR #12 na `phase/01-nucleo-sem-ia` |
| **PR aberto** | nenhum após a integração do PR #12 |
| **Última tag publicada** | `fase-00` → aponta para `cbbeb65` (tag anotada `28f5be7`, merge commit em `develop`, CI verde) |
| **MCP do GitHub** | indisponível; `gh` CLI autenticado usado como alternativa (PRs e CI consultados) |

### Próxima ação exata (uma frase, imperativa)

> Criar a ficha `docs/tasks/FASE-01/F1-T05.md` e a branch `feat/f1-t05-cadastro-manual` a partir da fase, e implementar o serviço e a rota de cadastro manual de vaga usando normalização, `canonical_url`/fingerprint e aviso de duplicata.

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
- **F1-T02 dividida (2026-11-16):** decisões do JP — rotas REST por `candidate_id`, JSONB estruturado validado por Pydantic, `POST /skills` permitido (na `-b`) e divisão em `F1-T02-a` (candidato + preferências + erros + `api.md`) e `F1-T02-b` (habilidades + experiências). Divisão registrada no `BACKLOG.md`.
- **F1-T02-a implementada (2026-11-16):** schemas com `education`/`languages` estruturados, exceções de domínio com handlers 404/409/422 e `request_id`, repositórios, serviço (e-mail único, upsert 1:1) e rotas REST de candidato/preferências. Fixtures de banco movidas para `tests/conftest.py` com cliente de API; 18 testes de API, 31 unitários, `docs/api.md` e `email-validator`. Suíte: 70 passed. **PR #9 integrado por merge commit (`359fbfa`) com CI verde.**
- **F1-T02-b implementada (2026-11-17):** a sessão retomou com o trabalho já escrito e não commitado (13 arquivos novos + 7 modificados). Revisão do diff, suíte completa contra PostgreSQL real (**119 passed**), lint e formatação limpos. Commits `d6513a6` (código + testes) e `eb7481d` (`docs/api.md`, BACKLOG e ficha); branch publicada e **PR #10 aberto** com CI verde (run `44187596274`). Escopo entregue: catálogo com busca `q`, `POST /skills`, vínculo por `skill_id`/`canonical_name`, `PATCH`/`DELETE` do vínculo, CRUD de experiências, `InvalidDataError` (422) para faixa de datas no `PATCH`, `CandidateRead` com `skills`/`experiences` e `selectinload` contra N+1.
- **Ambiente da sessão (2026-11-17):** Docker Desktop estava desligado, o que gerou 63 erros de conexão na primeira execução dos testes (falso vermelho). Subido o container `jobpilot-postgres` via `docker compose up -d`; suíte completa ficou verde.
- **F1-T02-b integrada (2026-11-17):** STATUS registrado em `eca1e4b`, branch sincronizada e **PR #10 mesclado** em `phase/01-nucleo-sem-ia` (merge commit `4136bf2`) com CI verde (run `44188162643`). `phase/01-nucleo-sem-ia` atualizada localmente por fast-forward; `feat/f1-t02b-skills-experiencias` preservada no remoto.
- **F1-T03 implementada e integrada (2026-11-17):** modelos `Job`/`ImportBatch` com enums (`WorkMode`, `Seniority`, `ImportKind`), migração `000000000003` reversível (upgrade → downgrade → upgrade testados), índice único parcial `(source, external_id)`, índices de `fingerprint`/`canonical_url`, FKs com `SET NULL`, CHECKs de salário/contadores; 19 testes de constraint novos; suíte **138 passed**. Commit `11ffb68`, **PR #11 mesclado** (`b837c3d`) com CI verde (run `44189183645`); `data-model.md`, BACKLOG e ficha atualizados.
- **F1-T04 implementada e integrada (2026-11-17):** funções puras em `app/services/normalization.py` (`clean_text`, `comparison_text`, `normalize_work_mode`, `normalize_seniority`, `canonicalize_url`, `job_fingerprint`), 46 testes unitários sem banco, suíte **184 passed**. Commit `3cfd4fb`, **PR #12 mesclado** (`396e851`) com CI verde (run `44191309228`); BACKLOG e ficha atualizados.
- **Sessão encerrada (2026-11-17):** 4 tarefas fechadas ou integradas (fechamento da F1-T02-b, F1-T03, F1-T04 e registros de STATUS), 3 PRs mesclados (#10, #11, #12) e 2 commits de documentação na fase. Ponto de retomada: F1-T05.

---

## 3. O que falta na tarefa atual (lista concreta)

**Tarefa atual:** F1-T05 — cadastro manual de vaga · **não iniciada**.
**Planejamento detalhado:** `docs/tasks/FASE-01/F1-T05.md` (a criar). Critérios de aceitação canônicos: `docs/BACKLOG.md` → F1-T05.

- [x] Base da Fase 0 e higiene mescladas (`cbbeb65`, `ff60748`) ✅
- [x] Criar `phase/01-nucleo-sem-ia` a partir de `develop` e publicar ✅
- [x] Padronizar documentação (BACKLOG/STATUS/fichas) — PR #7 mesclado ✅
- [x] F1-T01 concluída: modelos, migração, testes de constraint e `data-model.md` (PR #8) ✅
- [x] F1-T02 dividida em `-a`/`-b` e decisões confirmadas (REST, JSONB, `POST /skills` na `-b`) ✅
- [x] F1-T02-a concluída: candidato/preferências, erros padronizados, testes e `api.md` (PR #9) ✅
- [x] F1-T02-b concluída e integrada: habilidades e experiências (PR #10) ✅
- [x] F1-T03 concluída e integrada: modelos e migração de `jobs`/`import_batches` (PR #11) ✅
- [x] F1-T04 concluída e integrada: normalização e canonização (PR #12) ✅
- [ ] Criar ficha `F1-T05.md` e branch `feat/f1-t05-cadastro-manual`
- [ ] Schema/repositório/serviço de vaga manual (normaliza, calcula URL canônica/fingerprint)
- [ ] Rota REST de cadastro manual e detecção de duplicata certa/provável com aviso claro
- [ ] Testes unitários e de API; `docs/api.md` atualizado
- [ ] PR tarefa → fase, CI verde e merge (com autorização)

### Itens fora do escopo da Fase 0 (resolvido)

- ~~`skills-lock.json` modificado e `.agents/skills/git-create-repo/` não versionado~~ → skill de terceiros ignorado no `.gitignore` e lock restaurado ao estado versionado (decisão registrada na seção 6).

---

## 4. Progresso por fase

| Fase | Estado | Tag | Gate |
|------|--------|-----|------|
| 0 — Fundação | concluída | `fase-00` (`cbbeb65`) | ✅ PR #4 mesclado com CI verde |
| 1 — Núcleo sem IA | em andamento (F1-T01, F1-T02-a, F1-T02-b, F1-T03 e F1-T04 concluídas; próxima: F1-T05) | — | — |
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
| 2026-11-17 | dívida | `skills.canonical_name` é único case-sensitive no banco; a API compara em minúsculas, mas concorrência ainda pode criar variações de caixa | F2-T01 | aberto |
| 2026-11-17 | dívida | `CandidateRepository.get` carrega preferências, skills e experiências em toda leitura de candidato; separar consultas se virar gargalo | F1-T03+ | aberto |

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
| 2026-11-17 | `PATCH` de experiência revalida a faixa de datas combinando estado atual + payload e responde `422 invalid_data` (novo `InvalidDataError`) | a regra depende do estado gravado, não só do payload; separar `validation_error` (schema) de `invalid_data` (consistência) deixa o erro diagnosticável | — |
| 2026-11-17 | Vínculo por `canonical_name` cria a habilidade no catálogo quando ela não existe | permite registrar habilidades sem um passo prévio de curadoria; a duplicidade é fechada pela comparação case-insensitive na API | — |

---

## 7. Perguntas pendentes para o JP

- [ ] Confirmar se deseja configurar proteção de branch no GitHub (requer plano pago ou settings de admin) ou seguir por disciplina registrada no STATUS.md
- [ ] Decidir se `phase/00-fundacao` deve ser apagada após o gate (hoje preservada no remoto)

---

## 8. Observações

- **Docker Desktop encerrou sozinho durante a sessão (2026-11-17):** a segunda execução completa de testes gerou 82 erros de conexão; o container `jobpilot-postgres` foi reiniciado (`docker compose up -d`) e a suíte voltou a verde (184 passed). Nenhuma falha de código.
- **Divergência corrigida em 2026-11-17:** o §1 dizia "F1-T02-b não iniciada; ficha a criar", mas o Git já tinha a ficha (`186b575`), a branch publicada e ~1.900 linhas de implementação não commitadas. Confiado o Git; STATUS corrigido e o trabalho revisado, testado e commitado (`d6513a6`, `eb7481d`). Nenhum outro campo divergia do remoto.
- **Divergência corrigida em 2026-11-16:** o §1 mostrava último commit `ff60748` e push 03:05 UTC; o Git/GitHub confirmam `9bc62d1` em `phase/01-nucleo-sem-ia`, push às 06:44 UTC (CI verde, run 43567810203). Corrigido; nenhum outro campo divergia.
- **MCP do GitHub:** indisponível nesta sessão; operações de consulta (PRs e CI) feitas com `gh` CLI autenticado. Git local segue como via de commits/push.
- Variáveis de ambiente novas desde a última sessão: `TEST_DATABASE_URL` (opcional; default deriva de `DATABASE_URL` + `_test`), documentada no `.env.example` e no README.
- **Divergência registrada (F1-T01):** o `PLANO.md` §5.1 prevê `years` em `candidate_skills`; a decisão de 2026-11-16 também alocou `years` em `candidate_experiences`. As duas colunas existem com CHECK `>= 0`; confirmar a duplicidade semântica antes da F1-T02.

---

## 9. Checklist de encerramento de sessão (conferir antes de parar)

- [x] Testes verdes **ou** falhas isoladas e listadas em §5
- [x] Tudo commitado (`chore(wip)` se incompleto)
- [x] Push feito e **verificado** (`git status -sb` sem `ahead`; branch visível no GitHub)
- [x] Campos de sincronização da §1 atualizados (remoto, último push, PR aberto, CI no GitHub)
- [x] §1 e §3 atualizados com a próxima ação exata
- [x] `BACKLOG.md` marcado
- [x] Ficha da tarefa atual atualizada (se existir)
- [x] `RELATORIO.md` com nota curta da tarefa (se concluída) — a seção da Fase 1 será preenchida no gate da fase
- [x] `.env.example` sincronizado (se houve nova variável) — nenhuma variável nova
- [x] `uv.lock` commitado junto com o `pyproject.toml` (se houve mudança de dependência) — nenhuma dependência nova