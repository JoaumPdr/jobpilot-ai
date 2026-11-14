# JobPilot AI — STATUS (estado vivo)

> Vira `docs/STATUS.md`. **Atualizar ao final de toda sessão** (e após cada tarefa concluída).
> Objetivo: qualquer agente ou pessoa retoma o trabalho em menos de 2 minutos lendo só este arquivo.
> Só o Orquestrador (ou o agente único) edita este arquivo.

---

## 1. Retomada rápida

| Campo | Valor |
|-------|-------|
| **Última atualização** | 2026-11-14 01:05 (UTC) |
| **Fase atual** | Fase 0 — Fundação |
| **Branch da fase** | `phase/00-fundacao` |
| **Tarefa atual** | F0-GATE — Gate da fase (PR phase/00 → develop, tag fase-00 publicada) |
| **Branch da tarefa** | `phase/00-fundacao` |
| **Estado da tarefa** | em andamento |
| **Último commit** | `e9b5a54` — fix(ci): remover project.scripts inexistente que quebra build do uv_build |
| **Testes** | verdes (4 passed) |
| **CI** | workflow em .github/workflows/ci.yml; erro do build corrigido (project.scripts removido) — aguardando execucao no GitHub via PR |
| **Repositório remoto** | `https://github.com/JoaumPdr/jobpilot-ai` |
| **Sincronização com o remoto** | em dia |
| **Último push** | 2026-11-14 01:00 (UTC) — branch `phase/00-fundacao` + tag `fase-00` |
| **PR aberto** | nenhum |
| **Última tag publicada** | nenhuma |
| **MCP do GitHub** | indisponível (usando git local) |

### Próxima ação exata (uma frase, imperativa)

> Criar `.github/workflows/ci.yml` com `uv sync --locked`, ruff, pytest com PostgreSQL service, teste de migração Alembic.

---

## 2. O que foi feito na última sessão

- F0-T01 concluída: repositório GitHub criado, branches enviadas, estrutura de docs e arquivos base commitados.
- F0-T02 concluída: ambiente Python configurado com `uv`, dependências de dev, pre-commit, teste de sanidade e ADR 0008.
- F0-T03 concluída: `docker-compose.yml` com PostgreSQL 16 (porta 5433 no host devido a conflito com Docker Desktop backend na 5432), `.env.example` e `alembic.ini` atualizados para porta 5433, `app/core/config.py` com validação de ambiente, `app/api/routes/health.py` com conversão de URL SQLAlchemy para psycopg v3. Verificado com banco real: container saudável, `alembic upgrade head` + `downgrade -1` funcionam, `/health` retorna 200 com database.status = healthy.
- F0-T04 concluída: `app/main.py` com FastAPI, middleware `request_id`, handler global de exceções; `app/api/routes/health.py` com `GET /health`; `app/core/logging.py` com structlog JSON; `tests/api/test_health.py` com 3 testes de API. 4 testes passando, lint limpo.
- F0-T05 concluída: `app/models/base.py` com Base declarativa (UUID, __tablename__ automático), `app/core/database.py` com engine/SessionLocal/get_db, Alembic inicializado, ADR 0010 (UUID) registrado.
- F0-T06 concluída: `.github/workflows/ci.yml` com `uv sync --locked`, ruff, pytest com serviço PostgreSQL, teste de migração Alembic.
- F0-T07 concluída: ADRs 0001–0007 e 0009 criados (total de 10 ADRs incluindo 0008 e 0010), `docs/privacy-and-sources.md` criado, README revisado e completo conforme GUIA_DOCS_E_GIT.md.

---

## 3. O que falta na tarefa atual (lista concreta)

- [ ] Abrir PR `phase/00-fundacao` → `develop` pelo MCP do GitHub (ou via VS Code)
- [ ] Conferir CI verde no GitHub antes de mesclar
- [x] Tag `fase-00` publicada no remoto ✅
- [ ] Adicionar seção da Fase 0 no `RELATORIO.md`

---

## 4. Progresso por fase

| Fase | Estado | Tag | Gate |
|------|--------|-----|------|
| 0 — Fundação | em andamento | — | — |
| 1 — Núcleo sem IA | não iniciada | — | — |
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
| — | — | — | — | — |

*(Testes vermelhos ou `xfail` ativos devem ser listados aqui com o motivo.)*

---

## 6. Decisões tomadas (resumo; detalhe em ADR quando relevante)

| Data | Decisão | Motivo | ADR |
|------|---------|--------|-----|
| 2026-11-10 | Repositório GitHub: `JoaumPdr/jobpilot-ai` privado | Nome sugerido no PLANO.md, conta do JP | — |
| 2026-11-10 | Branch strategy: `main` → `develop` → `phase/*` | Modularidade, resiliência, gates por fase | 0009 (sincronização GitHub) |
| 2026-11-13 | Gerenciador de dependências: `uv` | Performance, lock file, grupos de dependências | 0008 |

---

## 7. Perguntas pendentes para o JP

- [ ] Confirmar se deseja configurar proteção de branch no GitHub (requer plano pago ou settings de admin) ou seguir por disciplina registrada no STATUS.md

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