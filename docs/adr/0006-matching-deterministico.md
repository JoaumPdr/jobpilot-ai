# ADR 0006 — Matching determinístico primeiro; embeddings só se golden set provar ganho
- Data: 2026-11-14
- Status: aceito

## Contexto
A Fase 2 (Matching) exige cálculo de score de compatibilidade entre candidatos e vagas. É necessário decidir entre abordagem determinística (baseada em taxonomia de skills) e semântica (embeddings).

## Decisão
Adotar **matching determinístico primeiro**, com:
- Taxonomia de skills versionada em `data/` (categorias, aliases PT/EN).
- Extrator determinístico de requisitos (seções obrigatórias/desejáveis, palavras-gatilho).
- Filtros eliminatórios (knockouts) separados do score.
- Score ponderado com pesos versionados (`scoring_version`).
- Embeddings multilíngues apenas como opcional, se o golden set (Fase 2-T06) mostrar ganho mensurável.

## Alternativas consideradas
- **Embeddings desde o início:** Maior complexidade, custo de API, dificuldade de explicar por que um score foi gerado.
- **Apenas determinístico:** Pode perder nuances semânticas, mas é mais barato e explicável.

## Consequências
- Melhorias: Baixo custo, explicabilidade obrigatória (atendidos/ausentes/não confirmados/evidências), reproduzibilidade via `scoring_version`.
- Piores: Pode não capturar similaridade semântica entre skills relacionadas não mapeadas na taxonomia.
- Revisitar: Fase 2-T07 condicional — adotar embeddings apenas se o golden set provar ganho.
