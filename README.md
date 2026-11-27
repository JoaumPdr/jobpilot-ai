# JobPilot AI

**Repositório:** https://github.com/JoaumPdr/jobpilot-ai

[![CI](https://github.com/JoaumPdr/jobpilot-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/JoaumPdr/jobpilot-ai/actions/workflows/ci.yml)

Assistente pessoal para buscar, analisar e gerir candidaturas a vagas. Desenvolvido como demonstração de engenharia de software, engenharia de dados e **orquestração multiagente** (com apoio da Alethe).

## Princípios

1. **O sistema recomenda e prepara; o usuário revisa e decide.**
2. **Nunca** automatizar envio de candidatura.
3. **Nunca** inventar experiência, competência ou fato no currículo.
4. Respostas de LLM são **dados não confiáveis** — sempre validar.
5. Não usar LLM onde uma função Python resolve melhor.

## Status Atual

**Fase 1 — Núcleo sem IA** concluída e integrada em `develop`. A API permite cadastrar perfil, importar e filtrar vagas, revisar duplicatas e acompanhar candidaturas. Veja o [roteiro de uso](#fluxo-da-fase-1) e o [marco `fase-01`](https://github.com/JoaumPdr/jobpilot-ai/tree/fase-01).

**Fase 2 — Matching** concluída e integrada em `develop`. A API calcula compatibilidade com evidências e permite consultar o ranking por candidato. [Roteiro de matching](#fluxo-da-fase-2) · [Avaliação no golden set](docs/evaluation.md) · [Marco `fase-02`](https://github.com/JoaumPdr/jobpilot-ai/tree/fase-02)

**Fase 3 — Camada LLM** concluída e integrada em `develop`. O serviço Python gera análises opcionais com evidências verificadas e cache em PostgreSQL. O matching determinístico continua como padrão. [Uso da análise](#fluxo-da-fase-3) · [Comparação no golden set](docs/evaluation.md#avaliação-com-llm) · [Marco `fase-03`](https://github.com/JoaumPdr/jobpilot-ai/tree/fase-03)

Roadmap:
- [x] Fase 0: Fundação (repo, CI, Docker, FastAPI `/health`, Alembic, docs-base)
- [x] Fase 1: Núcleo sem IA (perfil, vagas, CSV, dedup, filtros, candidaturas)
- [x] Fase 2: Matching (taxonomia, extração, score explicável, golden set)
- [x] Fase 3: Camada LLM (provedor abstrato, cache, análise validada)
- [ ] Fase 4: Orquestração (LangGraph pipeline) → **MVP v0.1.0**
- [ ] Fase 5: Assistente de currículo → v0.2.0
- [ ] Fase 6: Dashboard e analytics → v0.3.0
- [ ] Fase 7: Hardening e release → **v1.0.0** com distribuição local por Docker Compose, interface no navegador, configuração documentada, dados persistentes e backup/restauração testados em instalação limpa

## Pré-requisitos

- **Python 3.12+** (gerenciado via [`uv`](https://docs.astral.sh/uv/))
- **Docker** e **Docker Compose** (para PostgreSQL)
- **Git**

## Instalação

```bash
# Clonar o repositório
git clone https://github.com/JoaumPdr/jobpilot-ai.git
cd jobpilot-ai

# Instalar as versões do lockfile, incluindo o LangGraph do pipeline local
uv sync --locked
```

## Configuração

```bash
# Copiar exemplo de variáveis de ambiente
cp .env.example .env

# Editar .env com suas configurações
# (pelo menos DATABASE_URL para o PostgreSQL)

# Opcional: banco de testes isolado.
# Se omitido, os testes usam DATABASE_URL com o sufixo "_test"
# (ex.: jobpilot_test), recriado automaticamente pela suíte.
# TEST_DATABASE_URL=postgresql+psycopg://jobpilot:jobpilot@localhost:5433/jobpilot_test
```

### Provedor LLM opcional

Deixe `LLM_PROVIDER` vazio para manter o LLM desativado. Use `LLM_PROVIDER=fake`
para obter uma resposta fixa sem rede ou `LLM_PROVIDER=ollama` para usar um modelo
instalado no Ollama. No segundo caso, defina `LLM_MODEL` no `.env` com o nome do
modelo local e inicie o Ollama com `OLLAMA_NO_CLOUD=1` no ambiente do servidor.
A conexão usa `127.0.0.1` e a porta `LLM_OLLAMA_PORT`, com padrão `11434`.
A API local dispensa chave. [Configuração do Ollama](https://docs.ollama.com/faq#how-do-i-disable-ollamas-cloud-features)

`LLM_TIMEOUT` define o timeout de rede de cada tentativa. `LLM_RETRIES` limita
as tentativas adicionais após uma falha transitória, e `LLM_MAX_TOKENS` limita
a geração de cada resposta. A inferência local dispensa cobrança por chamada.
`LLM_BUDGET_USD` fica reservado para o controle de custo do futuro pipeline.
[Estratégia LLM](docs/llm-strategy.md)

## Execução

```bash
# Subir o banco de dados
docker compose up -d

# Rodar migrações
uv run alembic upgrade head

# Iniciar a API
uv run uvicorn app.main:app --reload

# Acessar http://localhost:8000/docs para usar a API
```

## Fluxo da Fase 1

Com a API em execução, abra [http://localhost:8000/docs](http://localhost:8000/docs).
Em cada rota, clique em **Try it out**, preencha os campos e clique em **Execute**.
Use um banco local de desenvolvimento para os exemplos fictícios abaixo.

1. **Crie o perfil** em `POST /candidates` com `{"name":"Ana Silva","resume_text":"Experiência com análise de dados."}`.
   A resposta `201` fornece o `id` que você usará como `candidate_id`. Em
   `PUT /candidates/{candidate_id}/preferences`, envie
   `{"desired_titles":["Analista de dados"],"work_modes":["remoto"]}`.
   A [referência da API](docs/api.md#candidato) também explica como editar
   o perfil, cadastrar habilidades e registrar experiências.

2. **Importe vagas.** Salve este conteúdo como `vagas.csv` em UTF-8.

   ```csv
   title,company,description,url,work_mode
   Analista de dados,Empresa X,Relatórios,https://example.com/jobs/demo-fase-1-remoto,remoto
   Analista de dados,Empresa Y,Painéis,https://example.com/jobs/demo-fase-1-presencial,presencial
   ```

   Em `POST /jobs/import`, escolha o arquivo em `file` e digite
   `demo-fase-1` em `source`. Na primeira importação em um catálogo vazio,
   confira `inserted: 2` e `rejected: 0`. Envie o mesmo arquivo novamente e
   confira `inserted: 0` e `duplicates: 2`. O relatório identifica linhas
   inválidas em `errors`. Para outras colunas, veja o [formato CSV](docs/import-csv.md).
   Para inserir uma única vaga, use [`POST /jobs`](docs/api.md#post-jobs).

3. **Filtre o catálogo.** Em `GET /jobs`, use `q=Analista de dados`,
   `work_mode=remoto` e `source=demo-fase-1`. Copie o `id` da vaga da
   Empresa X como `job_id`. Preencha os filtros com os valores desejados
   mesmo quando já tiver registrado preferências no perfil. Se precisar
   revisar possíveis repetições, use [`GET /jobs/duplicates`](docs/api.md#revisão-de-duplicatas)
   e confirme a referência após comparar as vagas.

4. **Salve e acompanhe a candidatura.** Em
   `POST /candidates/{candidate_id}/jobs/{job_id}/save`, informe os dois
   identificadores. A resposta `201` contém o `id` da candidatura em
   `salva`. Use esse valor como `application_id` em
   `PATCH /candidates/{candidate_id}/applications/{application_id}`.
   Envie `{"status":"planejada"}` e, depois que enviar a candidatura por
   conta própria, registre `{"status":"aplicada"}`.

5. **Confira o histórico.** Em
   `GET /candidates/{candidate_id}/applications/{application_id}`, verifique
   a sequência `salva` → `planejada` → `aplicada` em `status_history` e
   a data em `applied_at`. Para encontrar essas vagas no catálogo, combine
   `candidate_id` e `application_status=aplicada` em `GET /jobs`.
   Use [`POST /jobs/{job_id}/archive`](docs/api.md#post-jobsjob_idarchive)
   para ocultar uma vaga da listagem padrão e manter seu histórico.

Consulte a [API](docs/api.md), o [modelo de dados](docs/data-model.md) e o
[changelog](CHANGELOG.md) para mais detalhes sobre a fase.

## Fluxo da Fase 2

No Swagger UI, use o `candidate_id` de um perfil fictício recém-criado conforme
o passo 1 do fluxo da Fase 1. Para o exemplo, o perfil começa sem habilidades.

1. **Declare a habilidade.** Em `POST /candidates/{candidate_id}/skills`,
   envie `{"canonical_name":"Postgres"}`.
2. **Cadastre a vaga.** Em `POST /jobs`, envie o JSON abaixo e copie
   `job.id` da resposta como `job_id`.

   ```json
   {
     "title": "Analista de Dados",
     "company": "Equipe A",
     "url": "https://example.com/jobs/demo-fase-2",
     "description": "Requisitos: PostgreSQL e Docker. Diferenciais: Kubernetes.",
     "work_mode": "remoto",
     "location": "São Paulo"
   }
   ```

3. **Calcule a compatibilidade.** Em `POST /candidates/{candidate_id}/matches/{job_id}`,
   envie `{"confirmed_absent":["Docker"]}` para registrar essa ausência
   no cálculo. Na resposta, `scoring_version` é `deterministico-v1` e
   `match_score` representa 0,35. Confira em `analysis` PostgreSQL em `met`
   por alias, Docker em `absent` e Kubernetes em `unconfirmed`.
4. **Consulte o resultado persistido.** Em `GET /candidates/{candidate_id}/matches/{job_id}`,
   veja os requisitos e os trechos de evidência. Em
   `GET /candidates/{candidate_id}/matches`, use `work_mode=remoto` para listar
   o ranking de avaliações calculadas para vagas remotas.

O golden set usa descrições expurgadas e um perfil sintético. Confira da
raiz do repositório se o relatório corresponde à avaliação local.

```bash
uv run python -m scripts.evaluate_matching --check
```

[Rotas de matching](docs/api.md#matching) · [Metodologia](docs/matching-methodology.md) · [Resultados e limitações](docs/evaluation.md)

## Fluxo da Fase 3

A análise é acionada sob demanda pelo serviço Python. Calcule o matching e
use a versão retornada pela API. Configure o Ollama como provedor, aplique as
migrações e execute a função abaixo a partir da raiz do repositório, em um
ambiente Python iniciado com `uv run python`. Passe como argumentos os UUIDs
e a versão do matching. O exemplo grava a análise no banco configurado.
[Fluxo da Fase 2](#fluxo-da-fase-2) · [Configuração do provedor](#provedor-llm-opcional)

```python
from uuid import UUID

from app.core.config import settings
from app.core.database import SessionLocal
from app.llm.providers import build_llm_provider
from app.repositories.matching import MatchRepository
from app.services.job_analysis import JobAnalysisService
from app.services.llm_cache import LLMCacheService


def analisar_vaga(candidate_id: str, job_id: str, scoring_version: str):
    provider = build_llm_provider(settings)
    if provider is None:
        raise ValueError("Configure LLM_PROVIDER para executar a análise.")

    with SessionLocal() as session:
        service = JobAnalysisService(
            MatchRepository(session), LLMCacheService(provider)
        )
        return service.analyze(UUID(candidate_id), UUID(job_id), scoring_version)
```

A função devolve `prompt_version` e `analysis`. O serviço confere a saída,
tenta um reparo quando a resposta é inválida ou vazia e registra falhas que
impedem a geração. A seleção de vagas por score ≥ 0,80 e top-10 é o funil medido
para uso local sob demanda. A chamada acima analisa uma vaga por vez.

Para verificar o fluxo com dados sintéticos e respostas controladas, execute
os testes de integração com PostgreSQL. Eles cobrem cache, reparo e validação
das evidências sem uma chamada real ao modelo.

```bash
uv run pytest tests/db/test_job_analysis.py tests/db/test_llm_cache.py
```

[Contrato, cache e reprodução da avaliação](docs/llm-strategy.md) · [Medições e escolha do funil](docs/evaluation.md#funil-de-custo)

## Executar um lote pela API

No Swagger UI em `/docs`, abra `POST /pipeline/runs`, informe o UUID de um
candidato cadastrado, um novo `run_id` e um arquivo CSV em UTF-8. Para experimentar
o fluxo determinístico, mantenha `llm_enabled=false`. Use vagas novas para que
o lote contenha itens após a deduplicação.

Consulte `GET /pipeline/runs/{id}` com o mesmo `run_id` para recuperar o estado,
os erros por vaga e a lista `recommendations_for_review`. Salvar uma vaga é
uma escolha explícita do usuário. [Contrato e exemplo em PowerShell](docs/api.md#pipeline)

## Testes e Qualidade

```bash
# Testes
uv run pytest

# Lint e formatação
uv run ruff check
uv run ruff format --check

# Tipagem (quando adotada)
uv run mypy
```

Os testes de integração usam um banco **isolado** (`jobpilot_test`): a fixture
recria o banco, aplica `alembic upgrade head` e o remove no fim. Se
`TEST_DATABASE_URL` não estiver definida, o nome é derivado de `DATABASE_URL`
acrescentando `_test`; a suíte aborta se o alvo não terminar em `_test` ou for
igual ao banco de desenvolvimento.

## Arquitetura Resumida

```
API (FastAPI) → Serviços → Repositórios → PostgreSQL
                    ↓
              Orquestração (LangGraph)
                    ↓
              Provedores Externos (LLM, embeddings)
```

Ver [`design.md`](design.md) para detalhes.

## Estrutura de Pastas

```
jobpilot-ai/
├── app/                    # Código da aplicação
│   ├── api/routes/         # Rotas finas
│   ├── core/               # Config, logging, erros
│   ├── models/             # SQLAlchemy
│   ├── schemas/            # Pydantic
│   ├── repositories/       # Acesso a dados
│   ├── services/           # Regras de negócio
│   ├── matching/           # Taxonomia, extração, score
│   ├── llm/                # Interface, provedores, prompts, cache
│   ├── orchestration/      # State, nodes, graph (LangGraph)
│   └── main.py
├── migrations/             # Alembic
├── prompts/                # Prompts versionados
├── data/                   # Taxonomia, golden set (anonimizado)
├── tests/                  # Testes organizados por camada
├── docs/                   # Documentação do projeto
├── scripts/                # Scripts utilitários
├── docker-compose.yml
├── .env.example
├── pyproject.toml
├── uv.lock
├── .python-version
└── README.md · RELATORIO.md · design.md
```

## Como Contribuir / Retomar

- Ponto de entrada para agentes: [`AGENTS.md`](AGENTS.md)
- Estado vivo: [`docs/STATUS.md`](docs/STATUS.md)
- Instruções de execução: [`docs/ALETHE_INSTRUCOES.md`](docs/ALETHE_INSTRUCOES.md)
- Guia de docs e Git: [`docs/GUIA_DOCS_E_GIT.md`](docs/GUIA_DOCS_E_GIT.md)
- Backlog: [`docs/BACKLOG.md`](docs/BACKLOG.md)
- Plano mestre: [`docs/PLANO.md`](docs/PLANO.md)

## Privacidade e Fontes

Ver [`docs/privacy-and-sources.md`](docs/privacy-and-sources.md).

## Licença

[MIT](LICENSE) — © 2026 João Pedro
