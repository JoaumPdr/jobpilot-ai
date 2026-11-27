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

## Matching, seleção e análise

`match_jobs` chama `MatchingService.calculate` para cada vaga filtrada do
candidato. O estado recebe os scores determinísticos na ordem de entrada e
a versão do cálculo. Um lote vazio recebe a versão ativa e zero resultados.

No modo determinístico, `select_jobs` produz uma seleção vazia. Com o LLM
habilitado, seleciona até dez vagas com score ≥ 0,80, por score decrescente
e UUID crescente nos empates. Vagas com score nulo ficam fora. O estado
também verifica esse corte ao reconstruir uma seleção. [Avaliação do funil](evaluation.md#funil-de-custo)

`analyze_jobs` chama `JobAnalysisService.analyze` na ordem da seleção,
usando o candidato e a versão do matching. Uma seleção vazia completa a
etapa com zero chamadas. O serviço mantém a validação, o cache e o limite
de um reparo por vaga. O funil admite, assim, até 20 chamadas lógicas por
execução, contando os reparos. [Nós](../app/orchestration/matching.py) · [Teste com provedor falso](../tests/integration/test_matching_nodes_db.py)

## Execução local e falhas por vaga

`run_pipeline` recebe um `PipelineState` inicial, os bytes do CSV e os serviços
de importação, catálogo e matching. Nome do arquivo e origem são opcionais.
Quando `llm_enabled` está ativo, o chamador também fornece o serviço de análise.
O grafo executa os nós em sequência e devolve o estado final validado. Uma seleção
vazia encerra o fluxo com `analyzed_ids=()`. [Grafo](../app/orchestration/graph.py)

No matching, um timeout do pool, uma conexão invalidada ou os códigos PostgreSQL
`40001` e `40P01` permitem uma segunda tentativa da mesma vaga após 250 ms.
Quando uma falha esperada é definitiva, o grafo registra em `errors` o UUID da
vaga, a etapa, o tipo da exceção e o número de tentativas do nó. As vagas
seguintes continuam. Na análise, cada vaga selecionada chega ao serviço uma vez.
O provedor e o serviço cuidam das tentativas de transporte e do reparo da resposta.
Erros do lote e erros de programação chegam ao chamador. [Testes do grafo](../tests/unit/test_pipeline_graph.py)

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

## Persistência e retomada

A API local expõe a execução por `POST /pipeline/runs` e a leitura do último
snapshot por `GET /pipeline/runs/{id}`. [Contrato HTTP e exemplo](api.md#pipeline)

`run_persisted_pipeline(estado_inicial, content=csv)` reserva o UUID do
chamador. Para retomar, repita a chamada com o mesmo estado inicial, CSV,
nome e origem. No modo LLM, forneça também o provedor. O serviço compara o
SHA-256 dos bytes, os parâmetros da execução, a versão de scoring e a identidade
do provedor e modelo. Se o UUID estiver associado a outra entrada, levanta
`ConflictError`. O conteúdo do CSV permanece transitório.

Cada nó bloqueia a linha de `pipeline_runs`, lê o snapshot confirmado e grava
seus efeitos no catálogo e o novo snapshot em uma transação. Assim, duas
chamadas simultâneas podem fazer a mesma execução avançar. Se o processo cair
antes da confirmação, a próxima chamada reencontra o nó pendente. O cache LLM
mantém sua transação própria e pode reutilizar uma resposta já validada.

| Status | Efeito ao repetir a chamada |
|---|---|
| `running` | Continua a partir da primeira etapa pendente |
| `failed` | Repete a etapa que falhou e preserva as anteriores |
| `completed` | Devolve o snapshot final |
| `partial` | Devolve o snapshot final com os erros por vaga |

Os eventos `pipeline_node_completed` e `pipeline_node_failed` identificam
a etapa e herdam o `run_id` no contexto de logging. A falha registra o tipo
da exceção. [Execução persistida](../app/orchestration/persistence.py) · [Testes em PostgreSQL](../tests/integration/test_pipeline_runs_db.py)

## Revisão humana das recomendações

O grafo termina quando entrega as recomendações ao usuário. No estado devolvido
por `run_pipeline` ou `run_persisted_pipeline`, a propriedade Python
`recommendations_for_review` lista as vagas do lote com score determinístico,
por score decrescente e UUID crescente nos empates. Cada item traz `job_id`
e `score`. Durante a execução, a propriedade vale `None`. Ao final, uma
tupla vazia indica que nenhuma vaga recebeu score. Uma falha na análise LLM
preserva a recomendação baseada no matching e aparece em `errors`.
A lista deriva do snapshot e também está disponível ao recuperar execuções
anteriores. O top-10 e o limiar de 0,80 continuam específicos da análise LLM.

O usuário pode encerrar a revisão ou escolher uma vaga e solicitar
`POST /candidates/{candidate_id}/jobs/{job_id}/save`. Essa escolha explícita
registra a vaga como `salva` no acompanhamento local. Cabe ao usuário enviar
a candidatura ao empregador e registrar a mudança de status. Concluir ou
retomar o pipeline preserva as candidaturas existentes.
[Operação de salvar](api.md#post-candidatescandidate_idjobsjob_idsave) · [Teste em PostgreSQL](../tests/integration/test_pipeline_runs_db.py)
