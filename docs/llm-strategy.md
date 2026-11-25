# Estratégia LLM

## Prompt e contrato de análise de vaga

O prompt ativo `job-analysis-v2` orienta a análise de vagas para revisão humana. A aplicação carrega o arquivo versionado e acrescenta o JSON Schema gerado pelo mesmo modelo Pydantic usado na validação. Mantenha as versões anteriores em `prompts/` e crie uma versão nova ao alterar as instruções ou o contrato. [Prompt v2](../prompts/job-analysis-v2.txt) · [Prompt v1](../prompts/job-analysis-v1.txt) · [Schema e carregador](../app/llm/job_analysis.py)

| Campo | Conteúdo |
|---|---|
| `job_id` | UUID da vaga analisada, conferido com o UUID esperado pela aplicação |
| `matched_skills` | Requisitos com presença confirmada pelo perfil |
| `missing_skills` | Requisitos com ausência explícita no perfil |
| `unknown_requirements` | Requisitos vagos, contraditórios ou com evidência insuficiente |
| `recommendation`, `explanation` | Textos fundamentados nos dados e nas incertezas |
| `evidence` | Trechos literais vinculados a um requisito e à fonte `job` ou `profile` |

O prompt manda usar somente fatos explícitos. Se o perfil silenciar sobre uma habilidade, ela fica entre os requisitos sem confirmação. A recomendação serve de apoio à decisão do usuário e preserva o score determinístico. [Política de privacidade](privacy-and-sources.md#3-dados-não-confiáveis)

O parser recebe o mesmo objeto de prompt usado na chamada e registra sua versão em `prompt_version` junto à análise validada. O schema rejeita campos extras. O serviço previsto na F3-T05 verifica os trechos contra as fontes e reclassifica itens sem evidência. [Backlog da Fase 3](BACKLOG.md#fase-3--camada-llm--branch-phase03-camada-llm--tag-fase-03)

## Delimitação e minimização da entrada

`prepare_job_analysis_input` monta a mensagem de sistema a partir do prompt versionado. A mensagem de usuário contém um objeto JSON com `job_id`, `job` e `profile`. A serialização mantém aspas, quebras de linha e texto apresentado como instrução dentro de `job.description`. Os testes conferem essa separação com um provedor falso. [Preparação da entrada](../app/services/llm_input.py)

A aplicação limita a fonte da descrição a 8.000 caracteres, normaliza as quebras de linha e remove caracteres de controle, exceto tabulações e quebras, além das marcas invisíveis de formatação. `job.description_truncated` sinaliza quando a fonte ultrapassa o limite.

O perfil contém `skills` para as habilidades que o matching associou à vaga e `confirmed_absent` para ausências explícitas. As duas listas usam nomes canônicos do catálogo local, sem trechos do currículo ou campos de identificação do candidato. O prompt orienta o modelo a tratar requisitos fora dessas listas como sem confirmação. [Política de privacidade](privacy-and-sources.md)

## Cache e métricas

`LLMCacheService.get_or_generate` usa SHA-256 sobre o provedor, o modelo, a versão e as mensagens efetivas. O serviço revalida a análise ao reutilizá-la. Em caso de geração, a gravação ocorre depois de o validador aceitar o resultado. O banco guarda a análise e as métricas; as mensagens da chamada entram somente no cálculo da chave. [Serviço de cache](../app/services/llm_cache.py) · [Modelo de dados](data-model.md#cache-de-análises-llm-llm_cache-f3-t04)

O PostgreSQL serializa pedidos da mesma chave com um bloqueio transacional. A transação própria do cache mantém o bloqueio até concluir a leitura ou a geração. Se o provedor, a validação ou a gravação falhar, a transação libera o bloqueio e permite nova tentativa.

Cada invocação de `LLMProvider.complete` gera um evento `llm_call` com provedor, modelo, versão do prompt, status, tokens informados, custo estimado em USD e latência monotônica em milissegundos. A duração inclui as tentativas internas do adaptador. O provedor falso e o Ollama local têm custo por chamada igual a zero. Tarifas e contagens desconhecidas ficam nulas. Uma leitura do cache gera `llm_cache_hit`; o log registra metadados operacionais.
