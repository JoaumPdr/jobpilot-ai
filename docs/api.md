# JobPilot AI — API

> Documento vivo. Atualizar sempre que uma rota mudar (gatilho do
> `GUIA_DOCS_E_GIT.md`). Cobre o núcleo da Fase 1: perfil e preferências,
> catálogo de vagas e candidaturas com histórico.

- **Base local:** `http://localhost:8000`
- **Formato:** corpos em JSON (`Content-Type: application/json`).
  O [envio de CSV](#post-jobsimport) usa `multipart/form-data`.
- **Autenticação:** nenhuma no MVP (single-user local; ADR 0007). As tabelas já
  carregam `candidate_id` para o futuro multiusuário.
- **Documentação interativa:** `GET /docs` (Swagger UI) e `GET /openapi.json`.
  Siga o [roteiro do README](../README.md#fluxo-da-fase-1) para percorrer a API.

## Convenções

### `request_id`

Toda resposta inclui o cabeçalho `X-Request-ID`. O mesmo valor aparece no corpo
dos erros, permitindo correlacionar com os logs estruturados.

### Formato de erro

```json
{
  "error": "validation_error",
  "message": "Dados inválidos na requisição.",
  "request_id": "5f0c2a3e-7f4b-4a59-9a0e-3f3f5b0f2f11",
  "details": [
    {
      "field": "education.0.end_date",
      "message": "end_date não pode ser anterior a start_date.",
      "type": "value_error"
    }
  ]
}
```

| `error` | HTTP | Quando |
|---------|------|--------|
| `validation_error` | 422 | corpo, path ou parâmetros de consulta inválidos (Pydantic) |
| `invalid_data` | 422 | regra de negócio inválida, como transição de candidatura ou cadeia de duplicatas, ou problema do arquivo inteiro na importação CSV |
| `not_found` | 404 | candidato, preferências, habilidade, experiência, vaga ou candidatura inexistentes |
| `conflict` | 409 | conflito de e-mail, habilidade, vaga ou candidatura já existente para o par candidato/vaga |
| `bad_request` / `method_not_allowed` / … | 4xx | erros HTTP do próprio FastAPI, padronizados |
| `internal_server_error` | 500 | falha inesperada (sem detalhes internos) |

`details` aparece em `422` (campos inválidos, regras de estado e arquivo CSV),
no `409` de vaga duplicada (camada que detectou e dados da vaga existente) e nos
erros de revisão de duplicatas (vaga já marcada, cadeia, auto-referência).

### UUIDs

Todos os identificadores são UUID v4. UUID malformado no path retorna 422.

---

## Candidato

### `POST /candidates`

Cria o candidato. `email` é opcional, normalizado (trim + minúsculas) e único
sem diferenciar caixa.

**Corpo**

```json
{
  "name": "Ana Silva",
  "email": "ana@example.com",
  "resume_text": "Currículo em texto livre...",
  "headline": "Engenheira de Dados",
  "education": [
    {
      "institution": "USP",
      "degree": "Bacharelado em Ciência da Computação",
      "field_of_study": "Computação",
      "start_date": "2018-02-01",
      "end_date": "2022-12-15",
      "description": "TCC em recuperação de informação."
    }
  ],
  "languages": [
    { "name": "Português", "level": "nativo" },
    { "name": "Inglês", "level": "fluente" }
  ]
}
```

| Campo | Tipo | Obrigatório | Regras |
|-------|------|-------------|--------|
| `name` | string | sim | 1–200 caracteres |
| `email` | string | não | e-mail válido; normalizado; único |
| `resume_text` | string | sim | não vazio |
| `headline` | string | não | até 200 caracteres |
| `education` | lista | não (default `[]`) | estrutura abaixo |
| `languages` | lista | não (default `[]`) | estrutura abaixo |

Campos desconhecidos são rejeitados (`extra="forbid"`) em todos os níveis.

**`education[]`:** `institution` e `degree` obrigatórios; `field_of_study`,
`start_date`, `end_date` e `description` opcionais. Datas em `YYYY-MM-DD` e
`end_date >= start_date` quando ambas existirem.

**`languages[]`:** `name` obrigatório e `level` em `básico`, `intermediário`,
`avançado`, `fluente` ou `nativo` (valores acentuados).

**Resposta `201`**

```json
{
  "id": "3f1c2a9e-6b7d-4c8a-9e10-2a4b6c8d0e12",
  "name": "Ana Silva",
  "email": "ana@example.com",
  "resume_text": "Currículo em texto livre...",
  "headline": "Engenheira de Dados",
  "education": [ { "institution": "USP", "degree": "Bacharelado em Ciência da Computação", "field_of_study": "Computação", "start_date": "2018-02-01", "end_date": "2022-12-15", "description": "TCC em recuperação de informação." } ],
  "languages": [ { "name": "Português", "level": "nativo" }, { "name": "Inglês", "level": "fluente" } ],
  "skills": [],
  "experiences": [],
  "created_at": "2026-11-16T20:00:00Z",
  "updated_at": "2026-11-16T20:00:00Z",
  "preferences": null
}
```

**Erros:** `409 conflict` (e-mail já cadastrado), `422 validation_error`.

### `GET /candidates/{candidate_id}`

Retorna o candidato com `preferences` (ou `null`), `skills` e `experiences`.
As listas são carregadas em uma consulta por relação (`selectinload`), sem N+1.
**Erros:** `404`, `422` (UUID inválido).

### `PATCH /candidates/{candidate_id}`

Atualiza **apenas** os campos enviados. `education`/`languages` são substituídos
por inteiro quando presentes; lista vazia limpa a seção.

```json
{
  "headline": "Tech Lead",
  "languages": [{ "name": "Espanhol", "level": "intermediário" }]
}
```

- `null` em `name`, `resume_text`, `education` ou `languages` → `422`.
- `"email": null` limpa o e-mail; e-mail de outro candidato → `409`.
- Corpo `{}` não altera nada e retorna `200`.

### `DELETE /candidates/{candidate_id}`

Remove o candidato e, por `ON DELETE CASCADE`, suas preferências, habilidades e
experiências. O catálogo `skills` é preservado.

**Resposta:** `204` sem corpo. **Erros:** `404`, `422`.

---

## Preferências (1:1)

### `GET /candidates/{candidate_id}/preferences`

Retorna as preferências. **Erros:** `404` se o candidato não existe **ou** se as
preferências ainda não foram criadas.

```json
{
  "id": "9a8b7c6d-5e4f-4a3b-2c1d-0e9f8a7b6c5d",
  "candidate_id": "3f1c2a9e-6b7d-4c8a-9e10-2a4b6c8d0e12",
  "desired_titles": ["Engenheira de Dados"],
  "locations": ["São Paulo", "Remoto"],
  "work_modes": ["remoto", "híbrido"],
  "seniority_levels": ["pleno", "sênior"],
  "min_salary": "12000.00",
  "knockout_rules": { "exclude_companies": ["Empresa X"] },
  "created_at": "2026-11-16T20:05:00Z",
  "updated_at": "2026-11-16T20:05:00Z"
}
```

### `PUT /candidates/{candidate_id}/preferences`

Substitui o conjunto inteiro (idempotente) e cria a linha se não existir.
Campos omitidos voltam ao default (`[]`, `null` ou `{}`).

```json
{
  "desired_titles": ["Engenheira de Dados", "Analista de Dados"],
  "locations": ["São Paulo"],
  "work_modes": ["remoto"],
  "seniority_levels": ["pleno"],
  "min_salary": "12000.00",
  "knockout_rules": { "exclude_companies": ["Empresa X"] }
}
```

| Campo | Tipo | Regras |
|-------|------|--------|
| `desired_titles`, `locations`, `work_modes`, `seniority_levels` | lista de strings | itens aparados; vazios descartados; até 200 caracteres por item |
| `min_salary` | número decimal | `>= 0`, até 12 dígitos e 2 casas; sem coluna de moeda nesta fase |
| `knockout_rules` | objeto JSON | chaves livres até a F2-T03 |

**Erros:** `404` (candidato inexistente), `422` (valores inválidos).

---

## Habilidades

O catálogo `skills` é compartilhado entre perfis (e, na Fase 2, entre vagas).
O vínculo `candidate_skills` guarda nível, anos e evidência do candidato para
aquela habilidade.

### `GET /skills?q=`

Lista o catálogo em ordem alfabética (sem diferenciar caixa). `q` é opcional e
filtra o nome canônico por trecho.

**Resposta `200`**

```json
[
  {
    "id": "7c6d5e4f-3a2b-4c1d-9e8f-0a1b2c3d4e5f",
    "canonical_name": "Python",
    "category": "linguagem",
    "aliases": ["py", "python3"]
  }
]
```

### `POST /skills`

Cria uma habilidade canônica. Nome repetido (sem diferenciar caixa) → `409`.

```json
{
  "canonical_name": "Python",
  "category": "linguagem",
  "aliases": ["py", "python3"]
}
```

| Campo | Tipo | Obrigatório | Regras |
|-------|------|-------------|--------|
| `canonical_name` | string | sim | 1–200 caracteres; nome aparado |
| `category` | string | não | até 100 caracteres; texto livre até a F2-T01 |
| `aliases` | lista de strings | não (default `[]`) | itens aparados; vazios descartados; até 200 caracteres |

**Resposta `201`:** o registro criado (mesmo formato do `GET /skills`).
**Erros:** `409 conflict`, `422 validation_error`.

### `GET /candidates/{candidate_id}/skills`

Lista os vínculos do candidato, com a habilidade canônica aninhada.
**Erros:** `404` (candidato inexistente), `422`.

```json
[
  {
    "id": "1a2b3c4d-5e6f-4a7b-8c9d-0e1f2a3b4c5d",
    "candidate_id": "3f1c2a9e-6b7d-4c8a-9e10-2a4b6c8d0e12",
    "skill_id": "7c6d5e4f-3a2b-4c1d-9e8f-0a1b2c3d4e5f",
    "skill": { "id": "7c6d5e4f-3a2b-4c1d-9e8f-0a1b2c3d4e5f", "canonical_name": "Python", "category": "linguagem", "aliases": ["py", "python3"] },
    "level": "intermediário",
    "years": 3,
    "evidence_note": "Projeto de ingestão em produção.",
    "created_at": "2026-11-16T20:10:00Z"
  }
]
```

### `POST /candidates/{candidate_id}/skills`

Vincula uma habilidade ao candidato. Informe **exatamente um** entre `skill_id`
e `canonical_name`:

- `skill_id`: busca no catálogo; inexistente → `404`.
- `canonical_name`: reaproveita a habilidade pelo nome (sem diferenciar caixa)
  ou **cria** no catálogo se ela ainda não existir.

```json
{ "canonical_name": "Python", "level": "intermediário", "years": 3 }
```

| Campo | Tipo | Regras |
|-------|------|--------|
| `skill_id` | UUID | alternativa a `canonical_name` |
| `canonical_name` | string | 1–200 caracteres; alternativa a `skill_id` |
| `level` | string | `iniciante`, `intermediário` ou `avançado`; `null` = desconhecido |
| `years` | inteiro | `>= 0` |
| `evidence_note` | string | livre |

**Resposta `201`:** o vínculo criado (formato acima).
**Erros:** `404` (candidato/habilidade), `409` (par já vinculado ou nome
duplicado), `422 validation_error`.

### `PATCH /candidates/{candidate_id}/skills/{skill_id}`

Atualiza **apenas** os campos enviados do vínculo. `null` limpa `level`,
`years` ou `evidence_note`.

```json
{ "years": 5 }
```

**Resposta `200`:** o vínculo atualizado.
**Erros:** `404` (candidato ou vínculo inexistente), `422 validation_error`.

### `DELETE /candidates/{candidate_id}/skills/{skill_id}`

Remove o vínculo; a habilidade **permanece** no catálogo.
**Resposta:** `204` sem corpo. **Erros:** `404`, `422`.

---

## Experiências

`end_date` nula representa o vínculo atual.

### `GET /candidates/{candidate_id}/experiences`

Lista as experiências da mais recente para a mais antiga (`start_date` desc).
**Erros:** `404` (candidato inexistente), `422`.

```json
[
  {
    "id": "5e4d3c2b-1a0f-4e9d-8c7b-6a5f4e3d2c1b",
    "candidate_id": "3f1c2a9e-6b7d-4c8a-9e10-2a4b6c8d0e12",
    "company": "Empresa X",
    "role": "Engenheira de Dados",
    "start_date": "2020-01-01",
    "end_date": "2022-12-31",
    "description": "Construção de pipelines.",
    "skills_used": ["Python", "SQL"],
    "years": 3,
    "created_at": "2026-11-16T20:15:00Z",
    "updated_at": "2026-11-16T20:15:00Z"
  }
]
```

### `POST /candidates/{candidate_id}/experiences`

```json
{
  "company": "Empresa X",
  "role": "Engenheira de Dados",
  "start_date": "2020-01-01",
  "end_date": "2022-12-31",
  "description": "Construção de pipelines.",
  "skills_used": ["Python", "SQL"],
  "years": 3
}
```

| Campo | Tipo | Obrigatório | Regras |
|-------|------|-------------|--------|
| `company` | string | sim | 1–200 caracteres |
| `role` | string | sim | 1–200 caracteres |
| `start_date` | data | sim | `YYYY-MM-DD` |
| `end_date` | data ou `null` | não | `>= start_date`; `null` = vínculo atual |
| `description` | string | não | livre |
| `skills_used` | lista de strings | não (default `[]`) | itens aparados; vazios descartados |
| `years` | inteiro | não | `>= 0` (anos naquela função) |

**Resposta `201`:** a experiência criada.
**Erros:** `404` (candidato inexistente), `422 validation_error` (inclui
`end_date` anterior a `start_date`).

### `PATCH /candidates/{candidate_id}/experiences/{experience_id}`

Atualiza **apenas** os campos enviados.

- `null` explícito em `company`, `role`, `start_date` ou `skills_used` → `422`.
- `"end_date": null` marca o vínculo como atual.
- A faixa de datas é revalidada combinando o estado atual com o payload; se
  ficar inválida → `422 invalid_data`.

```json
{ "role": "Tech Lead", "end_date": null }
```

**Resposta `200`:** a experiência atualizada.
**Erros:** `404` (candidato/experiência inexistentes), `422 validation_error`
ou `422 invalid_data`.

### `DELETE /candidates/{candidate_id}/experiences/{experience_id}`

**Resposta:** `204` sem corpo. **Erros:** `404`, `422`.

---

## Vagas

### `GET /jobs`

Lista vagas da mais recente para a mais antiga por data de cadastro
(`created_at`). Vagas cadastradas no mesmo instante são ordenadas por UUID
decrescente, o que mantém a ordem entre páginas enquanto o catálogo e os
filtros forem os mesmos.

| Parâmetro | Regra |
|-----------|-------|
| `q` | Trecho literal no título, na empresa ou na descrição. Ignora maiúsculas/minúsculas e preserva distinções de acento. |
| `work_mode` | `remoto`, `híbrido`, `presencial` ou `desconhecido`. |
| `location` | Trecho literal da localização, sem distinguir maiúsculas/minúsculas. |
| `seniority` | `estágio`, `júnior`, `pleno`, `sênior`, `especialista` ou `desconhecido`. |
| `source` | Nome exato da fonte cadastrada. |
| `posted_from`, `posted_to` | Limites inclusivos e opcionais para `posted_at`. Use data e hora com fuso, como `2026-11-18T12:00:00Z`. Vagas sem data de publicação ficam fora quando houver qualquer limite. |
| `application_status` | Status atual da candidatura. Aceita `salva`, `planejada`, `aplicada`, `entrevista`, `oferta`, `rejeitada` ou `encerrada`. |
| `candidate_id` | UUID do candidato. Obrigatório com `application_status`. Quando usado sozinho, mantém a listagem geral. |
| `include_archived` | Use `true` para incluir arquivadas. Padrão `false`. |
| `include_duplicates` | Use `true` para incluir duplicatas confirmadas. Padrão `false`. |
| `limit`, `offset` | Tamanho da página de 1 a 100 (padrão 50) e quantidade de registros a pular (padrão 0). |

Os filtros são combinados por interseção. Por exemplo, `GET /jobs?q=dados&work_mode=remoto&limit=20`
lista a primeira página das vagas remotas que correspondem ao texto.
Com `candidate_id` e `application_status`, a página inclui somente vagas com
candidatura desse candidato no status informado.

**Resposta `200`.** O corpo contém `items` (vagas no mesmo formato `JobRead`
usado pelo cadastro), `limit`, `offset` e `has_more`. Quando `has_more` for
`true`, mantenha os filtros e use `offset + limit` para a próxima página.
Páginas sem resultados retornam `items: []` e `has_more: false`.

**Erro `422 validation_error`.** Parâmetros desconhecidos, valores inválidos,
intervalo invertido ou filtro de status sem `candidate_id`.

### `POST /jobs`

Cadastra uma vaga. O texto é guardado normalizado para exibição (acentos e caixa
preservados, espaços colapsados), `work_mode`/`seniority` são convertidos para
os valores internos e a URL gera `canonical_url` (sem parâmetros de rastreio,
fragmento, barra final ou porta padrão).

Os requisitos reconhecidos na descrição são gravados com a vaga. O extrator
usa seções e gatilhos em português e inglês e resolve termos pela taxonomia.
O formato da resposta continua igual. [Requisitos extraídos](data-model.md#requisitos-extraídos-job_skills-f2-t02)

```json
{
  "title": "Engenheira de Dados",
  "company": "Empresa X",
  "url": "https://empresa.com/vagas/123?utm_source=linkedin",
  "location": "São Paulo",
  "work_mode": "home office",
  "seniority": "Sênior",
  "description": "Texto livre.",
  "source": "manual",
  "external_id": null,
  "salary_min": "12000.00",
  "salary_max": "18000.00",
  "currency": "brl",
  "posted_at": "2026-11-10T09:00:00Z"
}
```

| Campo | Tipo | Obrigatório | Regras |
|-------|------|-------------|--------|
| `title` | string | sim | 1–300 caracteres; espaços colapsados |
| `company` | string | sim | 1–200 caracteres |
| `description` | string | não | texto livre; `null` se vazia |
| `location` | string | não | até 200 caracteres |
| `work_mode` | string | não | livre (`remoto`, `home office`, `híbrido`, `presencial`…); desconhecido vira `desconhecido` |
| `seniority` | string | não | livre (`júnior`, `sr`, `estágio`…); desconhecido vira `desconhecido` |
| `employment_type` | string | não | até 100 caracteres |
| `salary_min`, `salary_max` | decimal | não | `>= 0`, até 2 casas; `max >= min` |
| `currency` | string | não | ISO 4217 (3 letras); `brl` vira `BRL` |
| `source` | string | não (default `manual`) | até 100 caracteres |
| `external_id` | string | não | até 200 caracteres; vazio vira `null` |
| `url` | string | sim | `http`/`https` (sem esquema assume `https`) |
| `posted_at` | data/hora | não | sem fuso é interpretado como UTC |

**Deduplicação em camadas** (`PLANO.md` §6.3):

1. `(source, external_id)` igual → **`409 conflict`** com `details[0].layer = "external_id"`.
2. `canonical_url` igual → **`409 conflict`** com `details[0].layer = "canonical_url"`.
3. `fingerprint` igual (empresa + título + localização normalizados) → **`201`**
   com a vaga criada e `duplicates[]` listando as parecidas (`layer = "fingerprint"`).

Nada é apagado nem marcado automaticamente: a confirmação via
`duplicate_of_job_id` é feita na revisão de duplicatas (abaixo). A camada 4
(similaridade textual) só é avaliada nessa revisão.

**Resposta `201`**

```json
{
  "job": {
    "id": "3f1c2a9e-6b7d-4c8a-9e10-2a4b6c8d0e12",
    "title": "Engenheira de Dados",
    "company": "Empresa X",
    "description": "Texto livre.",
    "location": "São Paulo",
    "work_mode": "remoto",
    "seniority": "sênior",
    "employment_type": null,
    "salary_min": "12000.00",
    "salary_max": "18000.00",
    "currency": "BRL",
    "source": "manual",
    "external_id": null,
    "url": "https://empresa.com/vagas/123?utm_source=linkedin",
    "canonical_url": "https://empresa.com/vagas/123",
    "fingerprint": "9c1f...64 caracteres hexadecimais",
    "posted_at": "2026-11-10T09:00:00Z",
    "collected_at": "2026-11-18T12:00:00Z",
    "import_batch_id": null,
    "is_archived": false,
    "duplicate_of_job_id": null,
    "created_at": "2026-11-18T12:00:00Z",
    "updated_at": "2026-11-18T12:00:00Z"
  },
  "duplicates": []
}
```

Exemplo de `duplicates[]` (duplicata provável):

```json
[
  {
    "job_id": "7c6d5e4f-3a2b-4c1d-9e8f-0a1b2c3d4e5f",
    "title": "Engenheira de Dados",
    "company": "Empresa X",
    "source": "manual",
    "canonical_url": "https://empresa.com/vagas/123",
    "layer": "fingerprint"
  }
]
```

Exemplo de `409`:

```json
{
  "error": "conflict",
  "message": "Já existe uma vaga com a mesma URL canônica.",
  "request_id": "5f0c2a3e-7f4b-4a59-9a0e-3f3f5b0f2f11",
  "details": [
    {
      "job_id": "7c6d5e4f-3a2b-4c1d-9e8f-0a1b2c3d4e5f",
      "layer": "canonical_url",
      "title": "Engenheira de Dados",
      "company": "Empresa X",
      "source": "manual",
      "canonical_url": "https://empresa.com/vagas/123"
    }
  ]
}
```

**Erros:** `409 conflict` (duplicata certa/quase certa), `422 validation_error`
(URL inválida, faixa de salário invertida, moeda fora do ISO, campo desconhecido).

### `POST /jobs/import`

Importa um arquivo CSV em um lote auditável. **Linha inválida não derruba o
lote:** ela entra em `errors` com o número da linha e o campo, e o restante é
processado normalmente. O modelo do arquivo (colunas, formatos e armadilhas)
está em [`docs/import-csv.md`](import-csv.md).

- **Corpo:** `multipart/form-data`.
  - `file` (obrigatório): arquivo `.csv` em UTF-8 (com ou sem BOM), separado por
    vírgula, com cabeçalho.
  - `source` (opcional): origem usada quando a linha não traz a coluna `source`.
    Sem ele e sem a coluna, o lote usa `csv`.
- **Limite:** 5 MB por arquivo.

```bash
curl -X POST http://localhost:8000/jobs/import \
  -F "file=@vagas.csv" \
  -F "source=portal-a"
```

**Deduplicação:** usa as camadas 1 (`source` + `external_id`) e 2
(`canonical_url`). Linha repetida — em relação ao banco ou a outra linha do
mesmo arquivo — **não insere** e conta em `duplicates`. A camada 3
(`fingerprint`) não bloqueia importação. Consequência prática: reimportar o
mesmo arquivo resulta em `inserted = 0`.

**Resposta `201`**

```json
{
  "id": "9a8b7c6d-5e4f-4a3b-2c1d-0e9f8a7b6c5d",
  "source": "portal-a",
  "kind": "csv",
  "filename": "vagas.csv",
  "started_at": "2026-11-19T02:00:00Z",
  "finished_at": "2026-11-19T02:00:04Z",
  "total_rows": 3,
  "inserted": 1,
  "duplicates": 1,
  "rejected": 1,
  "errors": [
    { "row": 4, "field": "url", "message": "URL inválida: Esquema de URL não suportado: 'ftp'." }
  ]
}
```

| Campo | Significado |
|-------|-------------|
| `total_rows` | linhas de dados lidas (sem o cabeçalho) |
| `inserted` | vagas criadas; ficam ligadas ao lote por `import_batch_id` |
| `duplicates` | linhas puladas pela dedup (camadas 1/2) |
| `rejected` | linhas rejeitadas por erro de validação |
| `errors[]` | um item por problema: `row` (linha física, cabeçalho = 1), `field` e `message` |

`total_rows = inserted + duplicates + rejected`. Uma linha pode gerar mais de um
item em `errors`, mas conta uma única vez em `rejected`.

**Erros:**

| Situação | Resposta |
|----------|----------|
| arquivo > 5 MB, bytes não UTF-8, sem cabeçalho ou sem coluna obrigatória | `422 invalid_data` com `details[0].field = "file"` — **nenhum lote é criado** |
| `file` ausente no formulário | `422 validation_error` (FastAPI) |
| linha com coluna obrigatória vazia, URL inválida, salário/data malformados | `201` com a linha em `errors` e contada em `rejected` |

O problema do arquivo inteiro é distinguido do problema de linha justamente por
não criar lote: nada foi importado, e o usuário corrige o arquivo e reenvia.

### Revisão de duplicatas

O que as camadas 1 e 2 não bloquearam na escrita vira **sugestão** aqui. A
revisão agrupa vagas por dois critérios:

| `layer` | Critério |
|---------|----------|
| `fingerprint` | mesmo hash de empresa + título + localização (camada 3) |
| `similarity` | títulos parecidos (nota ≥ 85/100) **na mesma empresa** (camada 4) |

Nada é apagado ou mesclado automaticamente: confirmar apenas grava
`duplicate_of_job_id` na vaga marcada, que continua existindo e aponta para a
original.

#### `GET /jobs/duplicates`

Lista os grupos suspeitos. Parâmetros opcionais:

- `layer`: `fingerprint` ou `similarity` — filtra pelo critério.
- `limit`: 1–200 (default `50`) — máximo de grupos devolvidos.

```json
{
  "groups": [
    {
      "layer": "similarity",
      "similarity": 95.2,
      "canonical_job_id": "3f1c2a9e-6b7d-4c8a-9e10-2a4b6c8d0e12",
      "jobs": [
        {
          "id": "3f1c2a9e-6b7d-4c8a-9e10-2a4b6c8d0e12",
          "title": "Engenheiro de Dados Sênior",
          "company": "Empresa X",
          "location": "São Paulo",
          "source": "portal-a",
          "canonical_url": "https://empresa.com/vagas/1",
          "posted_at": "2026-11-10T09:00:00Z",
          "created_at": "2026-11-18T12:00:00Z",
          "duplicate_of_job_id": null
        },
        {
          "id": "7c6d5e4f-3a2b-4c1d-9e8f-0a1b2c3d4e5f",
          "title": "Engenheiro de Dados Sr.",
          "company": "Empresa X",
          "location": "Remoto",
          "source": "portal-b",
          "canonical_url": "https://outro.com/vagas/9",
          "posted_at": null,
          "created_at": "2026-11-19T01:00:00Z",
          "duplicate_of_job_id": null
        }
      ]
    }
  ],
  "scanned_jobs": 128,
  "truncated": false
}
```

- `jobs` vem da vaga mais antiga para a mais recente; `canonical_job_id` é a mais
  antiga e a referência natural para confirmar.
- Vagas arquivadas e já marcadas como duplicata **não** entram na varredura.
- Cada vaga aparece em no máximo um grupo (o fingerprint tem prioridade sobre a
  similaridade, para não repetir o mesmo par).
- `scanned_jobs` informa quantas vagas foram comparadas. `truncated = true`
  significa que o catálogo passou do teto da varredura (5 000 vagas): reduza o
  catálogo ou revise por partes.
- **Erros:** `422 validation_error` para `layer`/`limit` inválidos.

#### `POST /jobs/{job_id}/duplicate`

Confirma que a vaga do path é duplicata de outra. **Nada é apagado.**

```json
{ "duplicate_of_job_id": "3f1c2a9e-6b7d-4c8a-9e10-2a4b6c8d0e12" }
```

**Resposta `200`:** a vaga marcada, no formato de `JobRead`, com
`duplicate_of_job_id` preenchido.

| Situação | Resposta |
|----------|----------|
| vaga ou referência inexistente | `404 not_found` |
| vaga já marcada como duplicata de **outra** | `409 conflict` (desfaça antes) |
| a referência já é duplicata de outra (cadeia) | `422 invalid_data` |
| a vaga aponta para si mesma | `422 invalid_data` |
| repetir a mesma confirmação | `200` idempotente |

#### `DELETE /jobs/{job_id}/duplicate`

Desfaz a marcação e devolve a vaga à revisão. **Resposta:** `204` sem corpo.
**Erros:** `404` (vaga inexistente), `422 invalid_data` (vaga não está marcada).

### `POST /jobs/{job_id}/archive`

Arquiva a vaga sem corpo de requisição. Retorna `200` com a vaga e
`is_archived: true`, inclusive se ela já estiver arquivada. Uma vaga ausente
retorna `404 not_found`.

O arquivamento preserva a vaga e suas candidaturas. Para encontrá-la em
`GET /jobs`, use `include_archived=true`.

### `POST /candidates/{candidate_id}/jobs/{job_id}/save`

Salva a vaga para o candidato sem corpo de requisição. Retorna `201` com a
candidatura em `salva` e grava a entrada inicial no histórico. Use o `id`
retornado para mudar o status pela rota de candidaturas.

Candidato ou vaga ausente retorna `404 not_found`. Se o par já tiver uma
candidatura, o atalho retorna `409 conflict` e preserva o status e o histórico.

---

## Saúde

`GET /health` retorna `200`. Com conexão ao banco, `status` e
`database.status` são `healthy`. Se a conexão falhar, o status da aplicação
é `degraded` e `database.status` é `unhealthy`.

## Candidaturas

| Método e rota | Resposta |
|---|---|
| `POST /candidates/{candidate_id}/applications` | `201` com a candidatura criada em `salva`. Envie `job_id` e, opcionalmente, `notes`. Candidato ou vaga ausente retorna `404`. Uma candidatura existente para o mesmo par retorna `409`. |
| `GET /candidates/{candidate_id}/applications` | `200` com as candidaturas do candidato, das mais recentes às mais antigas. Candidato ausente retorna `404`. |
| `GET /candidates/{candidate_id}/applications/{application_id}` | `200` com a candidatura e seu `status_history`, do mais antigo ao mais recente. Candidatura ausente para esse candidato retorna `404`. |
| `PATCH /candidates/{candidate_id}/applications/{application_id}` | `200` com a candidatura atualizada. Envie `status`, `notes` ou ambos. Candidatura ausente para esse candidato retorna `404`. |

A candidatura contém `id`, `candidate_id`, `job_id`, `status`, `notes`,
`applied_at`, `created_at` e `updated_at`. Para limpar as observações, envie
`{"notes": null}`. A edição de observações preserva o histórico de status.

O fluxo principal é `salva` → `planejada` → `aplicada` → `entrevista` → `oferta`.
De qualquer um desses estados, é possível ir para `rejeitada` ou `encerrada`,
que são terminais. Ao chegar pela primeira vez a `aplicada`, a API preenche
`applied_at`. Uma transição fora do fluxo retorna `422 invalid_data`.
Atualizar o status para o mesmo valor ou enviar `status: null` também
retorna esse erro.

O histórico registra a criação com `from_status: null` e cada transição com
`from_status`, `to_status`, `changed_at` e `note`. Para acrescentar uma nota ao
evento, envie `transition_note` junto de `status`. Enviar apenas a nota
sem o novo status retorna `422 invalid_data`.

```json
{"status": "planejada", "transition_note": "Revisar currículo."}
```

## Fora desta versão

- Matching, LLM e pipeline.
