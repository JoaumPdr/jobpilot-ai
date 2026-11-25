# JobPilot AI — Backlog e Tasks

> Vira `docs/BACKLOG.md`. Marque `[x]` ao concluir. Estado vivo e retomada ficam em `docs/STATUS.md`.
> **Planejamento just-in-time:** a ficha detalhada (`docs/tasks/FASE-XX/Fx-Tyy.md`) é criada só quando a tarefa vai começar e **somente quando ela exigir planejamento detalhado** (várias etapas, decisão arquitetural, vários arquivos, risco relevante ou plano de testes não trivial). Tarefas pequenas e diretas são planejadas no próprio BACKLOG.
> **Sem fichas retroativas:** tarefas já concluídas (Fase 0) não recebem ficha.
> **Divisão de responsabilidade:** o BACKLOG decide **o que** fazer e **quando** está pronto (critérios canônicos); a ficha explica **como** executar e verificar; o `STATUS.md` registra **onde estamos** e como retomar.

---

## Como ler as tabelas

- **ID:** `F<fase>-T<número>`. Subtarefas: `-a`, `-b`.
- **Depende de:** não iniciar antes de concluir.
- **Branch:** sempre a partir da branch da fase, **enviada ao GitHub logo após o primeiro commit**.
- **Sincronização:** toda tarefa termina com push feito e verificado; todo gate de fase só fecha com PR mesclado no GitHub, CI verde no remoto e tag publicada (rotina na seção 4A do `ALETHE_INSTRUCOES.md` e B.9 do `GUIA_DOCS_E_GIT.md`).
- **Aceitação:** condições objetivas e verificáveis; todas precisam ser atendidas.
- **Ficha:** quando existir em `docs/tasks/FASE-XX/`, complementa a linha da tabela; os critérios de aceitação canônicos continuam sendo os desta tabela.

## Modelo de ficha de tarefa (quando aplicável)

```text
# Fx-Tyy — Título
- Fase / Branch:
- Depende de:
- Objetivo (1–2 frases):
- Contexto necessário (arquivos/docs a ler):
- Escopo (o que entra) / Fora de escopo (o que NÃO entra):
- Arquivos prováveis:
- Passos sugeridos:
- Critérios de aceitação (referência ao BACKLOG; detalhar apenas como verificar):
  - [ ] ...
- Plano de testes (unit / integração / API):
- Docs a atualizar:
- Riscos e dúvidas:
- Estado: não iniciada | em andamento | concluída
- Notas de retomada (preencher se parar no meio):
```

---

## FASE 0 — Fundação · branch `phase/00-fundacao` · tag `fase-00`

| ID | Tarefa | Depende de | Critérios de aceitação |
|----|--------|-----------|------------------------|
| [x] F0-T01 | Criar o **repositório no GitHub** (via MCP, privado, nome sugerido `JoaumPdr/jobpilot-ai`), configurar `origin`, branches `main`/`develop`/`phase/00-fundacao`, `.gitignore`, licença, estrutura `docs/`, pacote de documentos, `.github/PULL_REQUEST_TEMPLATE.md`, milestones das fases e labels; primeiro push | — | Repositório existe no GitHub e `origin` está configurado; as três branches estão no remoto; pacote de docs em `docs/` com os nomes corretos já no primeiro commit enviado; `.gitignore` cobre `.env`, `.venv`, caches (e **não** ignora `uv.lock`); `git status -sb` sem divergência; proteção de branch configurada ou limitação registrada no `STATUS.md`; link do repositório no `README` e no `STATUS.md` |
| [x] F0-T02 | Ambiente Python com **`uv`**: projeto inicializado com `pyproject.toml`, `.python-version` (3.12+), `uv.lock` versionado, grupo de dependências de desenvolvimento separado (pytest, Ruff, pre-commit), Ruff, pytest, pre-commit | F0-T01 | Instalação do zero em máquina limpa com `uv sync` seguindo o README; `lint` e `test` rodam via `uv run` (mesmo com 1 teste trivial); `uv.lock` commitado; nenhum `requirements.txt` nem uso de `pip install` direto; ADR 0008 (uv) registrado |
| [x] F0-T03 | Docker Compose do PostgreSQL, `.env.example`, configuração tipada de ambiente | F0-T02 | `docker compose up` sobe o banco; app lê configuração do `.env`; app falha com mensagem clara se faltar variável obrigatória |
| [x] F0-T04 | Esqueleto FastAPI: `/health`, logging estruturado com `request_id`, tratamento padrão de erros | F0-T03 | `/health` responde 200 com status do app e do banco; erros seguem formato único; teste de API cobre `/health` |
| [x] F0-T05 | SQLAlchemy + Alembic: conexão, sessão por requisição, migração inicial; decidir tipo de ID (int vs UUID) em ADR | F0-T04 | `upgrade` e `downgrade` funcionam; teste de integração conecta no banco; ADR do tipo de ID registrado |
| [x] F0-T06 | CI no GitHub Actions usando **`uv`** (instalação com lock travado, lint + testes + PostgreSQL + migração) | F0-T05 | CI verde em PR; instala dependências com `uv sync --locked` (falha se `uv.lock` estiver desatualizado); comandos executados via `uv run`; falha se lint/teste/cobertura mínima falhar |
| [x] F0-T07 | Docs-base: README inicial (com objetivo do repo), `design.md`, `RELATORIO.md`, ADRs 0001–0009 (inclui o ADR de sincronização com o GitHub), `docs/privacy-and-sources.md`, `STATUS.md` preenchido | F0-T01 | Todos os arquivos existem e seguem o `GUIA_DOCS_E_GIT.md`; README explica instalação e execução **com `uv`** (`uv sync`, `uv run`) e declara o objetivo de estudo de orquestração multiagente; ADR 0008 explica a escolha do `uv` |
| [x] F0-GATE | Gate da fase | todas | Itens do gate em `PLANO.md` §11 verdes → PR #4 `phase/00` → `develop` **mesclado no GitHub com CI verde**, tag `fase-00` **publicada no remoto** (`cbbeb65`), seção da fase no `RELATORIO.md` |

---

## FASE 1 — Núcleo sem IA · branch `phase/01-nucleo-sem-ia` · tag `fase-01`

| ID | Tarefa | Depende de | Critérios de aceitação |
|----|--------|-----------|------------------------|
| [x] F1-T01 | Modelos e migração do **perfil**: `candidates`, `candidate_preferences`, `skills`, `candidate_skills`, `candidate_experiences` | F0-GATE | Migração reversível; constraints (únicos, FKs) testadas; `docs/data-model.md` criado |
| [x] F1-T02-a | Serviço e rotas do **perfil — candidato e preferências**: CRUD de candidato, upsert 1:1 de preferências, erros padronizados, base de `docs/api.md` | F1-T01 | Validações Pydantic (incl. `education`/`languages` como JSONB estruturado); erros 404/415/409/422 padronizados; testes unitários e de API; `docs/api.md` criado |
| [x] F1-T02-b | Serviço e rotas do **perfil — habilidades e experiências**: catálogo (`POST /skills`), vínculo candidato/skill e CRUD de experiências | F1-T02-a | Validações Pydantic (`level`, `years >= 0`, datas); erros 404/409/422 padronizados; testes unitários e de API; `docs/api.md` atualizado |
| [x] F1-T03 | Modelos e migração de **vagas**: `jobs`, `import_batches` (com enums de modalidade e senioridade) | F0-GATE | Único `(source, external_id)` só quando `external_id` existe; índices em `fingerprint` e `canonical_url`; testes de constraint |
| [x] F1-T04 | **Normalização** e canonização (texto, modalidade, senioridade, URL, fingerprint) — funções puras | F1-T03 | Testes unitários cobrindo acentos, caixa, espaços, URLs com parâmetros de rastreio; sem acesso a banco |
| [x] F1-T05 | **Cadastro manual** de vaga (serviço + rota) usando normalização e dedup | F1-T04 | Vaga manual salva normalizada; duplicata certa/provável retorna aviso claro (não erro cego); testes |
| [x] F1-T06 | **Importação CSV** com relatório por linha e idempotência | F1-T05 | Linha inválida não aborta o lote; `import_batches` registra contadores e erros; reimportar o mesmo arquivo = 0 inserções; modelo de CSV documentado; teste de 5 mil linhas dentro do RNF-09 |
| [x] F1-T07 | **Deduplicação em camadas** + revisão humana (`possíveis duplicatas`, confirmar via `duplicate_of_job_id`) | F1-T05 | Camadas 1–4 do `PLANO.md` §6.3; nada é apagado automaticamente; endpoints para listar/confirmar/desfazer; testes |
| [x] F1-T08 | **Listagem e filtros** de vagas (texto, modalidade, localização, senioridade, fonte, datas, ocultar arquivadas/duplicadas) + paginação | F1-T06, F1-T07 | Filtros combináveis; paginação estável; listagem < 500 ms com 10 mil vagas (RNF-09); testes de API |
| [x] F1-T09 | Modelos e migração de **candidaturas**: `applications`, `application_status_history` | F1-T03 | Único `(candidate_id, job_id)`; histórico ligado à candidatura; testes |
| [x] F1-T10 | **Serviço e rotas de candidaturas** com máquina de estados e histórico e filtro por status da candidatura na listagem de vagas | F1-T09, F1-T02, F1-T08 | Transições válidas conforme `PLANO.md` §5.1; inválidas → 422 com mensagem; cada mudança grava histórico; observações editáveis; testes unitários da máquina de estados. O filtro por status é aplicado à candidatura do candidato consultado e combina com os filtros existentes, com teste de API |
| [x] F1-T11 | **Arquivar/salvar** vagas e atalhos de fluxo (salvar vaga cria candidatura "salva") | F1-T10, F1-T08 | Fluxo salvar → planejada → aplicada coberto por teste de integração |
| [x] F1-T12 | **Testes de ponta a ponta da Fase 1** + revisão de cobertura | F1-T11 | Cenário completo (perfil → importar → filtrar → candidatar) verde; cobertura serviços ≥ 85%, global ≥ 70% |
| [x] F1-T13 | Docs da fase: `api.md`, `data-model.md`, README, `RELATORIO.md`, `CHANGELOG.md` | F1-T12 | Documentos refletem o código; README ensina o fluxo completo da Fase 1 |
| [x] F1-GATE | Gate da fase | todas | RF-01…06 cobertos; reimportação idempotente; CI verde → PR para `develop`, tag `fase-01` |

---

## FASE 2 — Matching · branch `phase/02-matching` · tag `fase-02`

| ID | Tarefa | Depende de | Critérios de aceitação |
|----|--------|-----------|------------------------|
| [x] F2-T01 | **Taxonomia de skills** (arquivo versionado em `data/`, categorias, aliases PT/EN) + serviço de normalização de termos. [Ficha](tasks/FASE-02/F2-T01.md) | F1-GATE | Pelo menos ~150 skills iniciais de tecnologia/dados; busca por alias; relatório de termos não reconhecidos; testes |
| [x] F2-T02 | **Extrator determinístico de requisitos** (seções "requisitos/diferenciais", palavras-gatilho, taxonomia) → `job_skills`. [Ficha](tasks/FASE-02/F2-T02.md) | F2-T01 | Classifica obrigatório vs desejável com `confidence` e `evidence_snippet`; funciona em PT e EN; função pura testada |
| [x] F2-T03 | **Filtros eliminatórios** (knockouts) separados do score. [Ficha](tasks/FASE-02/F2-T03.md) | F1-GATE | Flags geradas a partir de `knockout_rules` e preferências; vaga com flag não entra na média; testes por regra |
| [x] F2-T04 | **Score determinístico explicável** + configuração de pesos versionada + `scoring_version`. [Ficha](tasks/FASE-02/F2-T04.md) | F2-T02, F2-T03 | Fórmula e níveis de correspondência conforme `PLANO.md` §7; "não confirmado" fora do cálculo e listado; mesma entrada → mesmo score; `docs/matching-methodology.md` criado |
| [x] F2-T05 | **Persistência e rotas de matching** (`job_matches`; calcular, listar ranking, detalhar com evidências). [Ficha](tasks/FASE-02/F2-T05.md) | F2-T04 | Único `(candidate_id, job_id, scoring_version)`; ranking filtrável; detalhe mostra atendidos/ausentes/não confirmados/evidências |
| [x] F2-T06 | **Golden set** (30+ vagas anonimizadas e rotuladas) + script de avaliação + relatório. [Ficha](tasks/FASE-02/F2-T06.md) | F2-T05 | Dataset em `data/golden/`; relatório gerado em `docs/evaluation.md` com precisão/recall da extração e concordância do ranking |
| [x] F2-T07 | *(Condicional)* **Embeddings multilíngues** como sinal semântico. Adoção adiada no [ADR 0012](adr/0012-adiar-embeddings-multilingues.md). [Ficha](tasks/FASE-02/F2-T07.md) | F2-T06 | Só executar se `docs/evaluation.md` mostrar ganho mensurável; comparação determinístico vs semântico documentada; caso contrário, registrar ADR "não adotar por ora" |
| [x] F2-T08 | Docs e relatório da fase. [Ficha](tasks/FASE-02/F2-T08.md) | F2-T06 | `matching-methodology.md`, `evaluation.md`, `RELATORIO.md`, README atualizados |
| [x] F2-GATE | Gate da fase. [Ficha](tasks/FASE-02/F2-GATE.md) | todas | RF-07…09; golden set com métricas; `scoring_version` ativa → PR para `develop`, tag `fase-02` |

---

## FASE 3 — Camada LLM · branch `phase/03-camada-llm` · tag `fase-03`

| ID | Tarefa | Depende de | Critérios de aceitação |
|----|--------|-----------|------------------------|
| [x] [F3-T01](tasks/FASE-03/F3-T01.md) | **Interface `LLMProvider`** + provedor falso + 1 provedor real configurável (e/ou local) + configurações (timeout, retry, max tokens, orçamento) | F2-GATE | Troca de provedor só por `.env`; provedor falso usado em todos os testes; chave nunca em log |
| [x] [F3-T02](tasks/FASE-03/F3-T02.md) | **Schemas de saída** (Pydantic) e **prompts versionados** em `prompts/` com política anti-inferência | F3-T01 | Campos: `job_id`, `matched_skills`, `missing_skills`, `unknown_requirements`, `recommendation`, `explanation`, `evidence`; `prompt_version` registrado |
| [x] [F3-T03](tasks/FASE-03/F3-T03.md) | **Sanitização e defesa de entrada**: descrição de vaga delimitada como dado, limite de tamanho, minimização de dados pessoais | F3-T02 | Testes com descrições contendo "instruções" maliciosas não alteram o comportamento; currículo enviado apenas no necessário |
| [x] [F3-T04](tasks/FASE-03/F3-T04.md) | **Cache e registro de custo** (`llm_cache`, tokens, custo estimado, latência) | F3-T01 | Mesma entrada não gera nova chamada; métricas por chamada registradas; `docs/llm-strategy.md` criado |
| [x] [F3-T05](tasks/FASE-03/F3-T05.md) | **Serviço de análise de vaga**: valida saída, 1 reparo máximo, falha registrada, itens sem evidência → `unknown_requirements` | F3-T02, F3-T03, F3-T04 | Nenhuma saída inválida persistida; LLM não altera o score determinístico; testes com respostas válidas, inválidas e vazias |
| [x] [F3-T06](tasks/FASE-03/F3-T06.md) | **Avaliação no golden set**: determinístico vs +LLM, custo e latência por vaga | F3-T05 | Resultados em `docs/evaluation.md`; decisão registrada sobre limiar/top-N para o funil de custo |
| [x] F3-T07 | [Docs e relatório da fase](tasks/FASE-03/F3-T07.md) | F3-T06 | `llm-strategy.md`, `evaluation.md`, `RELATORIO.md`, README atualizados |
| [x] [F3-GATE](tasks/FASE-03/F3-GATE.md) | Gate da fase | todas | RF-10; custo/latência medidos; CI verde sem chamar LLM real → PR para `develop`, tag `fase-03` |

---

## FASE 4 — Orquestração (LangGraph) · branch `phase/04-orquestracao` · tags `fase-04` e `v0.1.0`

| ID | Tarefa | Depende de | Critérios de aceitação |
|----|--------|-----------|------------------------|
| [x] [F4-T01](tasks/FASE-04/F4-T01.md) | **Estado do pipeline** e contratos de entrada/saída dos nós | F3-GATE | Estado tipado e validado; contratos documentados em `docs/pipeline.md` |
| [x] [F4-T02](tasks/FASE-04/F4-T02.md) | **Nós determinísticos**: importar, normalizar, deduplicar, filtrar (chamando os serviços existentes) | F4-T01 | Nenhuma lógica de negócio duplicada; cada nó testado isoladamente |
| [x] [F4-T03](tasks/FASE-04/F4-T03.md) | **Nós de matching, seleção top-N e análise LLM** | F4-T02 | Seleção usa limiar e orçamento definidos na F3-T06; só o top-N chega ao LLM; LLM falso nos testes |
| [ ] [F4-T04](tasks/FASE-04/F4-T04.md) | **Transições condicionais, retry e falha parcial** | F4-T03 | Falha em uma vaga não derruba a execução; retry limitado; erros registrados por item |
| [ ] F4-T05 | **Persistência da execução** (`pipeline_runs`) + logging com `run_id` + idempotência/retomada | F4-T04 | Reexecutar não duplica dados; execução interrompida pode ser retomada ou reiniciada com segurança |
| [ ] F4-T06 | **Ponto de aprovação humana** (interrupção antes de ações sensíveis; no MVP o fluxo termina na lista de recomendações) | F4-T04 | Nenhuma ação automática de candidatura existe; aprovação é explícita |
| [ ] F4-T07 | **Rotas do pipeline** (`POST /pipeline/runs`, `GET /pipeline/runs/{id}`) + testes do fluxo completo | F4-T05 | Fluxo completo verde com LLM falso; cenários de falha parcial cobertos |
| [ ] F4-T08 | **Fechamento do MVP**: checklist dos 10 critérios (`PLANO.md` §12), README final do MVP, `CHANGELOG`, `RELATORIO` | F4-T07 | Todos os critérios marcados com evidência (link para teste/doc) |
| [ ] F4-GATE | Gate da fase | todas | RF-11 + 10 critérios do MVP → PR para `develop`, tag `fase-04`; PR `develop` → `main`, tag `v0.1.0` |

---

## FASE 5 — Assistente de currículo · branch `phase/05-assistente-curriculo` · tag `fase-05` / `v0.2.0`

| ID | Tarefa | Depende de | Critérios de aceitação |
|----|--------|-----------|------------------------|
| [ ] F5-T01 | **Currículo estruturado** com seções e IDs estáveis + conversão do texto base (com revisão humana) | F4-GATE | Cada trecho tem ID rastreável; usuário confirma a estrutura |
| [ ] F5-T02 | **Gerador de sugestões** com vínculo de evidência (cada sugestão aponta para o trecho original) e classificação (reordenar, reescrever, destacar, *não comprovado*) | F5-T01 | Sugestão sem evidência é rejeitada; tipos de sugestão documentados |
| [ ] F5-T03 | **Validador anti-invenção** determinístico (empresas, datas, números, tecnologias, cargos ausentes do original) | F5-T02 | Teste com conjunto de "alucinações plantadas" é 100% bloqueado ou marcado |
| [ ] F5-T04 | **Revisão e aprovação** (rascunho → aprovada/rejeitada), diff e versões (`resume_versions`) | F5-T03 | Nada é aprovado sem ação explícita; histórico de versões preservado |
| [ ] F5-T05 | **Exportação** de versões aprovadas (Markdown; PDF/DOCX opcional) | F5-T04 | Impossível exportar versão não aprovada (teste) |
| [ ] F5-T06 | Testes e docs da fase | F5-T05 | `RELATORIO.md`, README, `llm-strategy.md` atualizados |
| [ ] F5-GATE | Gate da fase | todas | RF-12; validador anti-invenção ativo → `develop`, tag `fase-05` |

---

## FASE 6 — Dashboard e analytics · branch `phase/06-dashboard` · tag `fase-06` / `v0.3.0`

| ID | Tarefa | Depende de | Critérios de aceitação |
|----|--------|-----------|------------------------|
| [ ] F6-T01 | **Camada de métricas** (consultas SQL/visões) + rotas `/analytics`; **definições formais** das métricas (taxa de resposta, entrevista, etc.) | F4-GATE | Definições em `docs/analytics.md`; testes com dados sintéticos de resultado conhecido |
| [ ] F6-T02 | **App Streamlit base** consumindo a API (não acessa o banco direto) | F6-T01 | Navegação, configuração de URL da API, tratamento de erro de conexão |
| [ ] F6-T03 | **Páginas** de vagas/ranking (com explicação do score) e pipeline de candidaturas | F6-T02 | Exibe atendidos/ausentes/não confirmados; permite mudar status respeitando a máquina de estados |
| [ ] F6-T04 | **Analytics**: funil, competências mais demandadas, desempenho por fonte/cargo/competência | F6-T03 | Gráficos com dados reais do banco de teste; filtros por período |
| [ ] F6-T05 | **Entrevistas** (`interviews`) — registro e visualização | F6-T03 | CRUD básico; ligadas à candidatura |
| [ ] F6-T06 | Docs: capturas de tela no README, `analytics.md`, `RELATORIO.md` | F6-T04 | README ilustrado e atualizado |
| [ ] F6-GATE | Gate da fase | todas | RF-13; métricas documentadas → `develop`, tag `fase-06` |

---

## FASE 7 — Hardening e release · branch `phase/07-hardening-release` · tags `fase-07` e `v1.0.0`

| ID | Tarefa | Depende de | Critérios de aceitação |
|----|--------|-----------|------------------------|
| [ ] F7-T01 | **Revisão de segurança e privacidade** (segredos, logs sem PII, dependências, validação de entradas, CORS, limites de upload) | F6-GATE | Checklist em `docs/security.md` todo marcado; varredura de segredos limpa |
| [ ] F7-T02 | **Desempenho** (índices, N+1, tempos de RNF-09) | F6-GATE | Metas do RNF-09 comprovadas por teste/medição documentada |
| [ ] F7-T03 | *(Opcional)* **Primeiro coletor autorizado** atrás da interface `JobSource`, com checklist de termos de uso | F6-GATE | Fonte com API oficial/feed permitido; respeita limites e *rate limit*; desabilitável; `privacy-and-sources.md` atualizado; **sem** contornar proteções |
| [ ] F7-T04 | **Cobertura e e2e finais** | F7-T01 | Cobertura ≥ metas do RNF-03; cenário e2e do produto completo verde |
| [ ] F7-T05 | **Docs finais**: README completo, `design.md`, `RELATORIO.md` consolidado, `CHANGELOG.md` | F7-T04, F7-T07, F7-T08 | README documenta os pré-requisitos e os passos de instalação, configuração e execução do pacote, a URL da interface e os procedimentos de backup e restauração ou seus links. Documentação final corresponde ao candidato a release e serve de roteiro para a F7-T09. |
| [ ] F7-T06 | **Empacotamento de produção local** com Docker Compose | F7-T01 | A configuração de distribuição reaproveita o PostgreSQL, o volume nomeado e a verificação de saúde existentes onde forem aplicáveis. A partir de um banco vazio, o Compose coordena a inicialização da API FastAPI, da interface Streamlit e do PostgreSQL, com o esquema inicial aplicado. A API passa na verificação de saúde, a interface abre no navegador local e consome a API, e a execução dispensa instalação de Python, `uv` e PostgreSQL no host. |
| [ ] F7-T07 | **Configuração inicial segura** da distribuição local | F7-T06 | `.env.example` lista as variáveis usadas pelo pacote com exemplos sem segredos reais. A documentação explica como criar e preencher o `.env` e quando são necessárias credenciais do provedor de IA. Testes cobrem configuração válida e variáveis obrigatórias ausentes ou inválidas, com mensagens que identificam a variável sem expor seu valor. Segredos ficam fora do Git, das imagens e dos logs. |
| [ ] F7-T08 | **Persistência, backup e restauração** | F7-T06 | Dados de teste permanecem consultáveis após reiniciar e recriar os containers com o volume PostgreSQL preservado. A documentação identifica o que preservar, incluindo o backup do banco, a configuração local e os arquivos do usuário aplicáveis, e como proteger os artefatos com dados sensíveis. O procedimento documentado gera um backup fora dos containers e restaura os dados de teste em um banco vazio, com conferência dos registros restaurados. |
| [ ] F7-T09 | **Teste de instalação limpa por terceiro** | F7-T02, F7-T05 | Uma pessoa que não preparou o pacote segue o README em um ambiente limpo diferente do de desenvolvimento, sem Python, `uv` ou PostgreSQL no host. A validação comprova pré-requisitos identificáveis, configuração inicial funcional, serviços saudáveis, acesso à interface no navegador, dados preservados após reinício e recriação dos containers e backup restaurado conforme o roteiro. O `RELATORIO.md` registra a versão testada, o ambiente, os resultados, os problemas, as correções e o resultado do novo teste quando houver correções. |
| [ ] F7-GATE | Gate da fase | todas as obrigatórias, incluindo F7-T06 a F7-T09 | RNF-01…13 verificados e instalação limpa do candidato a release comprovada e registrada na F7-T09 → `develop`, tag `fase-07`; `develop` → `main`, tag `v1.0.0` |

---

## Registro de divisões de tarefas

*(A Alethe registra aqui qualquer tarefa dividida: ID original → subtarefas e motivo.)*
*(Dividir só quando a separação preservar unidades coesas; caso contrário, manter a tarefa inteira e justificar na ficha.)*

| Tarefa original | Subtarefas | Motivo | Data |
|-----------------|-----------|--------|------|
| F1-T02 | F1-T02-a (candidato + preferências + erros + `api.md`), F1-T02-b (skills + experiências) | Estimativa de ~11 arquivos e 900–1300 linhas, acima do limite de ~8 arquivos/400 linhas; a divisão separa unidades coesas (perfil base vs. relacionamentos) e permite revisão e CI por etapa. `-b` depende de `-a` para reaproveitar erros, schemas e fixtures. | 2026-11-16 |
