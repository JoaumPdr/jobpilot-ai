# JobPilot AI — STATUS (estado vivo)

> Vira `docs/STATUS.md`. **Atualizar ao final de toda sessão** (e após cada tarefa concluída).
> Objetivo: qualquer agente ou pessoa retoma o trabalho em menos de 2 minutos lendo só este arquivo.
> Só o Orquestrador (ou o agente único) edita este arquivo.

---

## 1. Retomada rápida

| Campo | Valor |
|-------|-------|
| **Última atualização** | 2026-11-13 23:00 (UTC) |
| **Fase atual** | Fase 0 — Fundação |
| **Branch da fase** | `phase/00-fundacao` |
| **Tarefa atual** | F0-T05 — SQLAlchemy + Alembic: conexão, sessão, migração inicial |
| **Branch da tarefa** | `phase/00-fundacao` |
| **Estado da tarefa** | não iniciada |
| **Último commit** | `41c87f6` — feat(api): esqueleto FastAPI com /health, logging estruturado e tratamento de erros (F0-T04) |
| **Testes** | verdes (4 passed) |
| **CI** | não configurado |
| **Repositório remoto** | `https://github.com/JoaumPdr/jobpilot-ai` |
| **Sincronização com o remoto** | em dia |
| **Último push** | 2026-11-13 23:00 (UTC) — branch `phase/00-fundacao` |
| **PR aberto** | nenhum |
| **Última tag publicada** | nenhuma |
| **MCP do GitHub** | indisponível (usando git local) |

### Próxima ação exata (uma frase, imperativa)

> Adicionar `sqlalchemy` e `alembic` ao projeto, criar `app/models/` e `app/repositories/`, configurar sessão por requisição, gerar migração inicial e decidir tipo de ID (int vs UUID) em ADR.

---

## 2. O que foi feito na última sessão

- F0-T01 concluída: repositório GitHub criado, branches enviadas, estrutura de docs e arquivos base commitados.
- F0-T02 concluída: ambiente Python configurado com `uv`, dependências de dev, pre-commit, teste de sanidade e ADR 0008.
- F0-T03 concluída: `docker-compose.yml` com PostgreSQL 16 criado, `.env.example` atualizado, dependências `pydantic-settings` e `psycopg[binary]` adicionadas, módulo `app.core.config` implementado com validação de ambiente via Pydantic.
- F0-T04 concluída: `app/main.py` com FastAPI, middleware `request_id`, handler global de exceções; `app/api/routes/health.py` com `GET /health`; `app/core/logging.py` com structlog JSON; `tests/api/test_health.py` com 3 testes de API. 4 testes passando, lint limpo.

---

## 3. O que falta na tarefa atual (lista concreta)

- [ ] Adicionar `sqlalchemy` e `alembic` como dependências de produção via `uv add`
- [ ] Criar `app/models/base.py` e `app/repositories/` base
- [ ] Configurar sessão SQLAlchemy por requisição (middleware ou dependency)
- [ ] Gerar migração inicial com Alembic (`alembic init migrations`, `alembic revision --autogenerate`)
- [ ] Decidir tipo de ID (int vs UUID) e registrar ADR
- [ ] Criar teste de integração conectando no banco (upgrade/downgrade)

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