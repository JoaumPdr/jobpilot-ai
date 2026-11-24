# ADR 0012 — Adiar a adoção de embeddings multilíngues

- Data — 2026-11-24 (UTC)
- Status — aceito

## Contexto

A F2-T07 condiciona a adoção de embeddings multilíngues à demonstração de
ganho mensurável no golden set, conforme o [ADR 0006](0006-matching-deterministico.md).
A [avaliação da F2-T06](../evaluation.md) mede `deterministico-v1` em 34 vagas
com um único perfil sintético. A precisão da extração foi de 99,24%, a revocação
foi de 67,53% e a concordância ordinal do ranking foi de 86,48% em 355 pares.
A revocação aponta espaço para melhorar a extração. Para estimar o efeito de
embeddings no ranking, seria necessária uma medição comparativa.

## Decisão

Adiar a adoção de embeddings multilíngues e continuar usando `deterministico-v1`
na Fase 2. O resultado disponível estabelece a linha de base para uma futura
comparação. [Relatório de avaliação](../evaluation.md)

## Alternativas consideradas

- **Incorporar o sinal semântico.** Poderia reconhecer relações além dos aliases
  cadastrados. Seu efeito no ranking ainda não foi medido, e a adoção exigiria
  operar e versionar um componente adicional.
- **Adiar a adoção.** Preserva a explicabilidade e a reprodução local do score
  atual. Relações semânticas fora da taxonomia podem continuar sem cobertura.

## Consequências

A decisão mantém o score baseado nas regras e nas evidências já documentadas.
Para reavaliá-la, comparar a linha de base com uma variante semântica nas mesmas
vagas e com os mesmos rótulos. Documentar a diferença de concordância ordinal
no conjunto e por idioma, além do custo e da latência da variante.
