# ADR 0007 — Single-user no MVP; `candidate_id` mantido nas tabelas
- Data: 2026-11-14
- Status: aceito

## Contexto
O modelo de dados sugere multiusuário (tabela `candidates`), mas o plano não inclui autenticação no MVP. É necessário decidir se o MVP suporta um ou múltiplos usuários.

## Decisão
Adotar **single-user local para o MVP**, mantendo `candidate_id` em todas as tabelas relevantes para facilitar futura migração para multiusuário sem autenticação.

## Alternativas consideradas
- **Multiusuário com autenticação:** Requer login, sessões, controle de acesso por usuário. Adiado para pós-v1.0.
- **Single-user sem `candidate_id`:** Simplificaria o MVP mas dificultaria a migração futura.

## Consequências
- Melhorias: MVP mais simples, sem necessidade de gerenciar senhas/tokens, foco nas regras de negócio principais.
- Piores: Não suporta múltiplos usuários simultâneos no MVP.
- Revisitar: Autenticação e multiusuário são decisões para pós-v1.0 (fora de escopo conforme PLANO.md §2.3).
