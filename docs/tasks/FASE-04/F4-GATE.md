# F4-GATE — Integração da Fase 4 e publicação do MVP

## Critérios técnicos

A revisão `0575c39` de `phase/04-orquestracao` inclui as oito tarefas da fase. A base de integração em `develop` é `b6fb209`. [Critérios de saída da fase](../../PLANO.md#11-fases-resultados-e-gates-de-saída)

| Critério | Evidência |
|---|---|
| RF-11 | O grafo importa e normaliza o CSV, aplica as decisões de deduplicação e os filtros, calcula o matching e encaminha as vagas selecionadas à análise opcional. Os testes verificam os IDs que seguem entre as etapas e o resultado do lote pela API. [Contratos](../../pipeline.md) · [Nós determinísticos](../../../tests/integration/test_deterministic_nodes_db.py) · [Nós de matching e análise](../../../tests/integration/test_matching_nodes_db.py) · [Fluxo HTTP](../../../tests/api/test_pipeline_runs_api.py) |
| Logs, retry e persistência | Os logs identificam a execução e a etapa. Os testes cobrem o limite de tentativas por vaga, a preservação dos resultados parciais e a retomada após interrupção. Repetir o lote com o mesmo UUID recupera o resultado persistido. [Logs por etapa](../../../app/orchestration/persistence.py) · [Testes do grafo](../../../tests/unit/test_pipeline_graph.py) · [Testes em PostgreSQL](../../../tests/integration/test_pipeline_runs_db.py) |
| Dez critérios do MVP | A F4-T08 vincula cada critério a testes ou documentação e registra a execução do exemplo do README, do cadastro ao salvamento manual. [Checklist validado](F4-T08.md#evidências-dos-dez-critérios) |

Na partida, 558 testes passaram em PostgreSQL. A cobertura atingiu 97,51% em `app` e 96,00% em `app/services`. Ruff aprovou lint e formatação, e `ty` aprovou a orquestração, o serviço de execução e as rotas do pipeline. O pacote e a API declaram a versão `0.1.0`.

O launcher confirmou o perfil Base do projeto e o hook passivo. O líder `gpt-6.2-astra` executou a verificação diretamente com esforço `high`.

## Integração e publicação

- [x] Conferir as tarefas integradas, o RF-11, os dez critérios do MVP e a suíte.
- [ ] Integrar `phase/04-orquestracao` em `develop` por PR, conferir o CI e publicar a tag anotada `fase-04` no merge verificado.
- [ ] Integrar `develop` em `main` por PR e conferir o CI do merge.
- [ ] Publicar a tag anotada `v0.1.0` no merge em `main`, criar a release com as notas do changelog e conferir ambos no GitHub.
