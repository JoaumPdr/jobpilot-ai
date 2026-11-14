# ADR 0008 — Gerenciamento de ambiente e dependências com uv
- Data: 2026-11-10
- Status: aceito

## Contexto
Necessidade de um gerenciador de ambiente e dependências robusto, reproduzível e que suporte fluxos de desenvolvimento modernos, incluindo suporte a grupos de dependências (produção vs desenvolvimento) e travamento de versões.

## Decisão
Adotar o **uv** como o único gerenciador de ambiente e dependências do projeto JobPilot AI.

## Alternativas consideradas
- `pip` + `venv` + `requirements.txt`: Problemas com resolução de dependências, falta de grupos e travamento de versões robusto.
- `poetry`: Ótimo, mas o `uv` oferece performance significativamente superior em resolução e instalação.

## Consequências
- Instalação e sincronização do ambiente via `uv sync`.
- Gerenciamento de pacotes via `uv add`/`uv remove`.
- Execução de comandos via `uv run`.
- `uv.lock` é versionado e deve ser sincronizado com `pyproject.toml`.
