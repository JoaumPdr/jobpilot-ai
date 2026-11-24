# Metodologia do score determinístico

A versão inicial é `deterministico-v1`. O cálculo recebe os requisitos
extraídos da vaga, as habilidades declaradas no perfil e o resultado dos
filtros eliminatórios. Pode receber também ausências verificadas pelo
chamador. [Plano, §7](PLANO.md)

## Da vaga ao ranking

O cadastro manual e a importação extraem requisitos obrigatórios e desejáveis
em português e inglês e gravam as habilidades reconhecidas com os trechos da
descrição em `job_skills`. Quando a vaga ainda não tem requisitos persistidos,
o cálculo usa a descrição para extrair os requisitos daquela avaliação.
[Modelo de dados](data-model.md#requisitos-extraídos-job_skills-f2-t02)

O cálculo aplica as preferências eliminatórias do candidato, compara os
requisitos com as habilidades declaradas e grava as evidências em `job_matches`.
O ranking usa avaliações persistidas. Após alterar o perfil ou as ausências
confirmadas, solicite um novo cálculo para atualizar o resultado da versão
ativa. Uma ausência confirmada é fornecida a cada cálculo. [Rotas de matching](api.md#matching)

## Elegibilidade e correspondência

O cálculo verifica os eliminatórios primeiro. Uma vaga com flag devolve
`score = None` e as flags da decisão. [Filtros eliminatórios](tasks/FASE-02/F2-T03.md)

| Nível | Fator | Evidência |
|---|---:|---|
| Exata | 1,0 | O nome do requisito e o nome declarado coincidem após normalizar caixa, acentos e espaços |
| Alias | 0,7 | Os nomes normalizados diferem e resolvem para a mesma habilidade na taxonomia |
| Relacionada | 0,7 | Uma relação direta na configuração liga o requisito à habilidade declarada |
| Ausente | 0 | A ausência foi confirmada explicitamente e consta na entrada |
| Não confirmada | — | As entradas fornecidas deixam o requisito sem confirmação |

O cálculo busca correspondência exata, depois alias. Se houver ausência
confirmada para o requisito, ela prevalece sobre uma relação indireta de
habilidade. As relações são direcionais e só se aplicam a pares declarados
no arquivo. Por exemplo, PySpark oferece evidência parcial de Apache Spark.
O par inverso exigiria uma declaração própria. [Configuração versionada](../data/matching/scoring.toml)

## Fórmula

`score = Σ(peso × fator) / Σ(peso)`, na escala de 0 a 1. Cada requisito
obrigatório pesa 3 e cada desejável pesa 1. Uma ausência confirmada soma
zero ao numerador e mantém o peso no denominador. Um requisito não confirmado
continua na explicação, fora dos dois termos da média. A confiança do
extrator continua disponível como evidência. A média usa os pesos da versão.

Por exemplo, Python obrigatório atendido por nome, PostgreSQL obrigatório
atendido pelo alias Postgres, Apache Spark desejável atendido por PySpark e
Docker desejável com ausência confirmada resultam em
`(3 × 1 + 3 × 0,7 + 1 × 0,7 + 1 × 0) / (3 + 3 + 1 + 1) = 0,725`.
Um requisito adicional de Kubernetes sem confirmação permanece listado.
Sem peso confirmado, o resultado é `None`. Com ausências confirmadas e sem
correspondências, o resultado é zero.

## Explicação e versão

O resultado contém a versão, o numerador, o denominador e os requisitos
agrupados em atendidos, ausentes e não confirmados. Cada entrada preserva
o tipo, o trecho original e a confiança do extrator. Uma correspondência
também expõe a habilidade declarada que a justificou. O cálculo usa
aritmética decimal com 28 dígitos de precisão e arredondamento para o par
mais próximo, com ordenação estável nas explicações.

Use `load_score_calculator()` do serviço de score para montar o cálculo com
a configuração e a taxonomia do repositório. Uma mudança de pesos, fatores
ou regras que altere resultados exige incrementar `scoring_version`.
O resultado carrega a versão usada em cada avaliação.

O armazenamento mantém uma linha por candidato, vaga e versão. Um novo
cálculo atualiza o resultado da versão ativa. O detalhe permite consultar
as versões anteriores preservadas. [Rotas de matching](api.md#matching)

## Avaliação e sinal semântico

O golden set mede a extração e a concordância ordinal do ranking com rótulos
manuais. A F2-T07 manteve `deterministico-v1` como linha de base e adiou os
embeddings multilíngues até uma comparação demonstrar ganho mensurável.
[Relatório de avaliação](evaluation.md) · [ADR 0012](adr/0012-adiar-embeddings-multilingues.md)
