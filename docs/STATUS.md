# JobPilot AI — STATUS (estado vivo)

> Vira `docs/STATUS.md`. **Atualizar ao final de toda sessão** (e após cada tarefa concluída).
> Objetivo: qualquer agente ou pessoa retoma o trabalho em menos de 2 minutos lendo só este arquivo.
> Só o Orquestrador (ou o agente único) edita este arquivo.

---

## 1. Retomada rápida

| Campo | Valor |
|-------|-------|
| **Última atualização** | AAAA-MM-DD HH:MM (UTC) |
| **Fase atual** | Fase 0 — Fundação |
| **Branch da fase** | `phase/00-fundacao` |
| **Tarefa atual** | F0-T01 — Criar repositório e estrutura de docs |
| **Branch da tarefa** | `feat/f0-t01-repositorio-e-docs` |
| **Estado da tarefa** | não iniciada · em andamento · bloqueada · concluída |
| **Último commit** | `<hash curto> — <mensagem>` |
| **Testes** | verdes · vermelhos (detalhar em §5) |
| **CI** | verde · vermelho · não configurado |
| **Repositório remoto** | `https://github.com/<usuário>/jobpilot-ai` (preencher na F0-T01) |
| **Sincronização com o remoto** | em dia · à frente N commits · atrás N commits · divergente |
| **Último push** | AAAA-MM-DD HH:MM (UTC) — branch `<nome>` |
| **PR aberto** | nenhum · #N tarefa → fase (link) |
| **Última tag publicada** | ex.: `fase-00` · nenhuma |
| **MCP do GitHub** | funcionando · sem permissão · indisponível (usando git local) |

### Próxima ação exata (uma frase, imperativa)

> Ex.: "Abrir `app/services/job_service.py` e implementar `normalize_work_mode()` conforme critério 2 de F1-T04; teste já escrito em `tests/unit/test_normalization.py` (falhando)."

---

## 2. O que foi feito na última sessão

- ...

## 3. O que falta na tarefa atual (lista concreta)

- [ ] ...
- [ ] ...

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
| — | — | — | — |

---

## 7. Perguntas pendentes para o JP

- [ ] ...

---

## 8. Observações

- Divergências entre este arquivo e o estado do Git (se houver): ...
- Variáveis de ambiente novas desde a última sessão: ...

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
