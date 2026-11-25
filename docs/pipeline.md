# Estado e contratos do pipeline

Uma execução trata as vagas de um lote para um candidato. O chamador atribui
um UUID a `run_id` e informa `candidate_id`. `filters` aceita os filtros de
`JobListQuery`. Se o filtro incluir um candidato, ele precisa coincidir com
o da execução. A análise LLM é opcional e começa desativada.
[Estado tipado](../app/orchestration/state.py) · [Filtros](../app/schemas/jobs.py)

| Nó | Entrada | Resultado no estado |
|---|---|---|
| Importar | CSV fornecido à execução como bytes, nome de arquivo e origem opcionais, conforme o serviço de importação | `imported` com o UUID do lote e os IDs das vagas vinculadas a ele |
| Normalizar | `imported` e vagas do lote | `normalized_ids` com as vagas normalizadas. O serviço de importação já normaliza o CSV |
| Deduplicar | `normalized_ids` e relações de duplicidade das vagas | `deduplicated_ids` com os IDs que seguem para filtragem |
| Filtrar | `deduplicated_ids` e `filters` | `filtered_ids` com as vagas da execução que satisfazem a consulta |
| Calcular matching | `candidate_id` e `filtered_ids` | `matching` com a versão de scoring e os pares de UUID e score. O score pode ser nulo para uma vaga eliminada |
| Selecionar | `matching` e `llm_enabled` | `selected_ids` em ordem de seleção. No modo local sob demanda cabem até dez vagas com score ≥ 0,80. No modo determinístico a lista fica vazia |
| Analisar | `candidate_id`, `selected_ids` e versão de scoring de `matching` | `analyzed_ids` identifica as vagas cuja análise validada foi gravada pelo serviço |

O estado transporta referências às vagas e ao lote. O conteúdo do CSV é entrada
transitória da importação. O matching e as evidências da análise ficam nos
registros que os serviços já mantêm. [Importação](../app/services/job_import.py) · [Estratégia LLM](llm-strategy.md) · [Critérios do funil](evaluation.md#funil-de-custo)

## Execução dos quatro nós determinísticos

`import_jobs` recebe os bytes do CSV e usa `JobImportService.import_csv`.
Somente as vagas persistidas nesse lote entram em `imported.job_ids`. Como
o importador chama `JobService.prepare_job` antes de gravar cada vaga,
`normalize_jobs` pode entregar esses mesmos IDs para a deduplicação.
Um CSV composto apenas de duplicatas exatas ou linhas rejeitadas produz um
lote com zero vagas. [Implementação dos nós](../app/orchestration/deterministic.py)

`deduplicate_jobs` exclui as duplicatas confirmadas por revisão humana.
Vagas que apenas compartilham um fingerprint seguem no pipeline. A etapa
considera todo o conjunto, inclusive vagas arquivadas. Em seguida,
`filter_jobs` aplica os filtros do catálogo aos IDs restantes e só então
seleciona a página por `offset` e `limit`. Assim, vagas de outros lotes
não ocupam posições na página. [Teste com PostgreSQL](../tests/integration/test_deterministic_nodes_db.py)

## Validação nas fronteiras

`None` indica que o nó ainda não produziu resultado. Uma coleção vazia indica
que a etapa terminou com zero vagas. Cada resultado exige o resultado da
etapa anterior e só pode conter IDs distintos vindos dela. Assim, um lote
vazio pode atravessar todas as etapas e uma análise parcial pode conter
apenas as vagas bem-sucedidas.

O nó produz os campos indicados na tabela. Para validar uma atualização,
combine seus campos com `state.model_dump()` e entregue o dicionário completo
a `PipelineState.model_validate(...)`. Para transportar o estado em JSON,
use `model_dump_json()` e reconstrua com `model_validate_json()`. A validação
rejeita campos desconhecidos. [Testes de contrato](../tests/unit/test_pipeline_state.py)
