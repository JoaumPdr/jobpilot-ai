# Avaliação do matching determinístico

Versão de score: `deterministico-v1`. Amostra: 34 vagas. Revisão da fonte: `b56a6054c10f1266a141e37c8df66c79ff2863af`.
[Procedência, licenciamento e protocolo](../data/golden/README.md)
[Metodologia do score](matching-methodology.md)

## Extração

Métricas micro por par de habilidade e tipo do requisito. Um tipo incorreto conta como falso positivo no tipo previsto e falso negativo no esperado.

| Segmento | VP | FP | FN | Precisão | Revocação | F1 |
|---|---:|---:|---:|---:|---:|---:|
| Total | 131 | 1 | 63 | 99,24% | 67,53% | 80,37% |
| en | 63 | 1 | 37 | 98,44% | 63,00% | 76,83% |
| pt-BR | 68 | 0 | 26 | 100,00% | 72,34% | 83,95% |

## Ranking

Compatibilidade manual: 5 alta, 14 média e 15 baixa.
Vagas com score: 29 de 34.

Concordância ordinal: **86,48%** em 355 pares comparáveis. Foram 300 concordantes, 14 empatados e 41 divergentes.
Pares com o mesmo rótulo ficam fora da métrica. Empates de score valem meio acerto. Vagas sem score ficam ao final.

## Evidências e reprodução

Trechos literais na descrição: 132 de 132 requisitos extraídos.
A avaliação roda localmente e faz zero chamadas a modelos externos. Da raiz do repositório, use `--check` para verificar o relatório. A opção `--timing` mede a média e a mediana de extração mais score por vaga.

```powershell
uv run python -m scripts.evaluate_matching --check --timing
```

Para regenerar o arquivo após uma mudança de dados ou de apresentação, execute `uv run python -m scripts.evaluate_matching`.

## Interpretação e limites

A precisão indica a proporção de acertos entre os requisitos previstos. A revocação indica a proporção de requisitos rotulados que o extrator recuperou. A concordância ordinal mede a ordem relativa das vagas, em pares com rótulos distintos.

A amostra é de conveniência e avalia um único perfil sintético. A porção PT-BR é adaptada de anúncios em inglês. A medição cobre a extração e o score em memória, com as vagas elegíveis. A API, a persistência e as regras eliminatórias são exercitadas pela suíte de testes.

Este resultado estabelece a linha de base determinística. Uma comparação com uma variante semântica nas mesmas vagas é necessária para medir o ganho. [Decisão sobre embeddings multilíngues](adr/0012-adiar-embeddings-multilingues.md)
