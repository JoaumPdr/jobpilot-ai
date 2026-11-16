# JobPilot AI — API

> Documento vivo. Atualizar sempre que uma rota mudar (gatilho do
> `GUIA_DOCS_E_GIT.md`). Estado atual: **F1-T02-a** — candidato e preferências.
> Habilidades e experiências entram na F1-T02-b.

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
| `not_found` | 404 | candidato ou preferências inexistentes |
| `conflict` | 409 | e-mail já usado por outro candidato |
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
  "created_at": "2026-11-16T20:00:00Z",
  "updated_at": "2026-11-16T20:00:00Z",
  "preferences": null
}
```

**Erros:** `409 conflict` (e-mail já cadastrado), `422 validation_error`.

### `GET /candidates/{candidate_id}`

Retorna o candidato e as preferências (ou `null`). **Erros:** `404`, `422`
(UUID inválido).

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

## Saúde

`GET /health` retorna `200` com o status da aplicação e do banco
(`healthy`/`degraded`). Não valida o contrato de perfil.

## Fora desta versão

- `POST /skills`, vínculo de habilidades e CRUD de experiências (F1-T02-b).
- Vagas, importação, matching, candidaturas, LLM e pipeline (fases seguintes).
