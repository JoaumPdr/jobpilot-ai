# ADR 0010 — Tipo de chave primária: UUID
- Data: 2026-11-13
- Status: aceito

## Contexto
É necessário decidir o tipo de chave primária para todas as tabelas do banco de dados. As opções são:
- Inteiro (serial/identity): simples, performático, mas sequencial e previsível.
- UUID: único globalmente, não sequencial, facilita fusão de dados e não vaza quantidade de registros.

## Decisão
Adotar **UUID** como tipo de chave primária (`id`) para todas as tabelas, usando `sqlalchemy.dialects.postgresql.UUID(as_uuid=True)` com geração via `uuid.uuid4`.

## Alternativas consideradas
- **Inteiro (serial/identity):**
  - Prós: Menor armazenamento, índices menores, ligeiramente mais performático.
  - Contras: IDs sequenciais previsíveis (risco de enumeração), dificuldade em mesclar dados de fontes distintas, vazamento de informações de volume.
- **UUID (escolhido):**
  - Prós: Único globalmente, não sequencial, seguro contra enumeração, facilita integração com fontes externas.
  - Contras: Maior armazenamento (16 bytes vs 4-8), índices maiores, levemente menos performático.

## Consequências
- Melhorias: Segurança contra enumeração de IDs, facilidade de mesclar dados, compatibilidade com futuras fontes externas.
- Pioras: Levemente maior uso de disco e memória para índices.
- Revisitar: Se houver problemas de desempenho em tabelas grandes, avaliar BigInteger com seqüências separadas por tenant.
