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

**Fase 0 — Fundação** (em andamento)

Roadmap:
- [x] Fase 0: Fundação (repo, CI, Docker, FastAPI `/health`, Alembic, docs-base)
- [ ] Fase 1: Núcleo sem IA (perfil, vagas, CSV, dedup, filtros, candidaturas)
- [ ] Fase 2: Matching (taxonomia, extração, score explicável, golden set)
- [ ] Fase 3: Camada LLM (provedor abstrato, cache, análise validada)
- [ ] Fase 4: Orquestração (LangGraph pipeline) → **MVP v0.1.0**
- [ ] Fase 5: Assistente de currículo → v0.2.0
- [ ] Fase 6: Dashboard e analytics → v0.3.0
- [ ] Fase 7: Hardening e release → **v1.0.0**

## Pré-requisitos

- **Python 3.12+** (gerenciado via [`uv`](https://docs.astral.sh/uv/))
- **Docker** e **Docker Compose** (para PostgreSQL)
- **Git**

## Instalação

```bash
# Clonar o repositório
git clone https://github.com/JoaumPdr/jobpilot-ai.git
cd jobpilot-ai

# Instalar dependências (cria .venv automaticamente)
uv sync
```

## Configuração

```bash
# Copiar exemplo de variáveis de ambiente
cp .env.example .env

# Editar .env com suas configurações
# (pelo menos DATABASE_URL para o PostgreSQL)
```

## Execução

```bash
# Subir o banco de dados
docker compose up -d

# Rodar migrações
uv run alembic upgrade head

# Iniciar a API
uv run uvicorn app.main:app --reload

# Acessar: http://localhost:8000/health
```

## Testes e Qualidade

```bash
# Testes
uv run pytest

# Lint e formatação
uv run ruff check
uv run ruff format

# Tipagem (quando adotada)
uv run mypy
```

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

- Estado vivo: [`docs/STATUS.md`](docs/STATUS.md)
- Instruções de execução: [`docs/ALETHE_INSTRUCOES.md`](docs/ALETHE_INSTRUCOES.md)
- Guia de docs e Git: [`docs/GUIA_DOCS_E_GIT.md`](docs/GUIA_DOCS_E_GIT.md)
- Backlog: [`docs/BACKLOG.md`](docs/BACKLOG.md)
- Plano mestre: [`docs/PLANO.md`](docs/PLANO.md)

## Privacidade e Fontes

Ver [`docs/privacy-and-sources.md`](docs/privacy-and-sources.md).

## Licença

[MIT](LICENSE) — © 2026 João Pedro