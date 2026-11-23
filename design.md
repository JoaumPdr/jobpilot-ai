# JobPilot AI — Design Document

> Documento vivo. Atualizado quando a arquitetura ou um fluxo mudam.
> Fonte da verdade para decisões arquiteturais (ADRs em `docs/adr/`).

---

## 1. Visão Geral

JobPilot AI é um assistente pessoal para buscar, analisar e gerir candidaturas a vagas.
Arquitetura: **monólito modular** em Python 3.12+, FastAPI, PostgreSQL, SQLAlchemy 2.x, Alembic, Pydantic v2, LangGraph.

**Princípios centrais:**
- O sistema recomenda e prepara; o usuário revisa e decide.
- Zero automação de envio de candidatura.
- Zero invenção de fatos no currículo.
- LLM como explicador, não como juiz — matching determinístico primeiro.

---

## 2. Camadas e Dependências

```
┌────────────────────────────────────────────┐
│  API (FastAPI routes) / UI (Streamlit)     │  ← entrada/saída, sem regra de negócio
└──────────────────────┬─────────────────────┘
                       │ chama
┌──────────────────────▼─────────────────────┐
│  Serviços (regras de negócio)              │  ← onde a lógica vive
│  profile / job / matching / application…   │
└───────┬────────────────────────┬───────────┘
        │                        │
┌───────▼─────────┐    ┌─────────▼─────────────┐
│ Repositórios    │    │ Provedores externos   │
│ (SQLAlchemy)    │    │ LLM / embeddings /    │
└───────┬─────────┘    │ coletores (interfaces)│
        │              └───────────────────────┘
┌───────▼────────┐
│ PostgreSQL     │
└────────────────┘
```

**Regras invioláveis:**
- Rotas não acessam repositórios diretamente.
- Serviços não importam FastAPI.
- Nós do LangGraph reutilizam serviços — **nunca reimplementam** lógica.
- Provedores externos ficam atrás de **interfaces**; testes usam implementações falsas.

---

## 3. Decisões Arquiteturais (ADRs)

| ADR | Título | Status |
|-----|--------|--------|
| 0001 | Monólito modular em Python | aceito |
| 0002 | FastAPI + SQLAlchemy 2.x + Alembic + Pydantic v2 | aceito |
| 0003 | PostgreSQL como único datastore (JSONB para análises) | aceito |
| 0004 | LangGraph como único framework de orquestração | aceito |
| 0005 | LLM atrás de interface `LLMProvider` | aceito |
| 0006 | Matching determinístico primeiro; embeddings só se golden set provar ganho | aceito |
| 0007 | Single-user no MVP; `candidate_id` mantido nas tabelas | aceito |
| 0008 | `uv` como único gerenciador de ambiente e dependências | aceito |
| 0009 | GitHub como remoto e fonte da verdade (MCP + git local) | aceito |
| [0011](docs/adr/0011-distribuicao-local-docker-compose.md) | Distribuição local da v1.0.0 com Docker Compose | aceito |

---

## 4. Modelo de Dados (Resumo)

Ver `docs/data-model.md` para detalhes completos.

**Fase 1:**
- `candidates`, `candidate_preferences`, `skills`, `candidate_skills`, `candidate_experiences`
- `import_batches`, `jobs`
- `applications`, `application_status_history`

**Fase 2:**
- `job_skills`, `job_matches`

**Fase 3:**
- `llm_cache`

**Fase 4:**
- `pipeline_runs`

**Fase 5:**
- `resume_versions`

**Fase 6:**
- `interviews`

---

## 5. Fluxos Principais

### 5.1 Importação de Vagas (CSV/Manual)
1. Recebe arquivo/entrada → valida linha a linha
2. Normaliza (texto, modalidade, senioridade, URL, fingerprint)
3. Deduplicação em 4 camadas (ID externo → URL canônica → fingerprint → similaridade)
4. Salva no banco com `import_batch_id` para rastreabilidade
5. Retorna relatório por linha (inseridas, duplicadas, rejeitadas, erros)

### 5.2 Matching Determinístico
1. Extrai requisitos da vaga (taxonomia de skills + aliases PT/EN)
2. Aplica filtros eliminatórios de modalidade, localização, empresas excluídas
   e habilidades obrigatórias excluídas. `JobService.evaluate_knockouts`
   carrega os requisitos quando a regra de habilidades está ativa e devolve
   flags com código e valor encontrado na vaga.
3. Calcula o score ponderado só para vagas elegíveis pela etapa anterior:
   `Σ(peso_i × correspondência_i) / Σ(peso_i)`
4. Níveis: exata=1.0, alias/relacionada=0.7, ausente=0, não confirmada=fora do cálculo
5. Retorna: atendidos, ausentes, não confirmados, evidências
6. Versionado via `scoring_version`

### 5.3 Pipeline Orquestrado (LangGraph)
Estado tipado → Nós determinísticos (importar, normalizar, dedup, filtrar, match) → Nós LLM (top-N) → Persistência (`pipeline_runs`) → Aprovação humana antes de ações sensíveis.

---

## 6. Segurança e Privacidade

- Segredos só em `.env` (nunca versionado); `.env.example` sem valores reais.
- **Nunca logar** texto de currículo ou dados pessoais (PII).
- Minimizar dados enviados a LLM; descrever vaga como *dado delimitado*.
- Documentação LGPD em `docs/privacy-and-sources.md`.
- Varredura de segredos no pre-commit e pre-push.

---

## 7. Observabilidade

- Logs estruturados JSON com `request_id` (API) e `run_id` (pipeline).
- Métricas de LLM: tokens, custo estimado, latência, cache hits.
- Migrações Alembic reversíveis e testadas (upgrade + downgrade).
