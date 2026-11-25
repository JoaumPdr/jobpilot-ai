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
