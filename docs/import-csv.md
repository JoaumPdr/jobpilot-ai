# JobPilot AI — Modelo de CSV para importação de vagas

> Documento vivo. Descreve o arquivo aceito por `POST /jobs/import` (F1-T06).
> Alterou uma coluna ou regra? Atualize aqui e em `docs/api.md`.

## Formato do arquivo

- **Codificação:** UTF-8 (com ou sem BOM — o BOM do Excel é aceito).
- **Separador:** vírgula (`,`). Arquivos com `;` são rejeitados com erro claro.
- **Cabeçalho:** obrigatório na primeira linha. Nomes sem diferenciar caixa e
  com espaços nas pontas são aceitos (`" Title "` vira `title`).
- **Tamanho máximo:** 5 MB.
- **Linhas em branco:** o leitor de CSV as ignora; uma linha só com separadores
  é tratada como linha inválida.
- **Colunas desconhecidas:** ignoradas (planilhas costumam trazer colunas extras).

## Colunas

| Coluna | Obrigatória | Formato / regras |
|--------|-------------|------------------|
| `title` | sim | 1–300 caracteres |
| `company` | sim | 1–200 caracteres |
| `description` | sim | texto livre (o `PLANO.md` §6.1 já a exigia) |
| `url` | sim | `http`/`https`; sem esquema assume `https`. **Desvio documentado:** o `PLANO.md` §6.1 lista só as três primeiras como obrigatórias, mas o modelo exige `url` (NOT NULL) e ela é a base da dedup |
| `location` | não | até 200 caracteres |
| `work_mode` | não | texto livre (`remoto`, `home office`, `híbrido`, `presencial`…); desconhecido vira `desconhecido` |
| `seniority` | não | texto livre (`estágio`, `jr`, `pleno`, `sr`, `especialista`); desconhecido vira `desconhecido` |
| `employment_type` | não | até 100 caracteres |
| `salary_min` / `salary_max` | não | decimal com **ponto** (`12000.00`), `>= 0`, até 2 casas; `max >= min` |
| `currency` | não | ISO 4217 com 3 letras (`BRL`, `USD`); `brl` vira `BRL` |
| `source` | não | se vazia, usa o campo `source` do formulário ou `csv` |
| `external_id` | não | identificador na origem; vazio vira `null` |
| `posted_at` | não | ISO 8601 (`2026-11-10` ou `2026-11-10T09:00:00Z`); sem fuso é UTC |

## Exemplo

```csv
title,company,description,url,location,work_mode,seniority,source,external_id,salary_min,salary_max,currency,posted_at
Engenheira de Dados,Empresa X,Vaga para pipeline de dados,https://empresa.com/vagas/1,São Paulo,home office,Sênior,portal-a,ext-1,12000.00,18000.00,BRL,2026-11-10T09:00:00Z
Analista de Dados,Empresa Y,Análise e dashboards,https://empresa.com/vagas/2,Remoto,remoto,Pleno,portal-a,ext-2,8000.00,10000.00,BRL,2026-11-11
```

```bash
curl -X POST http://localhost:8000/jobs/import \
  -F "file=@vagas.csv" \
  -F "source=portal-a"
```

## O que acontece com cada linha

| Situação | Resultado |
|----------|-----------|
| Linha válida e inédita | vaga criada; conta em `inserted` |
| Mesmo `(source, external_id)` de uma vaga existente ou de uma linha anterior | não insere; conta em `duplicates` |
| Mesma `canonical_url` de uma vaga existente ou de uma linha anterior | não insere; conta em `duplicates` |
| Coluna obrigatória vazia, URL inválida, salário/data malformados | não insere; conta em `rejected` e entra em `errors` com `row`, `field` e `message` |
| **Arquivo** com cabeçalho incompleto, bytes não UTF-8 ou > 5 MB | `422 invalid_data`; **nenhum lote é criado** |

- `row` é a **linha física** do arquivo (cabeçalho = 1).
- Uma linha pode gerar mais de uma entrada em `errors`, mas conta **uma vez**
  em `rejected`.
- A dedup da importação usa as camadas 1 (`source` + `external_id`) e 2
  (`canonical_url`). A camada 3 (`fingerprint`, duplicata provável) **não**
  bloqueia a importação — ela e a camada 4 (similaridade) aparecem na revisão
  de duplicatas (`GET /jobs/duplicates`).
- Reimportar o mesmo arquivo resulta em `inserted = 0` (as linhas caem em
  `duplicates`), contanto que `source` e URLs não tenham mudado.
- As vagas novas recebem os requisitos reconhecidos na descrição dentro da
  transação do lote. Linhas duplicadas preservam os requisitos já gravados.
  [Requisitos extraídos](data-model.md#requisitos-extraídos-job_skills-f2-t02)

## Relatório de exemplo

```json
{
  "id": "9a8b7c6d-5e4f-4a3b-2c1d-0e9f8a7b6c5d",
  "source": "portal-a",
  "kind": "csv",
  "filename": "vagas.csv",
  "started_at": "2026-11-19T02:00:00Z",
  "finished_at": "2026-11-19T02:00:04Z",
  "total_rows": 3,
  "inserted": 2,
  "duplicates": 0,
  "rejected": 1,
  "errors": [
    { "row": 4, "field": "url", "message": "URL inválida: Esquema de URL não suportado: 'ftp'." }
  ]
}
```

## Armadilhas comuns

- **Excel pt-BR:** salvar como "CSV (separado por vírgulas)" e conferir se os
  decimais ficaram com ponto. `12.000,00` é rejeitado (o serviço não adivinha o
  formato pt-BR). Separador `;` também é rejeitado.
- **IDs externos:** se o portal muda o `external_id` de uma vaga, a camada 1 não
  a reconhece; a URL canônica (camada 2) ainda evita a duplicata.
- **Descrição longa:** o limite de 5 MB é do arquivo inteiro; descrições muito
  longas reduzem quantas linhas cabem no lote.
- **Performance:** 5 mil linhas são importadas em um único commit e com as
  chaves de dedup pré-carregadas em blocos; o alvo do RNF-09 é < 30 s.
