# ADR 0003 — PostgreSQL como único datastore
- Data: 2026-11-14
- Status: aceito

## Contexto
O JobPilot AI precisa persistir dados de candidatos, vagas, candidaturas, matching, pipeline e cache de LLM. É necessário escolher o banco de dados principal.

## Decisão
Adotar **PostgreSQL** como único datastore da aplicação, utilizando **JSONB** para campos que exigem flexibilidade de esquema (ex.: `education`, `languages`, `knockout_rules`, `job_skills` evidências).

## Alternativas consideradas
- **MySQL/MariaDB:** Bom banco relacional, mas JSONB e suporte a consultas avançadas são mais maduros no PostgreSQL.
- **MongoDB:** Flexível para documentos, mas perderíamos integridade relacional e transações ACID importantes para dados financeiros e de candidatura.
- **SQLite:** Simples, mas não adequado para concorrência e produção.

## Consequências
- Melhorias: Integridade relacional, transações ACID, JSONB para esquemas dinâmicos, suporte a full-text search (português), ecossistema maduro.
- Piores: Requer servidor de banco separado (Docker Compose em desenvolvimento).
