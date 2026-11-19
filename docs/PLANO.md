# JobPilot AI — Análise e Plano de Desenvolvimento

> **Versão:** 1.0 · **Idioma:** PT-BR · **Público:** desenvolvedor (JP) e agentes de execução (Alethe)
> Este é o documento-mestre. Os demais arquivos do pacote:
> `02_Instrucoes_Alethe` (como executar) · `03_Documentacao_e_Git` (docs, branches, commits) · `04_Backlog_e_Tasks` (tarefas por fase) · `05_STATUS_template` (estado vivo do projeto).

---

## 1. Análise do plano original

### 1.1 Pontos fortes (manter)

- **Princípio central claro:** o sistema recomenda e prepara; o usuário decide. Nada de envio automático e nada de inventar experiência.
- **Custo sob controle:** filtrar com Python/SQL antes de gastar tokens com LLM.
- **LLM como explicador, não como juiz:** a metodologia é determinística; o LLM interpreta e justifica.
- **Fontes de vagas realistas:** APIs oficiais, feeds, CSV e entrada manual; sem scraping agressivo.
- **Orquestração incremental:** LangGraph + funções Python, sem misturar frameworks no MVP.
- **Qualidade como requisito:** testes, logs, `.env.example`, respostas de LLM tratadas como dados não confiáveis.

### 1.2 Ambiguidades e lacunas encontradas

| # | Ponto | Problema | Decisão proposta |
|---|-------|----------|------------------|
| D-01 | Usuário único ou múltiplos? | A tabela `candidates` sugere multiusuário, mas não há autenticação no plano. | **MVP single-user local.** Manter `candidate_id` em todas as tabelas (pronto para multiusuário) e **adiar autenticação** para pós-v1.0. |
| D-02 | Onde fica o LLM no roteiro? | O plano põe análise LLM junto de matching/orquestração, e o critério 7 do MVP exige análise validada. | **Criar fase própria para a camada LLM** (Fase 3), com abstração de provedor, cache e avaliação, antes do LangGraph. |
| D-03 | Deduplicação | Só há unicidade `(source, external_id)`, que não cobre CSV/manual sem ID. | **Deduplicação em camadas** (ver §6.3): ID externo → URL canônica → fingerprint → similaridade (apenas sinaliza, nunca apaga). |
| D-04 | Idioma das vagas | Vagas e currículo podem estar em PT-BR e EN. | Taxonomia de skills com **aliases PT/EN**; se usar embeddings, **modelo multilíngue**. |
| D-05 | Extração de requisitos | Não define como extrair antes do LLM. | **Extrator determinístico baseado em taxonomia primeiro**; LLM só para ambiguidades. |
| D-06 | Score vs. eliminatórios | Um requisito eliminatório (ex.: "obrigatório inglês fluente") pode ser diluído numa média. | **Separar:** filtros eliminatórios (flags) ≠ score ponderado. |
| D-07 | Histórico de status | Aparece só em "extensões futuras", mas é essencial para as métricas de funil. | **Incluir `application_status_history` já na Fase 1** (custo baixo, valor alto). |
| D-08 | Reprodutibilidade do score | Mudar pesos altera resultados antigos sem rastro. | **`scoring_version`** em cada match; pesos em arquivo de configuração versionado. |
| D-09 | Privacidade | Currículo contém dados pessoais e pode ir para API externa. | Minimizar dados enviados, **nunca logar texto de currículo**, permitir modelo local, documentar (LGPD). |
| D-10 | Prompt injection | Descrições de vaga são texto externo não confiável. | Delimitar como **dado**, nunca como instrução; validar saída com Pydantic (ver §10). |
| D-11 | UI no MVP | Sem UI, o uso depende de API. | Interface do MVP = **Swagger/OpenAPI** do FastAPI. Streamlit na Fase 6. |
| D-12 | Resiliência a falta de tokens | Não era requisito explícito. | **Requisito de projeto:** estado externo em arquivos (`STATUS.md`, tasks), tarefas pequenas, commits frequentes (ver arquivo 02). |

### 1.3 Melhorias propostas (resumo)

1. **Fase 0 de fundação** (repo, CI, docs-base, Docker) separada, para que as fases seguintes partam de base estável.
2. **Camada LLM isolada** com interface de provedor, provedor falso para testes, cache, orçamento e registro de custo.
3. **Golden set de avaliação** (30+ vagas rotuladas) criado cedo (Fase 2) e reutilizado nas Fases 3 e 4.
4. **Anti-invenção no currículo por construção:** toda sugestão referencia o trecho original; validador determinístico bloqueia fatos novos.
5. **Auditoria de execução:** `pipeline_runs` com `run_id`, contadores e erros; idempotência para retomar após falha.
6. **Import em lotes rastreáveis** (`import_batches`) com erros por linha sem derrubar o lote inteiro.
7. **Gates de saída por fase** (checklist objetivo) — a fase só fecha quando o gate passa.
8. **Planejamento just-in-time:** tarefas detalhadas do backlog são criadas quando a fase começa, evitando documentos desatualizados.

---

## 2. Escopo

### 2.1 MVP (Fases 0–4) — versão `v0.1.0`

Perfil, importação de vagas (CSV/manual), deduplicação, filtros, gestão de candidaturas, matching explicável, análise LLM validada, pipeline LangGraph com logs e erros, testes das regras centrais, README completo.

### 2.2 Pós-MVP (Fases 5–7) — versão `v1.0.0`

Assistente de currículo com aprovação humana, dashboard Streamlit e analytics, hardening e primeiro coletor autorizado opcional.

A primeira distribuição da `v1.0.0` será local e reproduzível. O pacote Docker Compose coordenará a API FastAPI, a interface Streamlit acessível no navegador e o PostgreSQL com armazenamento persistente. A instalação em uma máquina limpa será validada por uma terceira pessoa seguindo a documentação de configuração inicial, execução, backup e restauração. No Windows, o Docker Desktop poderá ser um pré-requisito. O uso do terminal e a edição do `.env` serão suficientes para configurar e iniciar a distribuição, sem instalação de Python, `uv` ou PostgreSQL no host. [ADR 0011](adr/0011-distribuicao-local-docker-compose.md)

### 2.3 Fora de escopo (decisões explícitas)

- Envio automático de candidaturas.
- Scraping que contorne login, CAPTCHA ou proteções.
- Autenticação e multiusuário.
- Múltiplos frameworks de orquestração (CrewAI etc.).
- UI em React.
- Probabilidade de contratação — o score é **compatibilidade explicável**, nunca chance de ser contratado.

**Possíveis melhorias para a `v1.1.0`, sujeitas a planejamento próprio.** Instalador gráfico para Windows, executável independente, assistente visual de configuração, atalho que gerencia a inicialização dos serviços, atualizador automático, backup pela interface e diagnóstico visual avançado.

---

## 3. Requisitos

### 3.1 Funcionais (RF)

| ID | Requisito | Fase |
|----|-----------|------|
| RF-01 | Cadastrar e editar perfil (dados, currículo em texto, skills, experiências, formação, idiomas). | 1 |
| RF-02 | Definir preferências: cargos, localização, modalidade, senioridade, filtros eliminatórios. | 1 |
| RF-03 | Importar vagas por CSV e por inclusão manual, com validação e relatório de erros por linha. | 1 |
| RF-04 | Deduplicar vagas em camadas, com revisão humana para casos duvidosos. | 1 |
| RF-05 | Listar/filtrar vagas por texto, modalidade, localização, senioridade, fonte, data e status. | 1 |
| RF-06 | Gerir candidaturas com máquina de estados e histórico de mudanças. | 1 |
| RF-07 | Extrair requisitos obrigatórios/desejáveis das vagas. | 2 |
| RF-08 | Calcular score explicável (atendidos, ausentes, não confirmados, evidências). | 2 |
| RF-09 | Aplicar filtros eliminatórios separadamente do score. | 2 |
| RF-10 | Gerar análise LLM estruturada e validada para vagas selecionadas. | 3 |
| RF-11 | Executar pipeline orquestrado (importar → normalizar → deduplicar → filtrar → match → analisar). | 4 |
| RF-12 | Sugerir adaptações de currículo com evidência e aprovação humana. | 5 |
| RF-13 | Exibir dashboard e métricas de funil. | 6 |

### 3.2 Não funcionais (RNF)

| ID | Requisito |
|----|-----------|
| RNF-01 | Python 3.12+, tipagem estática em todo o código novo, lint com Ruff. |
| RNF-02 | Camadas separadas: API → serviços → repositórios → modelos; agentes/nós só chamam serviços. |
| RNF-03 | Cobertura mínima: **≥ 85%** em serviços/regras de domínio, **≥ 70%** global. |
| RNF-04 | Testes de regras determinísticas não dependem de rede nem de LLM. |
| RNF-05 | Segredos só em `.env`; `.env.example` sem valores reais; nada sensível em logs. |
| RNF-06 | Logs estruturados (JSON) com `run_id`/`request_id`. |
| RNF-07 | Migrações Alembic reversíveis e testadas (upgrade + downgrade). |
| RNF-08 | Datas em UTC; importações idempotentes (reimportar o mesmo CSV não cria duplicatas). |
| RNF-09 | Desempenho de referência: listagem paginada < 500 ms com 10 mil vagas; importar 5 mil linhas em < 30 s. |
| RNF-10 | Toda decisão arquitetural relevante registrada em ADR. |
| RNF-11 | Documentação e commits em PT-BR; comentários didáticos explicando o "porquê". |
| RNF-13 | Sincronização contínua com o GitHub: push após cada commit significativo, nenhuma sessão termina com commits locais não enviados, PRs com CI verde antes de mesclar, tags de fase e de release publicadas no remoto. |
| RNF-12 | Ambiente reproduzível com `uv`: instalação do zero com `uv sync`, `uv.lock` sempre versionado e sincronizado com o `pyproject.toml`; CI instala com o lock travado; comandos do projeto executados via `uv run`. |

---

## 4. Arquitetura

### 4.1 Camadas e regra de dependência

```
        ┌────────────────────────────────────────────┐
        │  API (FastAPI routes)  /  UI (Streamlit)   │   ← entrada/saída, sem regra de negócio
        └──────────────────────┬─────────────────────┘
                               │ chama
        ┌──────────────────────▼─────────────────────┐
        │  Serviços (regras de negócio)              │   ← onde a lógica vive
        │  job / profile / matching / application…   │
        └───────┬────────────────────────┬───────────┘
                │                        │
     ┌──────────▼─────────┐   ┌──────────▼─────────────┐
     │ Repositórios       │   │ Provedores externos     │
     │ (SQLAlchemy)       │   │ LLM / embeddings /      │
     └──────────┬─────────┘   │ coletores (interfaces)  │
                │             └─────────────────────────┘
        ┌───────▼────────┐
        │ PostgreSQL     │
        └────────────────┘

  Orquestração (LangGraph): nós = finas camadas que CHAMAM serviços.
  Nenhuma regra de negócio dentro de nó ou rota.
```

**Regras invioláveis de dependência:**

- Rotas não acessam repositórios diretamente.
- Serviços não importam FastAPI.
- Nós do LangGraph reutilizam serviços — **nunca reimplementam** lógica.
- Provedores externos (LLM, embeddings, coletores) ficam atrás de **interfaces**; testes usam implementações falsas.

### 4.2 Decisões iniciais (viram ADRs na Fase 0)

| ADR | Decisão |
|-----|---------|
| 0001 | Monólito modular em Python (sem microsserviços). |
| 0002 | FastAPI + SQLAlchemy 2.x + Alembic + Pydantic v2. |
| 0003 | PostgreSQL como único datastore (JSONB para análises). |
| 0004 | LangGraph como único framework de orquestração. |
| 0005 | LLM atrás de interface `LLMProvider`; provedor configurável por `.env`. |
| 0006 | Matching determinístico primeiro; embeddings só se o golden set provar ganho. |
| 0007 | Single-user no MVP; `candidate_id` mantido nas tabelas. |
| 0009 | **GitHub é o remoto e a fonte da verdade.** Repositório privado na conta do JP (nome sugerido `JoaumPdr/jobpilot-ai`), operado pelo MCP do GitHub no VS Code (repositório, branches, PRs, CI) e pelo git local (commits e push). Push após cada commit significativo; nenhum trabalho confirmado fica só local; sem force push em branches compartilhadas; tags publicadas no remoto. |
| 0008 | **`uv` é o único gerenciador de ambiente e dependências, desde a Fase 0.** Cria e usa `.venv` automaticamente; dependências declaradas no `pyproject.toml`; versões exatas fixadas em `uv.lock` (versionado). Proibido `pip install` direto e `requirements.txt` paralelo. Dependências de desenvolvimento (pytest, Ruff, pre-commit) ficam em grupo separado das de produção. |

---

## 5. Modelo de dados revisado

Convenções: chaves `id` inteiras (ou UUID — decidir na F0-T05 e registrar em ADR), `created_at`/`updated_at` em UTC, enums como tipos nativos ou `CHECK` com valores documentados.

### 5.1 Fase 1

**`candidates`** — `id`, `name`, `email` (opcional), `resume_text`, `headline`, `created_at`, `updated_at`; `education` e `languages` como **JSONB validado por Pydantic** (normalizar depois só se as métricas pedirem).

**`candidate_preferences`** (1:1) — `candidate_id` (FK, único), `desired_titles` (lista), `locations` (lista), `work_modes` (lista), `seniority_levels` (lista), `min_salary` (opcional), `knockout_rules` (JSONB: ex. "excluir se exigir X"), `updated_at`.

**`skills`** — `id`, `canonical_name` (único), `category`, `aliases` (JSONB, PT/EN).

**`candidate_skills`** — `candidate_id`, `skill_id`, `level` (iniciante/intermediário/avançado), `years` (opcional), `evidence_note` (opcional). Único `(candidate_id, skill_id)`.

**`candidate_experiences`** — `id`, `candidate_id`, `company`, `role`, `start_date`, `end_date` (nulo = atual), `description`, `skills_used` (relação ou lista).

**`import_batches`** — `id`, `source`, `kind` (csv/manual/api), `filename`, `started_at`, `finished_at`, `total_rows`, `inserted`, `duplicates`, `rejected`, `errors` (JSONB, por linha).

**`jobs`** — `id`, `title`, `company`, `description`, `location`, `work_mode` (remoto/híbrido/presencial/desconhecido), `seniority` (estágio/júnior/pleno/sênior/…/desconhecido), `employment_type`, `salary_min`/`salary_max`/`currency` (opcionais), `source`, `external_id` (opcional), `url`, `canonical_url`, `fingerprint`, `posted_at`, `collected_at`, `import_batch_id` (FK), `is_archived`, `duplicate_of_job_id` (FK opcional, só quando o usuário confirma), `created_at`, `updated_at`.
Restrições: único `(source, external_id)` **quando `external_id` não é nulo**; índice em `fingerprint` e `canonical_url`.

**`applications`** — `id`, `candidate_id`, `job_id`, `status`, `applied_at`, `notes`, `created_at`, `updated_at`. Único `(candidate_id, job_id)`.

**`application_status_history`** — `id`, `application_id`, `from_status`, `to_status`, `changed_at`, `note`.

**Status e transições válidas (máquina de estados):**

```
salva → planejada → aplicada → entrevista → oferta → (encerrada)
   │         │          │            │          └→ rejeitada
   └─────────┴──────────┴────────────┴→ rejeitada | encerrada
```
Transições inválidas retornam erro 422 com mensagem clara; cada mudança grava histórico.

### 5.2 Fases seguintes (criar migrações só quando a fase começar)

| Tabela | Fase | Conteúdo-chave |
|--------|------|----------------|
| `job_skills` | 2 | `job_id`, `skill_id`, `requirement_type` (obrigatório/desejável), `weight`, `confidence`, `evidence_snippet`, `extraction_method`. |
| `job_matches` | 2 | `candidate_id`, `job_id`, `scoring_version`, `deterministic_score`, `semantic_score` (opcional), `match_score`, `knockout_flags` (JSONB), `analysis` (JSONB: atendidos/ausentes/não confirmados/evidências), `llm_analysis` (JSONB, opcional). Único `(candidate_id, job_id, scoring_version)`. |
| `llm_cache` | 3 | `cache_key` (hash de vaga+currículo+versão do prompt+modelo), `provider`, `model`, `prompt_version`, `response` (JSONB), `tokens_in`, `tokens_out`, `cost_estimate`, `created_at`. |
| `pipeline_runs` | 4 | `run_id`, `status`, `started_at`, `finished_at`, `params` (JSONB), `counters` (JSONB), `errors` (JSONB), `state_snapshot` (JSONB). |
| `resume_versions` | 5 | `candidate_id`, `job_id` (opcional), `parent_version_id`, `content`, `status` (rascunho/aprovada/rejeitada), `suggestions` (JSONB com evidências), `created_at`. |
| `interviews` | 6 | `application_id`, `scheduled_at`, `type`, `notes`, `outcome`. |

---

## 6. Regras de negócio centrais

### 6.1 Importação CSV

Colunas do modelo: `title`, `company`, `description`, `location`, `work_mode`, `seniority`, `url`, `external_id`, `source`, `posted_at`.
Obrigatórias: `title`, `company`, `description`. Erro em uma linha **não aborta** o lote: a linha vai para `errors` com número da linha e motivo. Reimportar o mesmo arquivo deve resultar em zero novas inserções.

### 6.2 Normalização

Remover espaços extras, normalizar caixa e acentos **para comparação** (sem alterar o texto exibido), mapear modalidade e senioridade para os enums, canonizar URL (remover parâmetros de rastreamento).

### 6.3 Deduplicação em camadas

1. `(source, external_id)` — duplicata certa.
2. `canonical_url` igual — duplicata quase certa.
3. `fingerprint` = hash de (empresa + título + localização normalizados) — duplicata provável.
4. Similaridade textual (ex.: RapidFuzz) acima de limiar — **apenas marca como "possível duplicata"** para o usuário decidir.

Nunca apagar automaticamente: o usuário confirma via `duplicate_of_job_id`.

### 6.4 Filtros

Fase 1 (SQL simples): texto livre (`ILIKE`), modalidade, localização, senioridade, fonte, intervalo de datas, status da candidatura, ocultar arquivadas/duplicadas. Busca full-text do PostgreSQL (configuração `portuguese`) é melhoria opcional.

---

## 7. Metodologia de matching (resumo; detalhe em `docs/matching-methodology.md`)

1. **Eliminatórios primeiro:** regras de preferência (`knockout_rules`, modalidade, localização) geram *flags*; vaga com flag eliminatória é rebaixada/ocultada, **sem entrar na média**.
2. **Score determinístico:** `score = Σ(peso_i × correspondência_i) / Σ(peso_i)`, com pesos de configuração versionada (ex.: obrigatório = 3, desejável = 1) e níveis de correspondência definidos (exata = 1,0; por alias/relacionada = 0,7; ausente = 0; **não confirmada = fora do cálculo e listada separadamente**).
3. **Explicabilidade obrigatória:** todo score vem com atendidos, ausentes, não confirmados e trecho de evidência.
4. **Semântico (opcional):** só entra se o golden set mostrar ganho mensurável sobre o determinístico.
5. **LLM:** explica e interpreta ambiguidades; **não altera** o score nem inventa fatos.
6. **Versionamento:** qualquer mudança de peso/regra incrementa `scoring_version`.

**Avaliação (golden set):** 30+ vagas reais anonimizadas, rotuladas à mão (requisitos obrigatórios/desejáveis, compatibilidade esperada: alta/média/baixa). Métricas: precisão/recall da extração, concordância do ranking com o rótulo, qualidade da justificativa (checklist manual), custo e latência por vaga.

---

## 8. Estratégia LLM

- **Funil de custo:** coletar → normalizar → deduplicar → filtrar → score → **somente top-N acima de limiar** vão ao LLM.
- **Interface `LLMProvider`** com implementação falsa (testes), provedor real configurável e opção de modelo local.
- **Orçamento:** limite de chamadas/tokens por execução, `timeout`, `max_tokens`, retry com backoff limitado.
- **Cache:** mesma (vaga, currículo, versão do prompt, modelo) não é reenviada.
- **Prompts versionados** em arquivos, com `prompt_version` registrado.
- **Saída estruturada validada por Pydantic;** se inválida: no máximo 1 tentativa de reparo e depois falha registrada (nunca aceitar texto livre).
- **Segurança:** descrição da vaga é *dado delimitado*; instruções de sistema proíbem inferir experiência ausente; itens sem evidência vão para `unknown_requirements`.
- **Privacidade:** enviar o mínimo de dados pessoais necessário; nunca logar currículo.

---

## 9. Estratégia de testes

| Camada | O que testar | Como |
|--------|--------------|------|
| Unitários | Normalização, dedup, score, máquina de estados, parsing de CSV, validadores | Funções puras, sem banco/rede; **TDD** nas regras determinísticas |
| Integração | Repositórios, migrações (upgrade/downgrade), constraints, importação ponta a ponta | PostgreSQL real (Docker local e *service* no CI), transação revertida por teste |
| API | Rotas, validação, códigos de erro, paginação | Cliente de teste do FastAPI |
| LLM/agentes | Contratos de entrada/saída, validação, retry, fallback | `LLMProvider` falso com respostas fixas; teste "live" opt-in por marcador, fora do CI padrão |
| Pipeline | Cada nó isolado + fluxo completo + falha parcial | Estado sintético, LLM falso |
| Avaliação | Golden set (qualidade do matching/LLM) | Script separado que gera relatório em `docs/evaluation.md` |

---

## 10. Estrutura de diretórios (mínima e incremental)

Criar apenas o que a fase atual exige. Alvo ao final do MVP:

```
jobpilot-ai/
├── app/
│   ├── api/routes/            # rotas finas
│   ├── core/                  # config, logging, erros
│   ├── models/                # SQLAlchemy
│   ├── schemas/               # Pydantic
│   ├── repositories/
│   ├── services/              # regras de negócio
│   ├── matching/              # taxonomia, extração, score (puro, sem I/O)
│   ├── llm/                   # interface, provedores, prompts, cache
│   ├── orchestration/         # state, nodes, graph (LangGraph)
│   ├── collectors/            # (Fase 7) interface JobSource
│   └── main.py
├── migrations/                # Alembic
├── prompts/                   # prompts versionados
├── data/                      # taxonomia de skills, golden set (anonimizado)
├── tests/{unit,integration,api,llm,pipeline}/
├── docs/                      # ver arquivo 03
├── scripts/
├── docker-compose.yml
├── .env.example
├── pyproject.toml             # dependências e configuração de ferramentas
├── uv.lock                    # versões exatas (versionado)
├── .python-version            # versão do Python usada pelo uv
├── README.md · RELATORIO.md · design.md
└── .github/workflows/ci.yml
```

---

## 11. Fases, resultados e gates de saída

Cada fase = **1 branch de fase** + **1 tag** ao fechar. Ninguém avança sem o gate verde.

| Fase | Nome | Resultado | Gate de saída |
|------|------|-----------|---------------|
| 0 | Fundação | Repo, CI, Docker, FastAPI `/health`, Alembic, docs-base | CI verde (instalando com `uv sync --locked`); `uv sync` + `docker compose up` + `/health` funcionando; `uv.lock` versionado; repositório remoto no GitHub com `main`, `develop` e `phase/00-fundacao` enviadas e docs no primeiro commit; ADRs 0001–0009 e README inicial escritos |
| 1 | Núcleo sem IA | Perfil, vagas, CSV, dedup, filtros, candidaturas + histórico | RF-01…06 cobertos por testes; reimportação idempotente; cobertura de serviços ≥ 85%; docs de API e dados atualizadas |
| 2 | Matching | Taxonomia, extração, eliminatórios, score explicável, golden set | RF-07…09; golden set com relatório de métricas; `scoring_version` ativa |
| 3 | Camada LLM | Provedor abstrato, cache, análise validada, avaliação | RF-10; nenhuma resposta inválida persistida; custo/latência por vaga medidos |
| 4 | Orquestração | Pipeline LangGraph com logs, retry, execução persistida | RF-11; testes por nó + fluxo; **checklist de 10 critérios do MVP** → tag `v0.1.0` |
| 5 | Assistente de currículo | Sugestões com evidência + aprovação humana | RF-12; validador anti-invenção bloqueia fatos novos; nada exportado sem aprovação |
| 6 | Dashboard | Streamlit + analytics de funil | RF-13; definições de métricas documentadas |
| 7 | Hardening e release | Segurança, desempenho, coletor autorizado opcional, documentação final e distribuição local por Docker Compose | RNF-01…13 verificados e F7-T06 a F7-T09 concluídas. Terceiro instala o candidato a release do zero pelo README, configura e inicia os serviços, abre a interface no navegador e comprova persistência, backup e restauração → tag `v1.0.0` |

Detalhe das tarefas, dependências e critérios de aceitação: **arquivo 04**.

---

## 12. Mapa dos 10 critérios de conclusão do MVP

| Critério (plano original) | Entregue em |
|---------------------------|-------------|
| 1. Cadastrar perfil | Fase 1 |
| 2. Importar e persistir vagas | Fase 1 |
| 3. Identificar duplicatas | Fase 1 |
| 4. Filtros objetivos | Fase 1 |
| 5. Salvar vagas e gerir candidaturas | Fase 1 |
| 6. Matching com score e explicação | Fase 2 |
| 7. Análise do agente com estrutura validada | Fase 3 |
| 8. Pipeline registra erros e resultados | Fase 4 |
| 9. Testes cobrem regras centrais | Fases 1–4 (gate de cada fase) |
| 10. README (instalação, configuração, arquitetura, execução) | Fase 0 (base) → atualizado a cada fase → fechado na Fase 4 |

---

## 13. Riscos e mitigação

| Risco | Impacto | Mitigação |
|-------|---------|-----------|
| Estourar o escopo | Projeto nunca fecha o MVP | Gates por fase; "fora de escopo" explícito (§2.3) |
| Esgotar tokens no meio de uma tarefa | Trabalho perdido ou inconsistente | Tarefas pequenas, `STATUS.md`, commits frequentes, push constante para o GitHub (arquivo 02, §4A) |
| Alucinação do LLM | Informação falsa no currículo/análise | Saída estruturada, evidência obrigatória, validador anti-invenção, revisão humana |
| Termos de uso das fontes | Bloqueio ou problema legal | Só fontes autorizadas; checklist por coletor; MVP funciona só com CSV |
| Golden set enviesado | Métricas enganosas | Variar cargos/fontes/idiomas; revisar rótulos |
| Custos de API | Surpresa na fatura | Funil de custo, cache, orçamento por execução, modelo local como alternativa |
| Vazamento de dados pessoais | Privacidade | `.env`, logs sem PII, minimização, documentação LGPD |
| Taxonomia de skills incompleta | Extração fraca | Taxonomia evolutiva (arquivo versionado) + relatório de termos não reconhecidos |

---

## 14. Próximo passo

Entregar o arquivo `02_Instrucoes_Alethe` à Alethe junto com este pacote e iniciar pela **Fase 0, tarefa F0-T01**.
