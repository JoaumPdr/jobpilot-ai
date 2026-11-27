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

<!-- llm-evaluation -->

## Avaliação com LLM

Ollama `0.40.18`, modelo `qwen2.5:1.5b`, digest `65ec06548149b04c096a120e4a6da9d4017ea809c91734ea5631e89f96ddc57b`. Perfil sintético, 34 vagas, banco novo, cache inicialmente vazio e limite de 640 tokens por resposta. Instruções `job-analysis-v2` e reparo `job-analysis-repair-v1`.

A comparação usa afirmações de presença ou ausência por habilidade, com referência nos rótulos manuais e nos fatos do perfil. Relações aproximadas entram como sem confirmação. Em falha do LLM, a variante mantém as afirmações determinísticas.

| Variante | VP | FP | FN | Precisão | Revocação |
|---|---:|---:|---:|---:|---:|
| Determinístico | 115 | 0 | 45 | 100,00% | 71,88% |
| Determinístico + LLM | 63 | 0 | 97 | 100,00% | 39,38% |

A primeira tentativa foi válida em 0 vagas, e o reparo produziu saída válida em 12. Houve 22 saídas inválidas e 0 falhas do provedor. O score e a ordem do ranking foram preservados.

Mediana determinística de 0.514 ms e mediana do serviço LLM de 24234.5 ms. Foram 68 chamadas, com custo conhecido de USD 0 e 0 vagas com custo indisponível.

| Vaga | Score | Análise | VP base → +LLM | Chamadas | Tokens | USD | Provedor (ms) | Serviço (ms) |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| GS-001 | 0.2500 | saída inválida | 2 → 2 | 2 | 2452 | 0 | 56274 | 56338.1 |
| GS-002 | 0.0000 | saída inválida | 1 → 1 | 2 | 2301 | 0 | 26304 | 26324.8 |
| GS-003 | — | saída inválida | 0 → 0 | 2 | 2244 | 0 | 17098 | 17115.6 |
| GS-004 | 0.6667 | saída inválida | 3 → 3 | 2 | 2871 | 0 | 40967 | 40980.8 |
| GS-005 | 0.0000 | saída inválida | 1 → 1 | 2 | 2827 | 0 | 42814 | 42826.5 |
| GS-006 | 0.0000 | saída inválida | 2 → 2 | 2 | 2013 | 0 | 7021 | 7033.1 |
| GS-007 | 0.7778 | reparo | 9 → 0 | 2 | 2706 | 0 | 33324 | 33356.7 |
| GS-008 | — | reparo | 0 → 0 | 2 | 3137 | 0 | 67136 | 67161.5 |
| GS-009 | 0.4545 | saída inválida | 8 → 8 | 2 | 2828 | 0 | 40602 | 40614.2 |
| GS-010 | 0.6667 | reparo | 9 → 0 | 2 | 2763 | 0 | 38261 | 38281.7 |
| GS-011 | — | reparo | 0 → 0 | 2 | 2720 | 0 | 35380 | 35401.0 |
| GS-012 | 1.0000 | saída inválida | 1 → 1 | 2 | 2360 | 0 | 18494 | 18506.1 |
| GS-013 | 0.7000 | saída inválida | 4 → 4 | 2 | 2374 | 0 | 20222 | 20234.4 |
| GS-014 | 0.7000 | reparo | 10 → 0 | 2 | 2816 | 0 | 36364 | 36382.7 |
| GS-015 | 0.7500 | saída inválida | 8 → 8 | 2 | 2566 | 0 | 28176 | 28188.5 |
| GS-016 | 0.0000 | saída inválida | 1 → 1 | 2 | 2263 | 0 | 19436 | 19448.8 |
| GS-017 | 0.6000 | reparo | 7 → 0 | 2 | 2644 | 0 | 33187 | 33209.4 |
| GS-018 | 0.6667 | reparo | 3 → 0 | 2 | 2462 | 0 | 25096 | 25117.9 |
| GS-019 | 1.0000 | reparo | 1 → 0 | 2 | 2183 | 0 | 12732 | 12751.7 |
| GS-020 | — | saída inválida | 0 → 0 | 2 | 2263 | 0 | 17567 | 17581.7 |
| GS-021 | 1.0000 | reparo | 3 → 0 | 2 | 2179 | 0 | 15319 | 15347.0 |
| GS-022 | 0.8000 | reparo | 3 → 0 | 2 | 2277 | 0 | 23329 | 23351.1 |
| GS-023 | 0.7286 | saída inválida | 2 → 2 | 2 | 2786 | 0 | 42656 | 42669.7 |
| GS-024 | 0.9091 | saída inválida | 5 → 5 | 2 | 2303 | 0 | 18887 | 18900.3 |
| GS-025 | 0.8500 | saída inválida | 2 → 2 | 2 | 2278 | 0 | 19152 | 19164.8 |
| GS-026 | 0.2500 | saída inválida | 2 → 2 | 2 | 2489 | 0 | 27009 | 27023.6 |
| GS-027 | 0.3500 | saída inválida | 2 → 2 | 2 | 2026 | 0 | 5967 | 5979.7 |
| GS-028 | 0.3077 | saída inválida | 5 → 5 | 2 | 2816 | 0 | 46074 | 46088.0 |
| GS-029 | 0.7692 | saída inválida | 5 → 5 | 2 | 2377 | 0 | 22947 | 22960.6 |
| GS-030 | 1.0000 | reparo | 3 → 0 | 2 | 2383 | 0 | 22193 | 22215.5 |
| GS-031 | 1.0000 | reparo | 4 → 0 | 2 | 2405 | 0 | 23111 | 23133.9 |
| GS-032 | 0.3158 | saída inválida | 7 → 7 | 2 | 2644 | 0 | 31906 | 31921.5 |
| GS-033 | — | saída inválida | 0 → 0 | 2 | 2237 | 0 | 15573 | 15584.6 |
| GS-034 | 0.0000 | saída inválida | 2 → 2 | 2 | 2327 | 0 | 19262 | 19273.9 |

### Funil de custo

A grade aplica o limiar de score e quebra empates pelo identificador da vaga. A escolha maximiza a retenção das vagas de alta compatibilidade e prefere menos consultas, limiar maior e top-N menor em caso de empate.

| Limiar inclusivo | Top-N | Vagas selecionadas | Compatibilidade alta |
|---:|---:|---:|---:|
| 0.50 | 3 | 3 | 0 |
| 0.50 | 5 | 5 | 2 |
| 0.50 | 10 | 10 | 4 |
| 0.60 | 3 | 3 | 0 |
| 0.60 | 5 | 5 | 2 |
| 0.60 | 10 | 10 | 4 |
| 0.70 | 3 | 3 | 0 |
| 0.70 | 5 | 5 | 2 |
| 0.70 | 10 | 10 | 4 |
| 0.80 | 3 | 3 | 0 |
| 0.80 | 5 | 5 | 2 |
| 0.80 | 10 | 8 | 4 |

Funil do modo local sob demanda. Score **≥ 0.80** e **top-10**, com 8 vagas selecionadas e 4 rotuladas como alta. O teto é de 20 chamadas lógicas por execução, incluindo reparos. O matching determinístico segue como referência para a decisão.

A medição reflete uma execução local com um modelo e um perfil. A latência varia com a máquina, e o custo em USD refere-se à tarifa por chamada do provedor.

### Revisão das evidências e decisão de uso

A revisão manual conferiu o contrato, os trechos de evidência e a cobertura
dos rótulos em três análises aceitas após reparo. Cada análise ficou com zero
evidências de presença ou ausência. Os rótulos incluem Python e Terraform em
`GS-007`, SQL e Python em `GS-017` e Git e Bash em `GS-022`. O perfil sintético
declara todas essas habilidades. Os acertos da linha de base
foram 9, 7 e 3, respectivamente. [Rótulos e perfil sintético](../data/golden/matching.json)

As 12 análises aceitas cumpriram o contrato após o reparo e ficaram com zero
acertos de presença ou ausência. Os 63 acertos da variante com LLM vieram das
22 vagas em que a saída inválida levou à classificação determinística. A
precisão de 100% mede apenas as afirmações emitidas. A revocação captura a
perda de 52 acertos no conjunto, passando de 71,88% para 39,38%.

O matching determinístico fica como padrão. O funil de score ≥ 0,80 e top-10
fica reservado à análise local sob demanda. Ele seleciona oito vagas e retém
quatro das cinco de alta compatibilidade pelo rótulo manual. A retenção mede
a seleção para análise. A qualidade da saída nas vagas selecionadas depende
do modelo e das evidências que sobreviverem à validação. [Reprodução da avaliação](llm-strategy.md#reprodução-da-avaliação-local)
