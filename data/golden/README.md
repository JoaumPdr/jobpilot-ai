# Golden set de matching

O conjunto contém 34 vagas distintas de tecnologia, com 17 descrições
adaptadas em inglês e 17 em português brasileiro. Cada `source_row` é o
índice da linha no split `train`, configuração `default` do corpus inglês
do Djinni. A revisão usada aparece em `matching.json`.
[Corpus MIT na revisão usada](https://huggingface.co/datasets/lang-uk/recruitment-dataset-job-descriptions-english/tree/b56a6054c10f1266a141e37c8df66c79ff2863af)

Fonte de dados: Djinni, 2020–2023. Cite Nazarii Drushchak e Mariana
Romanyshyn, *Introducing the Djinni Recruitment Dataset: A Corpus of
Anonymized CVs and Job Postings*, UNLP 2024. O código do JobPilot e
o corpus de origem têm seus próprios termos de licenciamento.
[Publicação original](https://aclanthology.org/2024.unlp-1.2/)

## Curadoria

- Amostra de conveniência de vagas de dados, backend, frontend, full stack,
  mobile, infraestrutura, QA, sistemas e gestão. Cada linha de origem
  aparece uma vez.
- As descrições são adaptações técnicas curtas dos anúncios. Mantêm os
  tópicos e o sentido dos trechos selecionados, com alguns títulos de seção
  variados. Trate o texto PT-BR como tradução e adaptação de origem inglesa.
- A curadoria reteve termos técnicos e marcadores de requisito. Os textos
  publicados omitem nomes de empresas, pessoas, contatos, URLs, locais,
  salários e texto institucional. Nenhum currículo do corpus foi usado.
- Os rótulos foram atribuídos manualmente antes de executar o avaliador.
  Cada termo recebe o tipo obrigatório ou desejável conforme o trecho.
  Habilidades mencionadas como alternativas no mesmo requisito entram
  como menções individuais. Menções que só descrevem o ambiente ficam fora.
  Os rótulos cobrem também termos que a taxonomia ainda não reconhece.
- A compatibilidade é uma leitura ordinal de cada descrição diante do
  perfil sintético de dados e backend em `matching.json`. Alta indica
  aderência ao núcleo técnico. Média indica aderência parcial ou evidência
  técnica limitada. Baixa indica uma lacuna importante na tecnologia
  central da vaga. As ausências do perfil foram declaradas no cenário.

O conjunto mede o comportamento nestas descrições selecionadas e com
um perfil sintético. A adaptação de vagas de uma única fonte e a
rotulagem por um único avaliador limitam a generalização das métricas.
[Relatório gerado](../../docs/evaluation.md)

## Revisão de evidências

- `GS-007` preserva literalmente a preferência por AWS, mas o extrator a
  classificou como obrigatória. O gatilho `preferable` não está entre os
  padrões reconhecidos.
- `GS-005` recupera o diferencial de Node.js com evidência válida. Os
  requisitos sob `Skills and experience` ficaram de fora da extração.
- `GS-033` tem requisitos com sinal explícito de tipo. Jira e Scrum ficaram
  fora da extração porque não constam da taxonomia avaliada.
