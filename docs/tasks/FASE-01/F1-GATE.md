# F1-GATE — Gate de saída da Fase 1

- Integração de `phase/01-nucleo-sem-ia` em `develop` pelo [PR #26](https://github.com/JoaumPdr/jobpilot-ai/pull/26).
- Critérios no [backlog](../../BACKLOG.md) e no [plano mestre](../../PLANO.md), §11.
- Revisão de referência validada localmente. `8c852a7`.

| Requisito | Evidência na suíte |
|---|---|
| RF-01 | [Perfil](../../../tests/api/test_profile_api.py), [habilidades](../../../tests/api/test_profile_skills_api.py) e [experiências](../../../tests/api/test_profile_experiences_api.py). |
| RF-02 | [Preferências do perfil](../../../tests/api/test_profile_api.py#L230) e [validação da configuração de filtros eliminatórios](../../../tests/unit/test_profile_schemas.py#L139). A aplicação das regras está prevista na F2-T03. |
| RF-03 | [Cadastro manual](../../../tests/api/test_jobs_api.py) e [importação CSV com relatório por linha](../../../tests/api/test_jobs_import_api.py). |
| RF-04 | [Detecção no cadastro](../../../tests/api/test_jobs_api.py) e [revisão, confirmação e reversão](../../../tests/api/test_jobs_duplicates_api.py). |
| RF-05 | [Listagem, filtros e paginação](../../../tests/api/test_jobs_listing_api.py) e [filtro por status da candidatura](../../../tests/api/test_applications_api.py#L183). |
| RF-06 | [Máquina de estados](../../../tests/unit/test_application_transitions.py) e [histórico gravado pela API](../../../tests/api/test_applications_api.py). |

## Verificação

- [x] [Fluxo de ponta a ponta](../../../tests/api/test_phase_one_flow.py) com PostgreSQL e zero novas vagas ao reimportar o CSV.
- [x] 360 testes aprovados, com cobertura de 96,60% em `app` (mínimo de 70%) e 95,33% em `app/services` (mínimo de 85%).
- [x] [Roteiro do README](../../../README.md#fluxo-da-fase-1), [API](../../api.md) e [modelo de dados](../../data-model.md) revisados na F1-T13.
- [x] [CI da branch da fase](https://github.com/JoaumPdr/jobpilot-ai/actions/runs/44608937267) verde na revisão de referência, incluindo Ruff e ciclo de migração Alembic.
- [x] PR da fase aberto para `develop`.
- [ ] Confirmar CI no head do PR, obter autorização e mesclar com histórico.
- [ ] Confirmar CI em `develop` e publicar a tag anotada `fase-01` para o merge validado.

```shell
uv run coverage run --source=app -m pytest
uv run coverage report --precision=2 --fail-under=70
uv run coverage report --precision=2 --include='app/services/*' --fail-under=85
```
