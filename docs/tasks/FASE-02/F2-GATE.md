# F2-GATE — Gate de saída da Fase 2

- **Integração da fase** — `phase/02-matching` → `develop` pelo [PR #37](https://github.com/JoaumPdr/jobpilot-ai/pull/37).
- **Estado** — concluído no merge `d30f0fc`, marcado com a tag anotada [`fase-02`](https://github.com/JoaumPdr/jobpilot-ai/tree/fase-02).
- **Revisão validada** — `b1f6d28`, sincronizada com o GitHub. `develop` em `e8d65d2` é ancestral da fase.
- **Estratégia** — execução direta com `gpt-6.2-sol` em esforço `high`. Política Base e hook passivo confirmados.
- **Critérios** — [Backlog da Fase 2](../../BACKLOG.md#fase-2--matching--branch-phase02-matching--tag-fase-02) · [Plano mestre, §11](../../PLANO.md#11-fases-resultados-e-gates-de-saída)

| Requisito | Evidência verificada |
|---|---|
| RF-07 | Extração de requisitos obrigatórios e desejáveis em PT-BR e EN, com evidências literais. Cadastro manual e importação gravam os requisitos em PostgreSQL. [Extração](../../../tests/unit/test_job_requirements.py) · [Persistência e reprocessamento](../../../tests/db/test_job_requirements.py) |
| RF-08 | Score com pesos, requisitos atendidos, ausências confirmadas e não confirmados, além de evidências na resposta persistida. [Cálculo do score](../../../tests/unit/test_scoring.py) · [Detalhe e recálculo pela API](../../../tests/api/test_matching_api.py#L51) |
| RF-09 | Regras eliminatórias por modalidade, localização, empresa e habilidades obrigatórias. Uma vaga eliminada mantém as flags e recebe score nulo. O ranking padrão exclui esse resultado. [Regras](../../../tests/unit/test_knockouts.py) · [Ranking pela API](../../../tests/api/test_matching_api.py#L86) |

## Verificação

- [x] `deterministico-v1` confirmada no carregador de produção e na resposta da API. A consulta por versão recupera o histórico. [Configuração](../../../data/matching/scoring.toml) · [Teste de versão histórica](../../../tests/api/test_matching_api.py#L156)
- [x] Golden set de 34 vagas com relatório reproduzido em execução offline. Precisão de 99,24%, revocação de 67,53% e concordância ordinal de 86,48% em 355 pares comparáveis. [Relatório](../../evaluation.md)
- [x] Suíte completa com 440 testes aprovados em PostgreSQL. Cobertura de 97,14% em `app` e 95,14% em `app/services`, acima dos mínimos de 70% e 85%.
- [x] Ruff e formatação aprovados. A revisão `b1f6d28` passou também no ciclo Alembic do CI. [CI da branch da fase](https://github.com/JoaumPdr/jobpilot-ai/actions/runs/45313001607)
- [x] Roteiro do README, metodologia, avaliação e relatório técnico consolidados na F2-T08. [Ficha da F2-T08](F2-T08.md) · [Roteiro de matching](../../../README.md#fluxo-da-fase-2)
- [x] Abrir o PR da fase para `develop`.
- [x] Confirmar o [CI do PR #37](https://github.com/JoaumPdr/jobpilot-ai/actions/runs/45314184412) na revisão `dc161e6` e mesclar com histórico após autorização.
- [x] Confirmar o [CI em `develop`](https://github.com/JoaumPdr/jobpilot-ai/actions/runs/45314777921), publicar a tag anotada `fase-02` e conferir seu apontamento para `d30f0fc` no GitHub.

```powershell
uv run python -m scripts.evaluate_matching --check
uv run coverage run --source=app -m pytest
uv run coverage report --precision=2 --fail-under=70
uv run coverage report --precision=2 --include='app/services/*' --fail-under=85
```
