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

## Fase 1 — Núcleo sem IA (concluída)

### F1-T08 — Listagem e filtros de vagas (2026-11-19)
- **O que foi feito.** `GET /jobs` com filtros combináveis e paginação. Arquivadas e duplicatas confirmadas ficam ocultas por padrão e podem ser incluídas separadamente.
- **Decisões e motivos.** A ordenação por data de cadastro e UUID desempata vagas do mesmo lote. Buscar um item adicional permite calcular `has_more` na mesma consulta da página.
- **Testes.** 23 testes de API cobrem filtros, paginação, validação e a meta de 500 ms com 10 mil vagas em PostgreSQL.
- **Continuação.** A F1-T10 acrescentou o filtro por status de candidatura sobre o modelo criado pela F1-T09.

### F1-T09 — Modelos e migração de candidaturas (2026-11-19)
- **O que foi feito.** Modelos de candidatura e histórico de status com a migração reversível `000000000004`.
- **Decisões e motivos.** A unicidade por candidato e vaga evita registros concorrentes duplicados. A exclusão de perfil remove seus históricos, e as vagas vinculadas podem ser arquivadas com o histórico preservado.
- **Testes.** 13 testes de constraints e 289 testes na suíte completa. O ciclo de migração validou a preservação de registros de perfil e vaga em PostgreSQL. A comparação do schema detectou somente duas diferenças de índices já presentes na revisão anterior.

### F1-T10 — Serviço e rotas de candidaturas (2026-11-19)

- **O que foi feito.** Rotas de criação, listagem, consulta e edição de candidaturas por candidato. O filtro por status de candidatura combina com os filtros de `GET /jobs`.
- **Decisões e motivos.** Estado e histórico são gravados na mesma transação. Um bloqueio na linha da candidatura serializa atualizações concorrentes e preserva a sequência de transições.
- **Testes.** 49 casos unitários para o grafo de estados e três testes de API. A suíte completa passou com 341 testes em PostgreSQL.

### F1-T11 — Arquivar e salvar vagas (2026-11-19)

- O arquivamento usa o campo `is_archived` e preserva as candidaturas vinculadas. A listagem continua ocultando vagas arquivadas por padrão.
- O atalho de salvar reutiliza o serviço de candidaturas, que grava o estado `salva` e a primeira entrada do histórico na mesma transação.
- Três testes de integração verificam o arquivamento, o fluxo `salva` → `planejada` → `aplicada` e a resposta para referências ausentes. A suíte completa passou com 359 testes em PostgreSQL.

### F1-T12 — Fluxo de ponta a ponta e cobertura (2026-11-19)

- Um teste com PostgreSQL verifica o fluxo pela API desde a criação do perfil até a consulta do histórico da candidatura. Reimportar o mesmo CSV produz zero vagas novas.
- O [CI da fase](https://github.com/JoaumPdr/jobpilot-ai/actions/runs/44604854927) passou com 360 testes, 96,60% de cobertura global e 95,33% nos serviços. Os mínimos no CI são 70% e 85%, respectivamente.

### F1-T13 — Documentação da Fase 1 (2026-11-19)

- O [README](README.md#fluxo-da-fase-1) reúne um roteiro local com dados fictícios, importação e reimportação de CSV, filtros e acompanhamento de candidaturas. A [API](docs/api.md) e o [modelo de dados](docs/data-model.md) detalham o contrato e a persistência.
- O [changelog](CHANGELOG.md) registra as entregas da Fase 1. O [backlog](docs/BACKLOG.md) registra a conclusão do gate.

### F1-GATE — Validação de saída (2026-11-19)

- A [ficha do gate](docs/tasks/FASE-01/F1-GATE.md) relaciona RF-01 a RF-06 aos testes da fase, incluindo a reimportação de CSV sem novas vagas e o histórico de candidaturas.
- A revisão `8c852a7` passou localmente com 360 testes em PostgreSQL, 96,60% de cobertura em `app` e 95,33% em `app/services`. O [CI da fase](https://github.com/JoaumPdr/jobpilot-ai/actions/runs/44608937267) também passou com Ruff, formatação e ciclo de migração Alembic.
- O [PR #26](https://github.com/JoaumPdr/jobpilot-ai/pull/26) integrou a fase em `develop` com histórico no commit `bbea363`. Depois do [CI verde em `develop`](https://github.com/JoaumPdr/jobpilot-ai/actions/runs/44610945327), a tag anotada [`fase-01`](https://github.com/JoaumPdr/jobpilot-ai/tree/fase-01) foi publicada nesse commit.

## Fase 2 — Matching (concluída)

### F2-T01 — Taxonomia de skills (2026-11-23)

- O [catálogo TOML](data/taxonomy/skills.toml) reúne 184 habilidades em 9 categorias, com aliases em português e inglês. A consulta ignora caixa, acentos e variações de espaço, e preserva pontuação significativa em termos como `C++` e `C#`.
- O catálogo rejeita aliases ambíguos no carregamento. O relatório agrega termos desconhecidos em memória e ordena por frequência, com desempate alfabético. [Ficha da F2-T01](docs/tasks/FASE-02/F2-T01.md)
- A suíte com PostgreSQL passou com 387 testes, 27 sobre a taxonomia. Cobertura de linhas de 96,70% em `app` e 95,46% em `app/services`. Ruff e formatação passaram.

### F2-T02 — Extrator determinístico de requisitos (2026-11-23)

- O extrator classifica habilidades da taxonomia como obrigatórias ou desejáveis
  a partir de seções e gatilhos em português e inglês. Guarda a confiança da
  regra e um trecho literal da vaga. [Ficha da F2-T02](docs/tasks/FASE-02/F2-T02.md)
- A migração `000000000005` adiciona `job_skills`. Cadastro manual e importação
  persistem os requisitos na transação da vaga, e o serviço permite reprocessar
  vagas anteriores. [Modelo de dados](docs/data-model.md#requisitos-extraídos-job_skills-f2-t02)
- A suíte passou com 400 testes em PostgreSQL, 13 novos. Cobertura de linhas de
  96,74% em `app` e 95,17% em `app/services`. Ruff e formatação passaram.

### F2-T03 — Filtros eliminatórios (2026-11-23)

- A avaliação devolve flags com o motivo e o valor encontrado na vaga. O
  resultado sinaliza quais vagas podem entrar na média do score. As regras
  cobrem modalidade, localização, empresas excluídas e habilidades
  obrigatórias excluídas. [Ficha da F2-T03](docs/tasks/FASE-02/F2-T03.md)
- A API valida as duas listas operacionais e preserva as demais chaves do
  JSON de preferências. A habilidade desejável fica fora da regra de
  exclusão. [Contrato de preferências](docs/api.md#preferências-11)
- Ruff e formatação passaram. A suíte com PostgreSQL passou com 420 testes,
  20 novos. Cobertura de linhas de 96,90% em `app` e 95,27% em `app/services`.

### F2-T04 — Score determinístico explicável (2026-11-24)

- A versão `deterministico-v1` calcula a média ponderada com pesos 3 e 1.
  Os eliminatórios interrompem a avaliação, e a explicação preserva as
  evidências dos requisitos atendidos, ausentes e não confirmados. [Metodologia](docs/matching-methodology.md)
- A ausência explícita contribui com fator zero. Os requisitos não
  confirmados ficam fora do numerador e do denominador. A configuração
  permite declarar relações direcionais entre habilidades. [Configuração](data/matching/scoring.toml)
- Ruff e formatação passaram. A suíte com PostgreSQL passou com 434 testes,
  14 novos. Cobertura de linhas de 97,05% em `app` e 95,35% em `app/services`.

### Manutenção do CI — Node.js 24 (2026-11-24)

- O [PR #32](https://github.com/JoaumPdr/jobpilot-ai/pull/32) atualizou
  `actions/checkout` para v7.0.1 e `astral-sh/setup-uv` para v10.4.0.
  O workflow passou na branch da fase sem o aviso de Node.js 20.
  [Execução do CI](https://github.com/JoaumPdr/jobpilot-ai/actions/runs/45299118537)

### F2-T05 — Persistência e rotas de matching (2026-11-24)

- A migração `000000000006` cria `job_matches`, com uma linha por candidato,
  vaga e versão. O recálculo usa upsert e preserva versões anteriores.
  [Modelo de dados](docs/data-model.md)
- As rotas calculam, listam o ranking filtrável e consultam detalhes com
  evidências. O cálculo usa a descrição quando a vaga ainda não possui
  requisitos persistidos. [Contrato de matching](docs/api.md#matching)
- Ruff e formatação passaram. A suíte com PostgreSQL passou com 437 testes,
  incluindo três novos. Cobertura de linhas de 97,14% em `app` e 95,14%
  nos serviços.

### F2-T06 — Golden set e avaliação do matching (2026-11-24)

- Curadoria de 34 vagas reais do Djinni, com descrições técnicas expurgadas
  em inglês e adaptadas para português e rótulos manuais. A avaliação usa
  um perfil sintético de dados e backend. [Procedência](data/golden/README.md)
- A versão `deterministico-v1` obteve 99,24% de precisão, 67,53% de revocação
  e 86,48% de concordância ordinal. O script reproduz as métricas a partir
  do snapshot local. [Relatório gerado](docs/evaluation.md)
- Ruff e formatação passaram. A suíte com PostgreSQL passou com 440 testes,
  três novos. Cobertura de 97,14% em `app` e 95,14% nos serviços.

### F2-T07 — Decisão sobre embeddings multilíngues (2026-11-24 UTC)

- A avaliação da F2-T06 estabeleceu a linha de base determinística nas 34
  vagas. A adoção de embeddings foi adiada até que uma comparação demonstre
  ganho no ranking. [ADR 0012](docs/adr/0012-adiar-embeddings-multilingues.md)
- A suíte de partida passou com 440 testes em PostgreSQL. A entrega é documental.
  [Ficha da F2-T07](docs/tasks/FASE-02/F2-T07.md)

### F2-T08 — Documentação e relatório da fase (2026-11-24 UTC)

- Cadastro e importação extraem requisitos em PT-BR e EN. O matching avalia
  os filtros eliminatórios, persiste a versão do score com evidências e permite
  consultar o ranking e o detalhe por candidato. [Metodologia](docs/matching-methodology.md)
- O roteiro no Swagger UI liga essas etapas com dados fictícios, do cadastro da
  habilidade à consulta do ranking. [Roteiro da Fase 2](README.md#fluxo-da-fase-2)
- A avaliação local documenta 99,24% de precisão, 67,53% de revocação e 86,48%
  de concordância ordinal nas 34 vagas. Um perfil sintético e uma amostra de
  conveniência delimitam a interpretação das métricas.
  [Avaliação reproduzível](docs/evaluation.md)
- A adoção de embeddings fica condicionada a uma comparação que demonstre ganho.
  [ADR 0012](docs/adr/0012-adiar-embeddings-multilingues.md) · [Ficha da F2-T08](docs/tasks/FASE-02/F2-T08.md)

### F2-GATE — Validação de saída (2026-11-24 UTC)

- A ficha relaciona RF-07 a RF-09 aos testes de extração, score, persistência e
  filtros eliminatórios. O carregador confirmou `deterministico-v1` como
  versão ativa, e o golden set reproduziu as métricas publicadas.
  [Ficha do gate](docs/tasks/FASE-02/F2-GATE.md)
- A revisão `b1f6d28` passou com 440 testes em PostgreSQL, 97,14% de
  cobertura em `app` e 95,14% em `app/services`. Ruff, formatação e ciclo de
  migração passaram no CI da fase.
  [CI da fase](https://github.com/JoaumPdr/jobpilot-ai/actions/runs/45313001607)
- A fase foi integrada com histórico em `develop` no commit `d30f0fc`. Após
  a aprovação do CI em `develop`, a tag anotada `fase-02` foi publicada e
  conferida no mesmo commit.
  [PR #37](https://github.com/JoaumPdr/jobpilot-ai/pull/37) · [CI em `develop`](https://github.com/JoaumPdr/jobpilot-ai/actions/runs/45314777921) · [Tag `fase-02`](https://github.com/JoaumPdr/jobpilot-ai/tree/fase-02)

## Fase 3 — Camada LLM

### F3-T01 — Interface e configuração de provedores LLM (2026-11-25 UTC)

- O contrato `LLMProvider` recebe instruções e dados em campos separados e
  devolve texto bruto com as contagens de tokens informadas pelo provedor.
  A configuração seleciona o provedor falso ou o Ollama local.
- O adaptador Ollama limita a saída e repete apenas falhas transitórias, com
  espera crescente e limitada. As mensagens de erro preservam o código HTTP
  quando disponível e omitem o corpo da resposta. A chave configurada é
  mascarada pelo Pydantic. [API de chat do Ollama](https://docs.ollama.com/api/chat)
- A suíte com PostgreSQL passou de 440 para 461 testes, com 97,20% de
  cobertura em `app` e 95,14% em `app/services`. A validação do adaptador
  usou transporte simulado. [Ficha da F3-T01](docs/tasks/FASE-03/F3-T01.md)

### F3-T02 — Schemas de saída e prompts versionados (2026-11-25 UTC)

- A análise de vaga recebe um contrato Pydantic com UUID, requisitos, recomendação, explicação e evidências tipadas. O parser confere o UUID e registra a versão do prompt usado pela aplicação.
- O prompt `job-analysis-v1` direciona omissões e contradições para `unknown_requirements` e pede trechos literais da vaga e do perfil para sustentar as classificações. O JSON Schema anexado ao prompt é gerado pela aplicação. [Estratégia LLM](docs/llm-strategy.md)
- A suíte passou de 461 para 481 testes em PostgreSQL. A cobertura ficou em 97,25% em `app` e 95,14% em `app/services`. Os novos testes usam dados sintéticos e o provedor falso. [Ficha da F3-T02](docs/tasks/FASE-03/F3-T02.md)

### F3-T03 — Sanitização e defesa de entrada (2026-11-25 UTC)

- A descrição fica em um campo JSON da mensagem de usuário, com limite de 8.000 caracteres, normalização de quebras de linha e sinal de truncamento. O prompt `job-analysis-v2` documenta como interpretar a entrada parcial e os delimitadores.
- O perfil enviado pela preparação contém as habilidades pertinentes e ausências explícitas do matching, em nomes canônicos do catálogo local. A revisão usou dados sintéticos e um provedor falso para confirmar a separação entre a descrição, o perfil e a mensagem de sistema. [Estratégia LLM](docs/llm-strategy.md#delimitação-e-minimização-da-entrada)
- A suíte passou de 481 para 490 testes em PostgreSQL. A cobertura ficou em 97,28% em `app` e 95,34% em `app/services`. [Ficha da F3-T03](docs/tasks/FASE-03/F3-T03.md)

### F3-T04 — Cache e registro de custo (2026-11-25 UTC)

- O serviço reutiliza uma análise validada para o mesmo provedor, modelo, versão do prompt e mensagens. Um bloqueio transacional por chave evitou chamadas duplicadas no teste com duas sessões PostgreSQL. [Modelo de dados](docs/data-model.md#cache-de-análises-llm-llm_cache-f3-t04)
- Cada chamada ao provedor registra tokens, custo estimado em USD e latência. Resultados validados guardam suas métricas no cache, e falhas liberam o bloqueio para nova tentativa. [Estratégia LLM](docs/llm-strategy.md#cache-e-métricas)
- A suíte passou de 490 para 496 testes em PostgreSQL, com 97,36% de cobertura em `app` e 95,61% em `app/services`. O ciclo da migração `000000000007` passou em banco isolado. [Ficha da F3-T04](docs/tasks/FASE-03/F3-T04.md)

### F3-T05 — Serviço de análise de vaga (2026-11-25 UTC)

- O serviço confere o contrato e as evidências, move itens sem respaldo para `unknown_requirements` e gera o resumo a partir da classificação verificada. A gravação em `job_matches.llm_analysis` confere o snapshot e preserva o score determinístico.
- O prompt complementar permite uma tentativa de reparo para saída inválida ou vazia. O cache reutiliza também o resultado reparado, e a falha final fica registrada em log estruturado. [Estratégia LLM](docs/llm-strategy.md#serviço-de-análise-de-vaga)
- A suíte passou de 496 para 506 testes em PostgreSQL, com 97,47% de cobertura em `app` e 96,11% em `app/services`. A validação usou um provedor falso e dados sintéticos. [Ficha da F3-T05](docs/tasks/FASE-03/F3-T05.md)

### F3-T06 — Avaliação no golden set (2026-11-25 UTC)

- As 34 vagas foram avaliadas no Ollama local com Qwen2.5 1.5B. A revocação de afirmações de presença e ausência caiu de 71,88% para 39,38%. O score e a ordem do ranking permaneceram iguais.
- Foram 68 chamadas, com 12 saídas aceitas após reparo, 22 inválidas e tarifa total de USD 0. A latência mediana do serviço ficou em 24,23 s por vaga. [Medições por vaga](docs/evaluation.md#avaliação-com-llm)
- A grade selecionou score ≥ 0,80 e top-10 para o modo local sob demanda. O funil retém quatro das cinco vagas de alta compatibilidade e o matching determinístico segue como padrão. A suíte completa passou com 507 testes. [Ficha da F3-T06](docs/tasks/FASE-03/F3-T06.md)

### F3-T07 — Documentação e relatório da fase (2026-11-25 UTC)

- A camada LLM atende à análise estruturada do RF-10 por um serviço Python
  sob demanda. Provedor falso e Ollama local usam o mesmo contrato. O serviço
  delimita a entrada, verifica as evidências, permite um reparo e armazena a
  análise validada em cache e no snapshot de matching. [Fluxo de uso](README.md#fluxo-da-fase-3) · [Estratégia LLM](docs/llm-strategy.md)
- No golden set, o reparo recuperou a estrutura em 12 vagas. Essas análises
  ficaram sem acertos de presença ou ausência. A queda de revocação e a
  mediana de 24,23 s por vaga em CPU sustentam o matching determinístico como
  padrão e o uso local sob demanda com o funil avaliado. A tarifa de USD 0
  refere-se às chamadas dessa execução local. [Comparação e limites](docs/evaluation.md#revisão-das-evidências-e-decisão-de-uso)
- O encerramento da fase depende do gate `F3-GATE`. O roteiro de verificação
  usa o provedor falso no CI e reproduz a linha de base sem inferência.
  [Ficha da F3-T07](docs/tasks/FASE-03/F3-T07.md)

## Fases 4–7

*(A serem preenchidas conforme avanço das fases)*
