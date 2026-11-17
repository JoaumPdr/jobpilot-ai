# JobPilot AI — API

> Documento vivo. Atualizar sempre que uma rota mudar (gatilho do
> `GUIA_DOCS_E_GIT.md`). Estado atual: **F1-T02-b** — candidato, preferências,
> habilidades e experiências.

- **Base local:** `http://localhost:8000`
- **Formato:** JSON (`Content-Type: application/json`)
- **Autenticação:** nenhuma no MVP (single-user local; ADR 0007). As tabelas já
  carregam `candidate_id` para o futuro multiusuário.
- **Documentação interativa:** `GET /docs` (Swagger UI) e `GET /openapi.json`.

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
| `validation_error` | 422 | payload/path inválido (Pydantic) |
| `invalid_data` | 422 | regra que só pode ser checada com o estado atual (ex.: faixa de datas no `PATCH` de experiência) |
| `not_found` | 404 | candidato, preferências, habilidade ou experiência inexistentes |
| `conflict` | 409 | e-mail, nome de habilidade ou par candidato/habilidade já usados |
| `bad_request` / `method_not_allowed` / … | 4xx | erros HTTP do próprio FastAPI, padronizados |
| `internal_server_error` | 500 | falha inesperada (sem detalhes internos) |

`details` só aparece em 422.

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

## Saúde

`GET /health` retorna `200` com o status da aplicação e do banco
(`healthy`/`degraded`). Não valida o contrato de perfil.

## Fora desta versão

- Vagas, importação, matching, candidaturas, LLM e pipeline (fases seguintes).
