# Changelog

## Em desenvolvimento — Fase 3

### Adicionado

- Interface de provedores LLM com adaptador falso para testes e Ollama local sob demanda.
- Análise de vaga com prompts versionados, entrada delimitada, validação de evidências e uma tentativa de reparo para saída inválida ou vazia.
- Cache de análises validadas em PostgreSQL e registro de tokens, custo estimado e latência por chamada.
- Avaliação comparativa no golden set com custo e latência por vaga e um funil para análise local. O matching determinístico segue como padrão.

## [fase-02] — 2026-11-24

### Adicionado

- Taxonomia versionada de 184 habilidades e extração de requisitos com aliases em inglês e português, tipo e evidências da descrição.
- Filtros eliminatórios por modalidade, localização, empresa e habilidades obrigatórias, aplicados antes do cálculo do score.
- Score determinístico explicável e versionado, com cálculo, detalhe persistido e ranking filtrável pela API.
- Golden set de 34 vagas expurgadas e rotuladas, avaliação offline reproduzível e roteiro de matching pelo Swagger UI.

## [fase-01] — 2026-11-19

### Adicionado

- Cadastro e edição do perfil com preferências, habilidades e experiências.
- Cadastro manual e importação de vagas por CSV com relatório por linha, reimportação idempotente e revisão de duplicatas.
- Listagem de vagas com filtros combináveis e paginação. Vagas arquivadas e duplicatas confirmadas ficam ocultas por padrão.
- Arquivamento de vagas e acompanhamento de candidaturas com atalho para salvar, validação de transições e histórico.
- Teste de ponta a ponta em PostgreSQL e limites de cobertura no CI de 70% global e 85% nos serviços.
- Roteiro prático no README e referências do contrato HTTP e do modelo de dados.

## [fase-00] — 2026-11-14

### Adicionado

- Estrutura inicial da API FastAPI com verificação de saúde, PostgreSQL via Docker Compose e migrações Alembic.
- Ambiente gerenciado com `uv`, validações locais, GitHub Actions e documentação de arquitetura e privacidade.

[fase-02]: https://github.com/JoaumPdr/jobpilot-ai/tree/fase-02
[fase-01]: https://github.com/JoaumPdr/jobpilot-ai/tree/fase-01
[fase-00]: https://github.com/JoaumPdr/jobpilot-ai/tree/fase-00
