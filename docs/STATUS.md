# JobPilot AI — STATUS (estado vivo)

> Vira `docs/STATUS.md`. **Atualizar ao final de toda sessão** (e após cada tarefa concluída).
> Objetivo: qualquer agente ou pessoa retoma o trabalho em menos de 2 minutos lendo só este arquivo.
> Só o Orquestrador (ou o agente único) edita este arquivo.

---

## 1. Retomada rápida

| Campo | Valor |
|-------|-------|
| **Última atualização** | 2026-11-25 (UTC) |
| **Fase atual** | Fase 4 — Orquestração |
| **Branch base** | `phase/04-orquestracao`, criada de `develop` em `b6fb209` após a integração do encerramento documental pelo PR #47 |
| **Última tarefa integrada** | [F4-T01 — Estado do pipeline e contratos dos nós](tasks/FASE-04/F4-T01.md), em `54badc1` |
| **Tarefa atual** | [F4-T02 — Nós determinísticos](tasks/FASE-04/F4-T02.md), na branch `feat/f4-t02-nos-deterministicos` |
| **Estado da tarefa** | Implementada e validada localmente. Aguarda autorização para PR e integração na fase |
| **Último merge de fase** | `b7348cc` — PR #46 (F3-GATE), em `develop` |
| **Testes** | **533 testes aprovados** com PostgreSQL, incluindo nove da F4-T02. Cobertura de 97,55% em `app` e 96,13% em `app/services`. Tipagem dos três módulos alterados, Ruff e formatação aprovados |
| **CI** | Aprovado na revisão `1ae2f2b` do PR #48 e no merge `54badc1`. [CI do PR](https://github.com/JoaumPdr/jobpilot-ai/actions/runs/45693518765) · [CI do merge](https://github.com/JoaumPdr/jobpilot-ai/actions/runs/45693771113) |
| **Repositório remoto** | `https://github.com/JoaumPdr/jobpilot-ai` |
| **Sincronização com o remoto** | `phase/04-orquestracao` atualizada por fast-forward após o PR #48. A branch da tarefa foi preservada no GitHub |
| **Merge da fase confirmado no remoto** | 2026-11-25 03:21 UTC, `b7348cc` em `develop` |
| **PR da fase** | [PR #46 — F3-GATE](https://github.com/JoaumPdr/jobpilot-ai/pull/46), mesclado em `develop` |
| **Última tag publicada** | [`fase-03`](https://github.com/JoaumPdr/jobpilot-ai/tree/fase-03) → `b7348cc` (tag anotada `492895f`) |
| **GitHub** | `gh` autenticado usado para abrir e mesclar o PR #48 com autorização e acompanhar o CI. MCP usado para confirmar o merge |

### Próxima ação exata (uma frase, imperativa)

> Com autorização do JP, abrir o PR de `feat/f4-t02-nos-deterministicos` para `phase/04-orquestracao`, conferir o CI da revisão e integrar com histórico.

---

## 2. O que foi feito na última sessão

- **F4-T02 implementada (2026-11-25 UTC).** Os quatro nós usam os dados persistidos pelo importador e os filtros do catálogo. A suíte passou de 524 para 533 testes. Após a correção autorizada, a tipagem dos três módulos passou. Política Base e hook confirmados, execução direta com Astra em esforço `high`. [Ficha](tasks/FASE-04/F4-T02.md)
- **F4-T01 integrada (2026-11-25 UTC).** O PR #48 integrou o estado tipado e os contratos dos nós em `54badc1`. O CI passou na revisão `1ae2f2b` e no merge. O ponto de retomada é a F4-T02. [PR #48](https://github.com/JoaumPdr/jobpilot-ai/pull/48)
- **F4-T01 implementada.** A suíte de partida em `b6fb209` passou com 507 testes na repetição autorizada, após seis falhas relacionadas a horários. O líder foi ajustado para `gpt-6.2-astra` com esforço `high`. O launcher confirmou a política Base e o hook do projeto. Execução direta. [Contratos](pipeline.md) · [Ficha](tasks/FASE-04/F4-T01.md)
- **F3-GATE concluído (2026-11-25 UTC).** O PR #46 integrou a Camada LLM em `b7348cc`. O CI passou na revisão `7ecab9d` e no merge em `develop`, e a tag anotada `fase-03` foi publicada e conferida no GitHub. Próximo ponto de retomada na F4-T01 após integrar o encerramento documental. [PR #46](https://github.com/JoaumPdr/jobpilot-ai/pull/46) · [Tag `fase-03`](https://github.com/JoaumPdr/jobpilot-ai/tree/fase-03)
- **F3-GATE validado tecnicamente (2026-11-25 UTC).** RF-10, proteção contra persistência de respostas inválidas, custo e latência por vaga e CI com respostas simuladas conferidos. Os 507 testes locais passaram, assim como Ruff, formatação e reprodução offline da linha de base. Execução direta com `gpt-6.2-sol` e esforço `high`, política Base e hook passivo confirmados. [Ficha](tasks/FASE-03/F3-GATE.md)
- **F3-T07 integrada (2026-11-25 UTC).** O PR #45 foi mesclado com histórico e autorização em `7b930d4`. CI aprovado em `bb79bab` e no merge, com 503 testes aprovados e quatro exclusivos do Windows omitidos no CI do PR. A branch da fase avançou por fast-forward. Ponto de retomada no F3-GATE. [PR #45](https://github.com/JoaumPdr/jobpilot-ai/pull/45)
- **F3-T07 documentada (2026-11-25 UTC).** README com exemplo do serviço Python, estratégia atualizada e síntese das evidências em `evaluation.md` e `RELATORIO.md`. Suítes de partida e entrega com 507 testes. O exemplo foi conferido em PostgreSQL isolado com resposta simulada e reutilização pelo cache. Execução direta em `gpt-6.2-sol` com esforço `high`, política Base e hook passivo confirmados. [Ficha](tasks/FASE-03/F3-T07.md)
- **F3-T06 integrada (2026-11-25 UTC).** O [PR #44](https://github.com/JoaumPdr/jobpilot-ai/pull/44) foi mesclado com histórico e autorização em `6f5ef4d`. CI verde na revisão `807eef8` e no merge. A branch local da fase avançou por fast-forward. Ponto de retomada na F3-T07.
- **F3-T06 implementada (2026-11-25 UTC).** Avaliação local com 34 vagas, 68 chamadas a Qwen2.5 1.5B em CPU, mediana de 24,23 s e tarifa total de USD 0. A revocação caiu de 71,88% para 39,38%. Funil local sob demanda de score ≥ 0,80 e top-10. Suítes de partida e entrega com 506 e 507 testes. Execução direta em `gpt-6.2-sol` com esforço `high`, política Base e hook passivo confirmados. [Ficha](tasks/FASE-03/F3-T06.md) · [Relatório](evaluation.md#avaliação-com-llm)
- **F3-T05 integrada (2026-11-25 UTC).** O [PR #43](https://github.com/JoaumPdr/jobpilot-ai/pull/43) foi mesclado com histórico e autorização em `01da5d6`. CI verde na revisão `fc96823` e no merge. A branch local da fase avançou por fast-forward. Ponto de retomada na F3-T06.
- **F3-T05 implementada (2026-11-25 UTC).** Análise validada e persistida no matching, com conferência de evidências, reparo único e reutilização via cache. Suíte de partida com 496 testes aprovados e suíte de entrega com 506. Execução direta em `gpt-6.2-sol` com esforço `high`, política Base e hook passivo confirmados. [Ficha](tasks/FASE-03/F3-T05.md)
- **F3-T04 integrada (2026-11-25 UTC).** O [PR #42](https://github.com/JoaumPdr/jobpilot-ai/pull/42) foi mesclado com histórico e autorização em `8fe13f8`. CI verde na revisão `9556229` e no merge. A branch local da fase avançou por fast-forward. Ponto de retomada na F3-T05.
- **F3-T04 implementada (2026-11-25 UTC).** Cache de análises validadas em PostgreSQL, bloqueio transacional por chave e métricas por chamada. A revisão `000000000007` passou no ciclo de migração em banco isolado. Suíte de partida com 490 testes aprovados e suíte de entrega com 496. Execução direta em `gpt-6.2-sol` com esforço `high`, política Base e hook passivo confirmados. [Ficha](tasks/FASE-03/F3-T04.md)
- **F3-T03 integrada (2026-11-25 UTC).** O [PR #41](https://github.com/JoaumPdr/jobpilot-ai/pull/41) foi mesclado com histórico e autorização em `5543a11`. CI verde na revisão `e9fff2d` e no merge. A branch local da fase avançou por fast-forward. Ponto de retomada na F3-T04.
- **F3-T03 implementada (2026-11-25 UTC).** Descrição delimitada em JSON, limite de 8.000 caracteres, seleção do perfil a partir do matching e prompt `job-analysis-v2`. Suíte de partida com 481 testes aprovados e suíte de entrega com 490. Execução direta em `gpt-6.2-sol` com esforço `high`, política Base e hook passivo confirmados. [Ficha](tasks/FASE-03/F3-T03.md)
- **F3-T02 integrada (2026-11-25 UTC).** O [PR #40](https://github.com/JoaumPdr/jobpilot-ai/pull/40) foi mesclado com histórico e autorização em `a97e8c8`. CI verde na revisão `c08edb2` e no merge. A branch local da fase avançou por fast-forward. Ponto de retomada na F3-T03.
- **F3-T02 implementada (2026-11-25 UTC).** Contrato Pydantic, prompt `job-analysis-v1` e registro de `prompt_version` a partir do prompt efetivamente usado. Suíte de partida com 461 testes aprovados e suíte da entrega com 481 testes. Execução direta em `gpt-6.2-sol` com esforço `high`, política Base e hook passivo confirmados. [Ficha](tasks/FASE-03/F3-T02.md)
- **F3-T01 integrada (2026-11-25 UTC).** O [PR #39](https://github.com/JoaumPdr/jobpilot-ai/pull/39) foi mesclado com histórico e autorização em `100666d`. CI verde na revisão `b9d7b7e` e no merge. A branch local da fase avançou por fast-forward. Ponto de retomada na F3-T02.
- **F3-T01 implementada (2026-11-25 UTC).** Interface tipada, provedor falso, Ollama local e limites configuráveis. Suíte de partida com 440 testes aprovados após liberar o diretório temporário do Windows. Suíte de entrega com 461 testes aprovados, Ruff e formatação verdes. Execução direta em `gpt-6.2-sol` com esforço `high`, política Base e hook passivo confirmados. [Ficha](tasks/FASE-03/F3-T01.md)
- **Encerramento documental da Fase 2 conferido.** O PR #38 foi mesclado em `aa23972` com seis arquivos de documentação. As branches da Fase 3 e da F3-T01 foram criadas a partir dessa base. [PR #38](https://github.com/JoaumPdr/jobpilot-ai/pull/38)
- **F2-GATE concluído (2026-11-24 UTC).** O [PR #37](https://github.com/JoaumPdr/jobpilot-ai/pull/37) foi mesclado com autorização em `d30f0fc`. O CI do merge passou em `develop`, e a tag anotada `fase-02` foi publicada e conferida no GitHub. Ponto de retomada na F3-T01 após o encerramento documental.
- **PR do F2-GATE aberto (2026-11-24 UTC).** O [PR #37](https://github.com/JoaumPdr/jobpilot-ai/pull/37) foi aberto de `phase/02-matching` para `develop` com `gh` autenticado após autorização do JP.
- **F2-GATE validado tecnicamente (2026-11-24 UTC).** RF-07 a RF-09 cobertos por testes, `deterministico-v1` ativa e golden set reproduzido. Suíte com 440 testes em PostgreSQL, cobertura de 97,14% em `app` e 95,14% em `app/services`. Execução direta com `gpt-6.2-sol` em `high`, política Base e hook passivo confirmados. [Ficha do gate](tasks/FASE-02/F2-GATE.md)
- **F2-T08 integrada (2026-11-24 UTC).** O [PR #36](https://github.com/JoaumPdr/jobpilot-ai/pull/36) foi mesclado com histórico e autorização em `6600b97`, após CI verde na revisão `be9d320`. A branch local da fase avançou por fast-forward. Ponto de retomada no F2-GATE.
- **PR da F2-T08 aberto (2026-11-24 UTC).** O [PR #36](https://github.com/JoaumPdr/jobpilot-ai/pull/36) foi aberto de `docs/f2-t08-documentacao-matching` para `phase/02-matching` com `gh` autenticado após autorização do JP.
- **F2-T08 documentada (2026-11-24 UTC).** README com roteiro de cálculo, detalhe e ranking, metodologia com fluxo de persistência e relatório de avaliação regenerado com as mesmas métricas. Roteiro confirmado em PostgreSQL isolado, 440 testes aprovados, Ruff e formatação aprovados. Execução direta com `gpt-6.2-sol` em `high`, política Base e hook passivo confirmados.
- **F2-T07 integrada (2026-11-24 UTC).** O [PR #35](https://github.com/JoaumPdr/jobpilot-ai/pull/35) foi mesclado com histórico e autorização em `55064a5`, após CI verde na revisão `09b139e`. A branch local da fase avançou por fast-forward. Ponto de retomada na F2-T08.
- **PR da F2-T07 aberto (2026-11-24 UTC).** O [PR #35](https://github.com/JoaumPdr/jobpilot-ai/pull/35) foi aberto de `docs/f2-t07-adiar-embeddings` para `phase/02-matching` com `gh` autenticado após autorização do JP. O MCP do GitHub recusou a abertura com 403.
- **F2-T07 documentada (2026-11-24 UTC).** O [ADR 0012](adr/0012-adiar-embeddings-multilingues.md) adia a adoção de embeddings até haver evidência comparativa de ganho. O relatório disponível mede a linha de base determinística. Suíte de partida com 440 testes aprovados em PostgreSQL. Execução direta com `gpt-6.2-sol` em `high`, política Base e hook passivo confirmados.
- **F2-T06 integrada (2026-11-24 UTC).** O [PR #34](https://github.com/JoaumPdr/jobpilot-ai/pull/34) foi mesclado com histórico e autorização em `8209788`, após CI verde na revisão `92f139e`. A branch local da fase avançou por fast-forward. Ponto de retomada na decisão condicional da F2-T07.
- **F2-T06 implementada (2026-11-24 UTC).** Curadoria de 34 vagas expurgadas e rotuladas, script offline e relatório reproduzível. Precisão de 99,24%, revocação de 67,53% e concordância ordinal de 86,48%. 437 testes de partida e 440 na entrega. Execução direta com `gpt-6.2-sol` em `high`. Política Base e hook passivo confirmados.
- **F2-T05 integrada (2026-11-24 UTC).** O [PR #33](https://github.com/JoaumPdr/jobpilot-ai/pull/33) foi mesclado com histórico e autorização em `673cdd5`, após CI verde na revisão `fb4ed4d`. A branch local da fase avançou por fast-forward. Ponto de retomada na F2-T06.
- **F2-T05 implementada (2026-11-24 UTC).** Persistência versionada em `job_matches`, cálculo, ranking e detalhe de matching. Suíte de partida com 434 testes e entrega com 437. Execução direta com `gpt-6.2-sol` em `high`, política Base e hook passivo confirmados.
- **CI atualizado para Node.js 24 (2026-11-24 UTC).** [PR #32](https://github.com/JoaumPdr/jobpilot-ai/pull/32) integrado em `7426146`. `checkout` v7.0.1 e `setup-uv` v10.4.0 passaram no PR e na fase sem a anotação de Node.js 20.
- **F2-T04 integrada (2026-11-24 UTC).** O [PR #31](https://github.com/JoaumPdr/jobpilot-ai/pull/31) foi mesclado com histórico e autorização em `4c353db`, após CI verde na revisão `003c06a`. A branch local da fase avançou por fast-forward. Ponto de retomada na F2-T05.
- **F2-T04 implementada (2026-11-24 UTC).** Cálculo puro, explicação por requisito e configuração `deterministico-v1`. 420 testes na partida e 434 na entrega. Política Base e hook passivo confirmados. Execução direta com `gpt-6.2-sol` em `high`.
- **F2-T03 integrada (2026-11-24 UTC).** O [PR #30](https://github.com/JoaumPdr/jobpilot-ai/pull/30) foi mesclado com histórico e autorização em `8b740b4`, após CI verde na revisão `c4f597a`. A branch local da fase avançou por fast-forward. Ponto de retomada na F2-T04.
- **F2-T03 implementada (2026-11-23 UTC).** Flags eliminatórias com decisão de elegibilidade, validação das listas de preferências e leitura dos requisitos obrigatórios persistidos. 400 testes na partida e 420 na entrega. Política Base e hook passivo confirmados. Execução direta com `gpt-6.2-sol` em `high`.
- **F2-T02 integrada (2026-11-23 UTC).** O [PR #29](https://github.com/JoaumPdr/jobpilot-ai/pull/29) foi mesclado com histórico e autorização em `24ce540`, após CI verde na revisão `e9ac9ec`. A branch local da fase avançou por fast-forward. Ponto de retomada na F2-T03.
- **F2-T02 implementada (2026-11-23 UTC).** Extração determinística em PT/EN, persistência em `job_skills` no cadastro e na importação e reprocessamento de vagas existentes. 387 testes na partida, 400 na entrega, com ciclo da migração em PostgreSQL. Execução direta com `gpt-6.2-sol` em `high`, após ajuste confirmado pelo JP. Política Base e hook passivo confirmados.
- **Limpeza de branches autorizada (2026-11-23 UTC).** Excluídas sete branches locais e seis remotas de `docs/*`, `test/*` e `fix/*`. Todas as pontas já pertenciam a `origin/develop` e nenhuma tinha PR aberto. A branch `docs/f1-t01-padronizacao-documental` existia só localmente.
- **F2-T01 integrada (2026-11-23 UTC).** O [PR #28](https://github.com/JoaumPdr/jobpilot-ai/pull/28) foi mesclado com histórico e autorização em `62649a8`, após CI verde na revisão `6b109a6`. A branch local da fase avançou por fast-forward. Ponto de retomada na F2-T02.
- **PR da F2-T01 aberto (2026-11-23 UTC).** O [PR #28](https://github.com/JoaumPdr/jobpilot-ai/pull/28) foi aberto com `gh` autenticado após autorização do JP. O MCP do GitHub recusou a abertura com 403.
- **F2-T01 implementada (2026-11-23 UTC).** Catálogo em TOML com 184 habilidades em 9 categorias, busca por nome ou alias e relatório em memória dos termos não reconhecidos. A suíte de partida teve 360 testes aprovados e a da entrega, 387. Política Base e hook passivo do JobPilot confirmados. Execução direta em `gpt-6.2-sol` com esforço `medium`.
- **F1-GATE concluído (2026-11-19 UTC).** O [PR #26](https://github.com/JoaumPdr/jobpilot-ai/pull/26) foi mesclado com autorização em `bbea363`. O CI do merge passou em `develop`, e a tag anotada `fase-01` foi publicada e conferida no GitHub. Ponto de retomada na F2-T01.
- **F1-GATE validado tecnicamente (2026-11-19 UTC).** A ficha reúne as evidências de RF-01 a RF-06, reimportação idempotente, cobertura e documentação. A suíte local passou com 360 testes. Cobertura de 96,60% em `app` e 95,33% em `app/services`. Execução direta com Sol/Medium, política e hook confirmados. [PR #26](https://github.com/JoaumPdr/jobpilot-ai/pull/26) aberto para `develop`.
- **F1-T13 integrada (2026-11-19 UTC).** O [PR #25](https://github.com/JoaumPdr/jobpilot-ai/pull/25) foi mesclado com autorização em `5fa4999`. A branch local da fase avançou por fast-forward e o CI do merge passou. O gate de saída é o ponto de retomada.
- **F1-T13 documentada (2026-11-19 UTC).** README com roteiro pelo Swagger UI, referências da API e do banco atualizadas, relatório consolidado e changelog da fase em desenvolvimento. O roteiro foi exercitado com seus exemplos exatos em PostgreSQL isolado. Rotas e links locais conferidos, 360 testes aprovados, Ruff e formatação verdes. Execução direta com Sol/Medium. [PR #25](https://github.com/JoaumPdr/jobpilot-ai/pull/25) aberto para a fase.
- **F1-T12 integrada (2026-11-19 UTC).** O [PR #24](https://github.com/JoaumPdr/jobpilot-ai/pull/24) foi revisado e mesclado com autorização em `3bb0df1`. Suíte de partida com 360 testes aprovados, política do JobPilot AI e hook confirmados pelo launcher. Revisão direta com Sol/Medium. A branch da fase foi atualizada por fast-forward e o CI do merge ficou verde. Ponto de retomada na F1-T13.
- **F1-T12 implementada (2026-11-19 UTC).** O teste pela API cobriu perfil, preferências, importação e reimportação CSV, filtros e candidatura com histórico. A suíte local passou com 360 testes em PostgreSQL. Adicionado `coverage.py` ao grupo de desenvolvimento, com os limites de 70% global e 85% nos serviços aplicados no CI. Execução direta com Sol/Medium.
- **Limpeza de branches (2026-11-19 UTC).** Removidas 12 branches de tarefas da F1-T01 à F1-T11 no Git local e no GitHub. Todos os commits removidos das referências já pertenciam ao histórico da fase. As branches de fase, `develop` e `main` foram verificadas após a limpeza.
- **F1-T11 implementada (2026-11-19 UTC).** O arquivamento oculta a vaga na listagem padrão. O atalho de salvar cria uma candidatura em `salva` com histórico inicial. O fluxo até `aplicada` foi validado com PostgreSQL. Suíte com 359 testes aprovados, Ruff e formatação verdes. Execução direta com Sol/Medium, no perfil Base.
- **F1-T11 integrada (2026-11-19 UTC).** [PR #23](https://github.com/JoaumPdr/jobpilot-ai/pull/23) mesclado em `5b11e45` com CI verde. Branch da fase atualizada por fast-forward. Ponto de retomada na F1-T12.
- **Correção do launcher integrada (2026-11-19 UTC).** O [PR #22](https://github.com/JoaumPdr/jobpilot-ai/pull/22) substituiu o PR #21 e foi mesclado em `010b9c6` com CI verde. O launcher inicia o Codex com servidor embutido e exige tier e provedor também em `run`. A nova sessão confirmou a política, os playbooks, o diretório de estado do JobPilot AI e `Hook Alethe (confirmed)`. Suíte local com 356 testes aprovados, incluindo 15 regressões do launcher.
- **Validação da intervenção.** Com Codex CLI 0.170.0 e Alethe 24, os três tiers resolveram no `dry-run`. Planos sem tier, política ausente ou inválida e provedor indisponível foram recusados. Em duas chamadas pela assinatura ChatGPT, uma sessão nova confirmou Sol/medium e gravou o estado do hook no diretório do projeto, e um worker somente leitura confirmou Luna/low e retornou `DONE` sem alterações. A suíte existente passou com 341 testes, e Ruff e formatação passaram.
- **F1-T10 implementada (2026-11-19 UTC).** Candidaturas com rotas por candidato, observações editáveis e histórico gravado junto da transição. `GET /jobs` aceita status da candidatura combinado com candidato e os filtros existentes. A suíte de partida passou com 289 testes. A suíte com a entrega passou com 341 testes. Execução direta no perfil Base da Alethe, com etapas do `plan-execute` e revisão local do diff.
- **F1-T10 integrada (2026-11-19 UTC).** [PR #20](https://github.com/JoaumPdr/jobpilot-ai/pull/20) mesclado em `e982147` com CI verde. A branch da fase recebeu o merge por fast-forward. A branch da tarefa foi preservada no GitHub.
- **F1-T09 implementada (2026-11-19 UTC):** modelos de candidaturas e histórico, com unicidade por par candidato/vaga, FKs e validação de status na migração `000000000004`. Suíte com 289 testes e ciclo de migração validado em PostgreSQL.
- **F1-T09 integrada (2026-11-19 UTC):** [PR #19](https://github.com/JoaumPdr/jobpilot-ai/pull/19) mesclado em `1b7f7da` com CI verde. Título do PR com o identificador `(F1-T09)` ao final, conforme solicitado pelo JP.
- **F1-T08 implementada (2026-11-19 UTC):** `GET /jobs` com filtros combináveis, paginação estável por data de cadastro e UUID, e opções independentes para incluir arquivadas e duplicatas confirmadas. O JP aprovou entregar o filtro por status de candidatura na F1-T10, após o modelo da F1-T09.
- **F1-T08 integrada (2026-11-19 UTC):** PR #18 mesclado com CI verde (`f612b3f`). Suíte local com 276 testes, incluindo o RNF-09 em PostgreSQL com 10 mil vagas.
- **Planejamento da v1.0.0 integrado (2026-11-19 UTC):** PR #17 mesclado em `18dd9be`. ADR 0011 aceito, tarefas de distribuição local registradas na Fase 7.
- **Adequação documental integrada (2026-11-19 UTC):** alterações commitadas em `05fe43a`, publicadas e mescladas na fase pelo PR #16 (`deef8b5`), com CI verde. A suíte local passou com 253 testes. A F1-T08 foi conferida contra o backlog e o plano mestre, e aguarda a decisão sobre o filtro por status de candidatura.
- **Adequação ao Codex CLI e à Alethe (2026-11-19 UTC):** login do Codex via ChatGPT confirmado. Política local isolada com perfil Base, teto de dois workers simultâneos, alerta de cota em 80% e bloqueio em 90%. `doctor`, `policy show`, `playbook --pick` e `usage` validados. `validate` e `dry-run` confirmaram os três tiers, o modo de leitura para revisão, o isolamento das escritas e a rejeição de `custom` em somente leitura. A cota semanal do Codex foi medida em 2%. A janela de 5 h segue desconhecida. Codex é o único provedor inicialmente habilitado e nenhum worker foi iniciado. Ponto de entrada em `AGENTS.md` e ativação da política em `docs/ALETHE_INSTRUCOES.md` §7A. A F1-T08 continua por iniciar.
- F0-T01 concluída: repositório GitHub criado, branches enviadas, estrutura de docs e arquivos base commitados.
- F0-T02 concluída: ambiente Python configurado com `uv`, dependências de dev, pre-commit, teste de sanidade e ADR 0008.
- F0-T03 concluída: `docker-compose.yml` com PostgreSQL 16 (porta 5433 no host devido a conflito com Docker Desktop backend na 5432), `.env.example` e `alembic.ini` atualizados para porta 5433, `app/core/config.py` com validação de ambiente, `app/api/routes/health.py` com conversão de URL SQLAlchemy para psycopg v3. Verificado com banco real: container saudável, `alembic upgrade head` + `downgrade -1` funcionam, `/health` retorna 200 com database.status = healthy.
- F0-T04 concluída: `app/main.py` com FastAPI, middleware `request_id`, handler global de exceções; `app/api/routes/health.py` com `GET /health`; `app/core/logging.py` com structlog JSON; `tests/api/test_health.py` com 3 testes de API. 4 testes passando, lint limpo.
- F0-T05 concluída: `app/models/base.py` com Base declarativa (UUID, __tablename__ automático), `app/core/database.py` com engine/SessionLocal/get_db, Alembic inicializado, ADR 0010 (UUID) registrado.
- F0-T06 concluída: `.github/workflows/ci.yml` com `uv sync --locked`, ruff, pytest com serviço PostgreSQL, teste de migração Alembic.
- F0-T07 concluída: ADRs 0001–0007 e 0009 criados (total de 10 ADRs incluindo 0008 e 0010), `docs/privacy-and-sources.md` criado, README revisado e completo conforme GUIA_DOCS_E_GIT.md.
- F0-GATE **concluído**: PR #4 (`phase/00-fundacao` → `develop`) mesclado com CI verde e merge commit `cbbeb65`; tag `fase-00` recriada nesse commit (a tag anterior apontava para `3df13a3`, que falhou no CI); `PR_BODY_F0.md` removido da raiz.
- Higiene pós-gate: skill de terceiros ignorado no `.gitignore` (permanece instalado localmente), `skills-lock.json` restaurado, baseline de `ruff format` aplicado e `ruff format --check` adicionado ao CI. Preparação da F1-T01 documentada, sem código.
- Sessão de padronização documental (2026-11-16): divisão de responsabilidades entre `BACKLOG.md` (fonte canônica), `STATUS.md` (retomada) e fichas `docs/tasks/` (execução); política de fichas just-in-time formalizada em `ALETHE_INSTRUCOES.md` §3A; ficha `docs/tasks/FASE-01/F1-T01.md` criada com o plano antes detalhado aqui. PR #7 aberto (docs → `phase/01`) com CI verde. Nenhum código alterado.
- **F1-T01 implementada (2026-11-16):** 5 tabelas do perfil + migração reversível `000000000002`, `migrations/env.py` registrando todos os modelos, 17 testes de constraint contra PostgreSQL real com banco isolado `jobpilot_test` (salvaguarda `_test`), `docs/data-model.md` com Mermaid e `TEST_DATABASE_URL` documentada. PR #8 integrado por merge commit com CI verde.
- **F1-T02 dividida (2026-11-16):** decisões do JP — rotas REST por `candidate_id`, JSONB estruturado validado por Pydantic, `POST /skills` permitido (na `-b`) e divisão em `F1-T02-a` (candidato + preferências + erros + `api.md`) e `F1-T02-b` (habilidades + experiências). Divisão registrada no `BACKLOG.md`.
- **F1-T02-a implementada (2026-11-16):** schemas com `education`/`languages` estruturados, exceções de domínio com handlers 404/409/422 e `request_id`, repositórios, serviço (e-mail único, upsert 1:1) e rotas REST de candidato/preferências. Fixtures de banco movidas para `tests/conftest.py` com cliente de API; 18 testes de API, 31 unitários, `docs/api.md` e `email-validator`. Suíte: 70 passed. **PR #9 integrado por merge commit (`359fbfa`) com CI verde.**
- **F1-T02-b implementada (2026-11-17):** a sessão retomou com o trabalho já escrito e não commitado (13 arquivos novos + 7 modificados). Revisão do diff, suíte completa contra PostgreSQL real (**119 passed**), lint e formatação limpos. Commits `d6513a6` (código + testes) e `eb7481d` (`docs/api.md`, BACKLOG e ficha); branch publicada e **PR #10 aberto** com CI verde (run `44187596274`). Escopo entregue: catálogo com busca `q`, `POST /skills`, vínculo por `skill_id`/`canonical_name`, `PATCH`/`DELETE` do vínculo, CRUD de experiências, `InvalidDataError` (422) para faixa de datas no `PATCH`, `CandidateRead` com `skills`/`experiences` e `selectinload` contra N+1.
- **Ambiente da sessão (2026-11-17):** Docker Desktop estava desligado, o que gerou 63 erros de conexão na primeira execução dos testes (falso vermelho). Subido o container `jobpilot-postgres` via `docker compose up -d`; suíte completa ficou verde.
- **F1-T02-b integrada (2026-11-17):** STATUS registrado em `eca1e4b`, branch sincronizada e **PR #10 mesclado** em `phase/01-nucleo-sem-ia` (merge commit `4136bf2`) com CI verde (run `44188162643`). `phase/01-nucleo-sem-ia` atualizada localmente por fast-forward; `feat/f1-t02b-skills-experiencias` preservada no remoto.
- **F1-T03 implementada e integrada (2026-11-17):** modelos `Job`/`ImportBatch` com enums (`WorkMode`, `Seniority`, `ImportKind`), migração `000000000003` reversível (upgrade → downgrade → upgrade testados), índice único parcial `(source, external_id)`, índices de `fingerprint`/`canonical_url`, FKs com `SET NULL`, CHECKs de salário/contadores; 19 testes de constraint novos; suíte **138 passed**. Commit `11ffb68`, **PR #11 mesclado** (`b837c3d`) com CI verde (run `44189183645`); `data-model.md`, BACKLOG e ficha atualizados.
- **F1-T04 implementada e integrada (2026-11-17):** funções puras em `app/services/normalization.py` (`clean_text`, `comparison_text`, `normalize_work_mode`, `normalize_seniority`, `canonicalize_url`, `job_fingerprint`), 46 testes unitários sem banco, suíte **184 passed**. Commit `3cfd4fb`, **PR #12 mesclado** (`396e851`) com CI verde (run `44191309228`); BACKLOG e ficha atualizados.
- **Sessão encerrada (2026-11-17):** 4 tarefas fechadas ou integradas (fechamento da F1-T02-b, F1-T03, F1-T04 e registros de STATUS), 3 PRs mesclados (#10, #11, #12) e 2 commits de documentação na fase. Ponto de retomada: F1-T05.
- **F1-T05 implementada (2026-11-18):** ficha criada, branch `feat/f1-t05-cadastro-manual`; `POST /jobs` com schemas validados (URL canônica, moeda ISO, faixa salarial, `posted_at` em UTC), `JobRepository` com consultas de dedup, `JobService` com as camadas 1/2 → `409` com `details` e camada 3 → `201` + `duplicates[]`, `BaseRepository` extraída para `app/repositories/base.py`, router registrado, 17 testes novos (9 unitários + 8 de API) e `docs/api.md` atualizado. Suíte **201 passed**; lint/format limpos.
- **F1-T05 integrada (2026-11-19 UTC):** commit `3279f7b`, **PR #13 mesclado** em `phase/01-nucleo-sem-ia` (`0a3ca2b`) com CI verde (run `44439397111`). `phase/01-nucleo-sem-ia` atualizada por fast-forward; `feat/f1-t05-cadastro-manual` preservada no remoto. Ponto de retomada: F1-T06.
- **F1-T06 implementada (2026-11-19 UTC):** ficha criada, branch `feat/f1-t06-importacao-csv`; `POST /jobs/import` em `multipart/form-data` com `file` + `source` opcional, `JobImportService` com validação por linha (erro com `row`/`field`/`message` sem abortar o lote), `ImportBatch` com contadores e `finished_at`, dedup pelas camadas 1/2 com pré-carga em blocos de 500 e um único `commit`, `prepare_job` extraído do `create_manual` e `docs/import-csv.md` criado. Suíte **219 passed**; o teste de 5 mil linhas fica em ~5 s (RNF-09).
- **F1-T06 integrada (2026-11-19 UTC):** commit `5af3d20`, **PR #14 mesclado** em `phase/01-nucleo-sem-ia` (`528a872`) com CI verde (run `44441646029`). `phase/01-nucleo-sem-ia` atualizada por fast-forward; `feat/f1-t06-importacao-csv` preservada no remoto. Ponto de retomada: F1-T07.
- **F1-T07 implementada (2026-11-19 UTC):** ficha criada, branch `feat/f1-t07-dedup-revisao`; camada 4 com RapidFuzz (`token_set_ratio`, limiar 85, só na mesma empresa), `JobDedupService` agrupando fingerprint e similaridade com a vaga mais antiga como referência, `GET /jobs/duplicates` (filtro por camada, limite e `truncated` com teto de 5 000 vagas), `POST /jobs/{job_id}/duplicate` (idempotente, 404/409/422) e `DELETE` para desfazer. Nada é apagado ou mesclado; nenhuma migração foi necessária. **34 testes novos**, suíte **253 passed**.
- **F1-T07 integrada (2026-11-19 UTC):** commit `7a8e4a7`, **PR #15 mesclado** em `phase/01-nucleo-sem-ia` (`430dc17`) com CI verde (run `44443291243`). `phase/01-nucleo-sem-ia` atualizada por fast-forward; `feat/f1-t07-dedup-revisao` preservada no remoto. Ponto de retomada: F1-T08.

---

## 3. O que falta na tarefa atual (lista concreta)

**Última tarefa integrada.** F4-T01, PR #48. [Ficha](tasks/FASE-04/F4-T01.md)
**Tarefa atual.** F4-T02, conforme os critérios do [backlog](BACKLOG.md).

- [x] Validar os quatro nós isoladamente e a passagem de um lote entre eles com PostgreSQL
- [ ] Abrir o PR da F4-T02 com autorização, conferir o CI, integrar e registrar o merge

- [x] Implementar e documentar o estado e testar as fronteiras dos nós
- [x] Abrir o PR #48, conferir o CI e integrar a F4-T01 na branch da fase
- [x] Conferir RF-10, validação antes de persistir e métricas por vaga
- [x] Confirmar a suíte local, reprodução offline e CI com respostas simuladas
- [x] Abrir o PR da fase para `develop` com autorização e conferir o CI da revisão final
- [x] Mesclar com histórico, confirmar o CI em `develop` e publicar `fase-03`
- [x] Atualizar o status, o backlog, a ficha, o README, o relatório e o changelog com o encerramento
- [x] Confirmar a base sincronizada e a suíte de partida da F3-T07
- [x] Consolidar e validar README, estratégia LLM, avaliação e relatório
- [x] Abrir o PR #45 da F3-T07 para a branch da fase com autorização
- [x] Confirmar o CI, integrar a tarefa e atualizar backlog e ficha
- [x] Conferir a base sincronizada e a suíte de partida da F3-T06
- [x] Medir a qualidade, o custo e a latência no golden set e registrar o funil
- [x] Abrir o PR #44 da F3-T06 para a branch da fase com autorização
- [x] Confirmar o CI, integrar a tarefa e atualizar backlog e ficha
- [x] Conferir a base sincronizada e a suíte de partida da F3-T05
- [x] Implementar e validar evidências, reparo e persistência da análise
- [x] Abrir o PR #43 da F3-T05 para a branch da fase com autorização
- [x] Confirmar o CI, integrar a tarefa e atualizar backlog e ficha
- [x] Conferir a base sincronizada e a suíte de partida da F3-T04
- [x] Implementar e validar o cache, as métricas e a migração reversível
- [x] Abrir o PR #42 da F3-T04 para a branch da fase com autorização
- [x] Confirmar o CI, integrar a tarefa e atualizar backlog e ficha
- [x] Conferir a base sincronizada e a suíte de partida da F3-T03
- [x] Implementar e validar a delimitação, a minimização e o prompt versionado
- [x] Abrir o PR #41 da F3-T03 para a branch da fase com autorização
- [x] Confirmar o CI, integrar a tarefa e atualizar backlog e ficha
- [x] Confirmar base sincronizada e suíte de partida da F3-T02
- [x] Implementar e validar schema, prompt e registro de versão
- [x] Abrir o PR #40 da F3-T02 para a branch da fase com autorização
- [x] Confirmar o CI, integrar a tarefa e atualizar backlog e ficha
- [x] Confirmar a base sincronizada e a suíte de partida da F3-T01
- [x] Implementar e testar o contrato, os provedores e as configurações
- [x] Abrir o PR #39 da F3-T01 para a branch da fase com autorização
- [x] Confirmar o CI, integrar a tarefa e atualizar backlog e ficha
- [x] Verificar RF-07 a RF-09, golden set e versão de score ativa
- [x] Registrar evidências do gate e preparar o changelog da Fase 2
- [x] Abrir o PR #37 da fase para `develop`
- [x] Confirmar o CI do PR #37 e integrar com autorização
- [x] Confirmar o CI em `develop` e publicar a tag anotada `fase-02`
- [x] Consolidar README, metodologia, avaliação e relatório da Fase 2
- [x] Conferir roteiro, relatório gerado e suíte de testes
- [x] Abrir o PR #36 para `phase/02-matching`
- [x] Confirmar o CI e integrar o PR #36 com autorização
- [x] Conferir a condição de adoção da F2-T07 no backlog e no relatório
- [x] Registrar o adiamento dos embeddings no ADR 0012
- [x] Abrir o PR #35 para `phase/02-matching`
- [x] Confirmar o CI e integrar o PR #35 com autorização
- [x] Curar o golden set e reproduzir métricas de extração e ranking
- [x] Confirmar o CI do PR e integrar a F2-T06 na branch da fase
- [x] Persistir e expor resultados de matching por candidato, vaga e versão
- [x] Confirmar o CI do PR e integrar a F2-T05 na branch da fase
- [x] Implementar e testar média ponderada, elegibilidade, explicação e versão
- [x] Confirmar o CI do PR e integrar a F2-T04 na branch da fase
- [x] Implementar e testar as regras eliminatórias e a avaliação de elegibilidade
- [x] Confirmar o CI do PR e integrar a F2-T03 na branch da fase
- [x] Extrair e persistir requisitos do cadastro manual e da importação, com suporte a reprocessamento
- [x] Confirmar o CI do PR e integrar a F2-T02 na branch da fase
- [x] Criar as branches da Fase 2 e da F2-T01 a partir de `develop` sincronizada
- [x] Implementar e testar o catálogo, o índice de aliases e o relatório
- [x] Confirmar o CI do PR e integrar a F2-T01 na branch da fase
- [x] Base da Fase 0 e higiene mescladas (`cbbeb65`, `ff60748`) ✅
- [x] Criar `phase/01-nucleo-sem-ia` a partir de `develop` e publicar ✅
- [x] Padronizar documentação (BACKLOG/STATUS/fichas) — PR #7 mesclado ✅
- [x] F1-T01 concluída: modelos, migração, testes de constraint e `data-model.md` (PR #8) ✅
- [x] F1-T02 dividida em `-a`/`-b` e decisões confirmadas (REST, JSONB, `POST /skills` na `-b`) ✅
- [x] F1-T02-a concluída: candidato/preferências, erros padronizados, testes e `api.md` (PR #9) ✅
- [x] F1-T02-b concluída e integrada: habilidades e experiências (PR #10) ✅
- [x] F1-T03 concluída e integrada: modelos e migração de `jobs`/`import_batches` (PR #11) ✅
- [x] F1-T04 concluída e integrada: normalização e canonização (PR #12) ✅
- [x] Criar ficha `F1-T05.md` e branch `feat/f1-t05-cadastro-manual` ✅
- [x] Schema/repositório/serviço de vaga manual (normaliza, calcula URL canônica/fingerprint) ✅
- [x] Rota REST de cadastro manual e detecção de duplicata certa/provável com aviso claro ✅
- [x] Testes unitários e de API; `docs/api.md` atualizado ✅
- [x] Commit da branch, CI verde e merge do PR #13 (com autorização) ✅
- [x] Criar ficha `F1-T06.md` e branch `feat/f1-t06-importacao-csv` ✅
- [x] Endpoint `POST /jobs/import` com relatório por linha e `import_batches` preenchido ✅
- [x] Idempotência (reimportar = 0 inserções) e 5 mil linhas dentro do RNF-09 ✅
- [x] `docs/import-csv.md`, `docs/api.md` e testes unitários/de API ✅
- [x] Commit da branch, CI verde e merge do PR #14 (com autorização) ✅
- [x] Criar ficha `F1-T07.md` e branch `feat/f1-t07-dedup-revisao` ✅
- [x] Camada 4 (similaridade) e agrupamento de fingerprint para revisão ✅
- [x] Endpoints de listar, confirmar (`duplicate_of_job_id`) e desfazer, sem apagar nada ✅
- [x] `docs/api.md`, ficha e testes unitários/de API ✅
- [x] Commit da branch, CI verde e merge do PR #15 (com autorização) ✅
- [x] Ficha, branch, endpoint de listagem, testes de API e documentação da F1-T08
- [x] Integrar a F1-T08 com CI verde (PR #18)
- [x] Modelos, migração, testes e documentação da F1-T09
- [x] Integrar a F1-T09 com CI verde (PR #19)
- [x] Criar ficha e branch da F1-T10, implementar rotas e filtro, validar suíte local e abrir o PR #20
- [x] Confirmar CI verde, mesclar o PR #20 e marcar o backlog
- [x] Criar ficha e branch da F1-T11
- [x] Implementar arquivamento e atalho para salvar uma vaga
- [x] Validar o fluxo `salva` → `planejada` → `aplicada` em um teste de integração
- [x] Publicar a F1-T11, confirmar o CI e integrar o PR #23
- [x] Criar a ficha e a branch da F1-T12, validar o cenário completo e medir a cobertura local
- [x] Publicar a F1-T12 e abrir o PR #24
- [x] Confirmar no CI os limites de cobertura da F1-T12
- [x] Revisar e integrar o PR #24, com CI verde na fase
- [x] Documentar a Fase 1, validar o roteiro e abrir o PR #25
- [x] Integrar o PR #25 após revisão, CI verde e autorização
- [x] Validar os critérios técnicos do F1-GATE e abrir o PR #26
- [x] Integrar o PR #26 após confirmar CI verde e autorização
- [x] Publicar a tag `fase-01` após confirmar o CI do merge em `develop`

### Itens fora do escopo da Fase 0 (resolvido)

- ~~`skills-lock.json` modificado e `.agents/skills/git-create-repo/` não versionado~~ → skill de terceiros ignorado no `.gitignore` e lock restaurado ao estado versionado (decisão registrada na seção 6).

---

## 4. Progresso por fase

| Fase | Estado | Tag | Gate |
|------|--------|-----|------|
| 0 — Fundação | concluída | `fase-00` (`cbbeb65`) | ✅ PR #4 mesclado com CI verde |
| 1 — Núcleo sem IA | concluída | `fase-01` (`bbea363`) | PR #26 mesclado com CI verde em `develop` |
| 2 — Matching | concluída | `fase-02` (`d30f0fc`) | PR #37 mesclado com CI verde em `develop` |
| 3 — Camada LLM | concluída | `fase-03` (`b7348cc`) | PR #46 mesclado com CI verde em `develop` |
| 4 — Orquestração (MVP v0.1.0) | em andamento | — | F4-T01 integrada |
| 5 — Assistente de currículo | não iniciada | — | — |
| 6 — Dashboard e analytics | não iniciada | — | — |
| 7 — Hardening e release (v1.0.0) | não iniciada | — | — |

*(Estados: não iniciada · em andamento · gate pendente · concluída)*

---

## 5. Problemas, bloqueios e dívida técnica

| Data | Tipo (bloqueio/bug/dívida/dúvida) | Descrição | Tarefa | Situação |
|------|-----------------------------------|-----------|--------|----------|
| 2026-11-14 | processo | PRs #5 e #6 foram abertos com base `main` em vez de `develop` (o GitHub mantém `main` como base padrão); corrigido por fast-forward de `develop` até `main`. **Mitigação:** abrir PRs sempre pela URL com base explícita (`/compare/develop...branch`) | F0-GATE | resolvido |
| 2026-11-14 | dívida | `app/main.py` usa `@app.on_event` (depreciado no FastAPI); migrar para `lifespan` | F1 | aberto |
| 2026-11-14 | dívida | `.agents/skills/alethe` versionado (~1,5 MB de assets) infla o repositório; reavaliar se precisa ficar versionado | — | aberto |
| 2026-11-17 | dívida | `skills.canonical_name` é único case-sensitive no banco; a API compara em minúsculas, mas concorrência ainda pode criar variações de caixa | F2-T01 | aberto |
| 2026-11-17 | dívida | `CandidateRepository.get` carrega preferências, skills e experiências em toda leitura de candidato; separar consultas se virar gargalo | F1-T03+ | aberto |
| 2026-11-18 | dívida | `canonical_url` não tem índice único: concorrência extrema pode criar duas vagas com a mesma URL canônica (a checagem do serviço é best-effort) | F1-T07 | aberto |
| 2026-11-19 | dívida | revisão de duplicatas varre no máximo 5 000 vagas por chamada (`truncated` avisa); catálogo maior exigirá varredura incremental ou paginação | F1-T08+ | aberto |
| 2026-11-19 | dívida | O Alembic detecta os índices `ix_candidate_experiences_candidate_id` e `ix_candidate_skills_skill_id` no banco, ausentes dos metadados ORM desde a revisão 002. A comparação antes e depois da F1-T09 apontou as mesmas diferenças | F1 | aberto |

*(Testes vermelhos ou `xfail` ativos devem ser listados aqui com o motivo.)*

---

## 6. Decisões tomadas (resumo; detalhe em ADR quando relevante)

| Data | Decisão | Motivo | ADR |
|------|---------|--------|-----|
| 2026-11-24 | Adiar embeddings multilíngues | A avaliação da F2-T06 fornece a linha de base determinística. A adoção exige evidência comparativa de ganho | [0012](adr/0012-adiar-embeddings-multilingues.md) |
| 2026-11-10 | Repositório GitHub: `JoaumPdr/jobpilot-ai` privado | Nome sugerido no PLANO.md, conta do JP | — |
| 2026-11-10 | Branch strategy: `main` → `develop` → `phase/*` | Modularidade, resiliência, gates por fase | 0009 (sincronização GitHub) |
| 2026-11-13 | Gerenciador de dependências: `uv` | Performance, lock file, grupos de dependências | 0008 |
| 2026-11-14 | Skills de agentes: versionar apenas o Alethe; skills de terceiros ficam fora do repo (`.gitignore`) | plugin de terceiros criava repositórios **públicos** por padrão e fixava outra conta do GitHub, inadequado a repo privado | — |
| 2026-11-14 | `ruff format --check` passa a rodar no CI | GUIA §B.8 exige lint **e** formatação; baseline aplicado antes de iniciar a F1 | — |
| 2026-11-16 | Divisão de responsabilidades documental: BACKLOG é fonte canônica das tarefas/critérios; ficha (`docs/tasks/`) detalha a execução; STATUS registra estado e retomada. Fichas são just-in-time e opcionais por complexidade; sem fichas retroativas para a F0 | eliminar ambiguidade e duplicação (o STATUS acumulava o plano da F1-T01) | — |
| 2026-11-16 | Perfil: e-mail único case-insensitive via `lower(email)`; `level` NULL = desconhecido; `years` em `candidate_skills` e `candidate_experiences` com CHECK; timestamps `TIMESTAMPTZ` com `now()` do servidor; `TEST_DATABASE_URL` isolada | decisões aprovadas pelo JP na preparação da F1-T01 | — |
| 2026-11-17 | `PATCH` de experiência revalida a faixa de datas combinando estado atual + payload e responde `422 invalid_data` (novo `InvalidDataError`) | a regra depende do estado gravado, não só do payload; separar `validation_error` (schema) de `invalid_data` (consistência) deixa o erro diagnosticável | — |
| 2026-11-17 | Vínculo por `canonical_name` cria a habilidade no catálogo quando ela não existe | permite registrar habilidades sem um passo prévio de curadoria; a duplicidade é fechada pela comparação case-insensitive na API | — |
| 2026-11-18 | Dedup do cadastro manual: camadas 1 (`source`+`external_id`) e 2 (`canonical_url`) → `409` com `details`; camada 3 (`fingerprint`) → `201` com `duplicates[]` | as duas primeiras identificam a mesma vaga; o fingerprint pode ser coincidência e a confirmação humana é da F1-T07 (nunca apagar/bloquear às cegas) | — |
| 2026-11-19 | Importação CSV usa `multipart/form-data` em `POST /jobs/import`, exige `title`/`company`/`description`/`url` e só aceita UTF-8 com vírgula | `url` é NOT NULL e base da dedup; adivinhar separador/codificação trocaria colunas silenciosamente (desvio do `PLANO.md` §6.1 documentado em `docs/import-csv.md`) | — |
| 2026-11-19 | Dedup da importação usa só as camadas 1 e 2 (contam em `duplicates`); o lote ignora a camada 3 | garante "reimportar o mesmo arquivo = 0 inserções"; o fingerprint provável continua na revisão humana da F1-T07 | — |
| 2026-11-19 | Importação em duas passadas com pré-carga de chaves em blocos de 500 e um único `commit` | uma consulta de dedup por linha levava ~32 s em 5 mil linhas; o alvo do RNF-09 é < 30 s (agora ~5 s) | — |
| 2026-11-19 | Camada 4 da dedup com RapidFuzz `token_set_ratio` (limiar 85) comparando títulos **na mesma empresa**, com grupos calculados sob demanda | implementa o `PLANO.md` §6.3 sem coluna nova; bloquear pela empresa evita ruído de cargos homônimos em empresas diferentes | — |
| 2026-11-19 | Revisão com `GET /jobs/duplicates`, `POST`/`DELETE /jobs/{job_id}/duplicate`; confirmação idempotente, `409` para trocar referência e `422` para cadeia/auto-referência | grava só `duplicate_of_job_id`, nunca apaga nem mescla; estados inconsistentes ficam diagnosticáveis | — |
| 2026-11-19 | Filtro por status da candidatura fica na F1-T10, após os modelos da F1-T09 | O JP aprovou entregar a listagem, a paginação e os demais filtros na F1-T08 | — |

---

## 7. Perguntas pendentes para o JP

- [ ] Confirmar se deseja configurar proteção de branch no GitHub (requer plano pago ou settings de admin) ou seguir por disciplina registrada no STATUS.md
- [ ] Decidir se `phase/00-fundacao` deve ser apagada após o gate (hoje preservada no remoto)

---

## 8. Observações

- **Base da Fase 2 (2026-11-23):** a tag `fase-01` continua apontando para o merge do gate em `bbea363`. A ponta de `develop` avançou para `e8d65d2` com o encerramento documental do [PR #27](https://github.com/JoaumPdr/jobpilot-ai/pull/27). Esse merge manteve a F2-T01 como ponto de retomada.
- **Divergência corrigida em 2026-11-18:** o §1 dizia último commit `396e851` (merge do PR #12) e push às 22:34 UTC; o Git/GitHub mostravam `05f69aa` ("docs(status): encerrar sessao...") com push às 22:35 UTC e CI verde (run `44191524901`). Era só documentação posterior ao merge; campos corrigidos. Nenhuma outra divergência.
- **Docker Desktop encerrou sozinho durante a sessão (2026-11-17):** a segunda execução completa de testes gerou 82 erros de conexão; o container `jobpilot-postgres` foi reiniciado (`docker compose up -d`) e a suíte voltou a verde (184 passed). Nenhuma falha de código.
- **Divergência corrigida em 2026-11-17:** o §1 dizia "F1-T02-b não iniciada; ficha a criar", mas o Git já tinha a ficha (`186b575`), a branch publicada e ~1.900 linhas de implementação não commitadas. Confiado o Git; STATUS corrigido e o trabalho revisado, testado e commitado (`d6513a6`, `eb7481d`). Nenhum outro campo divergia do remoto.
- **Divergência corrigida em 2026-11-16:** o §1 mostrava último commit `ff60748` e push 03:05 UTC; o Git/GitHub confirmam `9bc62d1` em `phase/01-nucleo-sem-ia`, push às 06:44 UTC (CI verde, run 43567810203). Corrigido; nenhum outro campo divergia.
- **MCP do GitHub:** indisponível nesta sessão; operações de consulta (PRs e CI) feitas com `gh` CLI autenticado. Git local segue como via de commits/push.
- Variáveis de ambiente novas desde a última sessão: `TEST_DATABASE_URL` (opcional; default deriva de `DATABASE_URL` + `_test`), documentada no `.env.example` e no README.
- **Divergência registrada (F1-T01):** o `PLANO.md` §5.1 prevê `years` em `candidate_skills`; a decisão de 2026-11-16 também alocou `years` em `candidate_experiences`. As duas colunas existem com CHECK `>= 0`; confirmar a duplicidade semântica antes da F1-T02.

---

## 9. Checklist de encerramento de sessão (conferir antes de parar)

- [x] Testes verdes **ou** falhas isoladas e listadas em §5
- [x] Adequação documental commitada, publicada e integrada pelo PR #16 com CI verde
- [x] Campos de sincronização da §1 atualizados (remoto, último push, PR aberto, CI no GitHub)
- [x] §1 e §3 atualizados com a próxima ação exata
- [x] `BACKLOG.md` marcado
- [x] Ficha da tarefa atual atualizada (se existir)
- [x] `RELATORIO.md` com nota curta da tarefa (se concluída) — a seção da Fase 1 será preenchida no gate da fase
- [x] `.env.example` sincronizado (se houve nova variável) — nenhuma variável nova
- [x] `uv.lock` commitado junto com o `pyproject.toml` (se houve mudança de dependência) — `python-multipart` (F1-T06) e `rapidfuzz` (F1-T07)
