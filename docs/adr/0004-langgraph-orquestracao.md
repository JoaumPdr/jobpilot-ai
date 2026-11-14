# ADR 0004 — LangGraph como único framework de orquestração
- Data: 2026-11-14
- Status: aceito

## Contexto
A Fase 4 (MVP v0.1.0) exige orquestração de um pipeline: importar → normalizar → deduplicar → filtrar → match → analisar. É necessário escolher um framework de orquestração multiagente.

## Decisão
Adotar **LangGraph** como único framework de orquestração. Nós do grafo são finas camadas que chamam serviços existentes — nunca reimplementam lógica de negócio.

## Alternativas consideradas
- **CrewAI:** Framework popular, mas mais opinativo e com menos controle sobre o grafo de execução.
- **AutoGen:** Poderoso, mas com foco em conversação multiagente, não em pipelines determinísticos.
- **Orquestração customizada com Python puro:** Mais código boilerplate para gerenciar estado, retry e transições condicionais.

## Consequências
- Melhorias: Estado tipado, transições condicionais, retry integrado, persistência de execução (`pipeline_runs`), integração com LangChain ecosystem.
- Piores: Dependência de um framework específico; curva de aprendizado para novos desenvolvedores.
- Revisitar: Se houver necessidade de múltiplos frameworks de orquestração, reavaliar (fora de escopo conforme PLANO.md §2.3).
