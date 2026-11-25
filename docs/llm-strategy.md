# Estratégia LLM

## Prompt e contrato de análise de vaga

O prompt `job-analysis-v1` orienta a análise de vagas para revisão humana. A aplicação carrega o arquivo versionado e acrescenta o JSON Schema gerado pelo mesmo modelo Pydantic usado na validação. Mantenha as versões anteriores em `prompts/` e crie uma versão nova ao alterar as instruções ou o contrato. [Prompt v1](../prompts/job-analysis-v1.txt) · [Schema e carregador](../app/llm/job_analysis.py)

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
