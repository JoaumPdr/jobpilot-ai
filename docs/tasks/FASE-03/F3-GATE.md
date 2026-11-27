# F3-GATE — Gate de saída da Fase 3

- **Integração da fase** — `phase/03-camada-llm` → `develop`. [PR #46](https://github.com/JoaumPdr/jobpilot-ai/pull/46)
- **Estado** — concluído no merge `b7348cc`, marcado com a tag anotada `fase-03` (`492895f`). [Tag publicada](https://github.com/JoaumPdr/jobpilot-ai/tree/fase-03)
- **Revisões validadas** — `ac7713c` na partida e `7ecab9d` no PR da fase, com `develop` em `aa23972` como base.
- **Execução** — direta com `gpt-6.2-sol` e esforço `high`. Política Base e hook passivo confirmados.
- **Critérios** — [Backlog](../../BACKLOG.md#fase-3--camada-llm--branch-phase03-camada-llm--tag-fase-03) · [Plano mestre, §11](../../PLANO.md#11-fases-resultados-e-gates-de-saída)

| Critério | Evidência verificada |
|---|---|
| RF-10 | O serviço Python seleciona o matching persistido por candidato, vaga e versão. Confere o UUID, valida o contrato, verifica os trechos contra as fontes e grava `analysis` e `prompt_version` com o snapshot vigente. O teste confirma a persistência e a preservação do score. [Serviço](../../../app/services/job_analysis.py) · [Teste](../../../tests/db/test_job_analysis.py#L136) |
| Persistência de respostas válidas | A saída inválida ou vazia admite um reparo. O teste de falha final confere que o cache fica vazio e `job_matches.llm_analysis` continua sem análise. Evidências ausentes ou incoerentes levam a requisitos sem confirmação. [Testes](../../../tests/db/test_job_analysis.py#L161) · [Cache](../../../app/services/llm_cache.py) |
| Custo e latência por vaga | A medição registrada para 34 vagas e 68 chamadas em Ollama local mostra tarifa de USD 0 e mediana do serviço de 24.234,5 ms. A soma dos custos, a mediana e a presença das medições por vaga foram conferidas na tabela publicada. [Avaliação](../../evaluation.md#avaliação-com-llm) |
| CI sem LLM real | A suíte usa respostas simuladas e intercepta o transporte do adaptador Ollama. O workflow provisiona PostgreSQL e a avaliação com inferência local exige execução explícita. [Testes do provedor](../../../tests/unit/test_llm_providers.py) · [Teste da avaliação](../../../tests/db/test_llm_evaluation.py) · [Workflow](../../../.github/workflows/ci.yml) |

## Verificação

- [x] F3-T01 a F3-T07 integradas na branch da fase. [Documentação da camada LLM](../../llm-strategy.md) · [Relatório técnico](../../../RELATORIO.md#fase-3--camada-llm)
- [x] Linha de base reproduzida offline e Ruff e formatação aprovados. A medição da F3-T06 permanece a referência do gate.
- [x] 507 testes aprovados em PostgreSQL no Windows. No CI da revisão `ac7713c`, 503 passaram, quatro exclusivos do Windows foram omitidos e o ciclo de migração passou. Cobertura de 97,47% em `app` e 96,11% em `app/services`. [CI da fase](https://github.com/JoaumPdr/jobpilot-ai/actions/runs/45537543242)
- [x] Abrir o PR #46 para `develop` e confirmar o CI de `7ecab9d`. [CI do PR](https://github.com/JoaumPdr/jobpilot-ai/actions/runs/45539247863)
- [x] Mesclar com histórico após autorização, confirmar o CI em `develop` e conferir a tag anotada `fase-03` no GitHub com apontamento para `b7348cc`. [CI do merge](https://github.com/JoaumPdr/jobpilot-ai/actions/runs/45539395837)

```powershell
uv sync --locked
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run python -m scripts.evaluate_matching --check --timing
```
