# Changelog

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

[fase-01]: https://github.com/JoaumPdr/jobpilot-ai/tree/fase-01
[fase-00]: https://github.com/JoaumPdr/jobpilot-ai/tree/fase-00
