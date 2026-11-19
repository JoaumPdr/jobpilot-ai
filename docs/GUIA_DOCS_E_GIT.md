# JobPilot AI — Guia de Documentação, Branches e Commits

> Idioma: **PT-BR** (docs, comentários, commits). Este guia vira `docs/GUIA_DOCS_E_GIT.md` no repositório.

---

## PARTE A — Documentação

### A.1 Mapa de documentos

| Arquivo | Para quê | Quando atualizar |
|---------|----------|------------------|
| `AGENTS.md` | Ponto de entrada para agentes, com links para as fontes canônicas | Quando mudar a ordem de retomada ou o mapa de instruções |
| `README.md` | Porta de entrada: objetivo, status, instalação, configuração, execução, arquitetura resumida, roadmap | A cada fase fechada e a cada mudança de instalação/execução |
| `design.md` | Arquitetura em detalhe: camadas, fluxos, decisões e o *porquê* | Quando a arquitetura ou um fluxo mudar |
| `RELATORIO.md` | Diário técnico por fase: o que foi feito, problemas, soluções, métricas, aprendizados | Ao fechar cada tarefa (nota curta) e cada fase (seção completa) |
| `docs/PLANO.md` | Plano-mestre (não editar sem registrar a mudança em ADR) | Só por decisão explícita |
| `docs/BACKLOG.md` | Tarefas, dependências, aceitação, estado (`[ ]`/`[x]`) | A cada tarefa |
| `docs/STATUS.md` | **Estado vivo** para retomada | A cada sessão (obrigatório) |
| `docs/ALETHE_INSTRUCOES.md` | Regras de execução do agente | Raramente |
| `docs/GUIA_DOCS_E_GIT.md` | Este guia | Raramente |
| `docs/adr/NNNN-titulo.md` | Registro de decisões arquiteturais | Sempre que houver decisão relevante |
| `docs/api.md` | Endpoints, exemplos de requisição/resposta, erros | Ao criar/alterar rota |
| `docs/data-model.md` | Tabelas, relações, constraints, enums, diagrama | Ao criar/alterar migração |
| `docs/matching-methodology.md` | Metodologia de score, pesos, níveis, `scoring_version`, limitações | Fase 2 em diante, a cada mudança de regra |
| `docs/llm-strategy.md` | Provedor, prompts, custo, cache, segurança, privacidade | Fase 3 em diante |
| `docs/evaluation.md` | Golden set, métricas, resultados comparativos | Fases 2, 3 e 4 |
| `docs/pipeline.md` | Grafo LangGraph: estado, nós, transições, falhas | Fase 4 em diante |
| `docs/privacy-and-sources.md` | Privacidade (LGPD), política de fontes de vagas e checklist de termos de uso | Fase 0 (base) e a cada nova fonte |
| `docs/tasks/FASE-XX/Fx-Tyy.md` | Ficha de cada tarefa | Ao iniciar tarefa que exija planejamento detalhado (política no `BACKLOG.md`) |
| `CHANGELOG.md` | Mudanças por versão (tags) | Ao criar tag |
| `.github/PULL_REQUEST_TEMPLATE.md` | Modelo de PR (seção B.5) | F0-T01; raramente depois |

### A.2 Gatilhos: "mudei X → atualizo Y"

| Mudança | Documentos a atualizar |
|---------|------------------------|
| Nova rota / alteração de contrato | `docs/api.md`, README (se afetar uso) |
| Nova migração / tabela / coluna | `docs/data-model.md` |
| Nova variável de ambiente | `.env.example`, README (seção configuração) |
| Mudança de regra de score/peso | `docs/matching-methodology.md`, incrementar `scoring_version`, `RELATORIO.md` |
| Novo prompt ou mudança de prompt | `prompts/` (nova `prompt_version`), `docs/llm-strategy.md` |
| Mudança de fluxo/nó do pipeline | `docs/pipeline.md`, `design.md` |
| Decisão de arquitetura | Novo ADR + `design.md` |
| Fase fechada | `RELATORIO.md`, `README.md` (status/roadmap), `CHANGELOG.md`, tag |

### A.3 README.md — conteúdo obrigatório

1. Nome, **link do repositório no GitHub e badge de CI**, descrição em 2–3 linhas e **objetivo do repositório** (portfólio + demonstração/estudo de engenharia de dados e **orquestração multiagente**, desenvolvido com apoio da Alethe e arquivos de instruções).
2. **Princípios** (recomenda e prepara; usuário decide; sem envio automático; sem inventar fatos).
3. Status atual (fase) e roadmap resumido com links.
4. Pré-requisitos (incluindo **`uv`** e Docker), instalação (`uv sync`), configuração (`.env`), execução, testes e lint (sempre via `uv run`).
5. Arquitetura resumida com diagrama e link para `design.md`.
6. Estrutura de pastas.
7. Como contribuir/retomar o desenvolvimento (aponta para `docs/STATUS.md` e `docs/ALETHE_INSTRUCOES.md`).
8. Aviso de privacidade e política de fontes.
9. Licença.

**Melhoria contínua da documentação:** a partir da Fase 1, adicionar diagramas (Mermaid ou ASCII) e, na Fase 6, capturas de tela do dashboard; manter o README dinâmico (badges de CI, status da fase).

### A.4 Padrão de comentários e docstrings

- **PT-BR, didáticos, para dev júnior.** Explicar o **porquê** da decisão, não repetir o que o código já diz.
- Todo módulo começa com docstring: *o que é*, *por que existe*, *quem usa*.
- Toda função pública: o que faz, parâmetros, retorno, exceções e **um exemplo curto** quando a regra for sutil (ex.: dedup, score).
- Marcar decisões não óbvias com `# POR QUÊ:`; pendências com `# TODO(Fx-Tyy):` referenciando a tarefa.
- Regras de negócio (score, transições de status) devem citar o trecho correspondente do `PLANO.md` ou do ADR.

### A.5 Modelo de ADR (`docs/adr/NNNN-titulo.md`)

```text
# ADR NNNN — Título curto
- Data: AAAA-MM-DD
- Status: proposto | aceito | substituído por ADR XXXX
## Contexto
O problema e as restrições.
## Decisão
O que foi decidido, em uma ou duas frases.
## Alternativas consideradas
Opção A (prós/contras), Opção B (prós/contras).
## Consequências
O que melhora, o que piora, o que precisa ser revisitado.
```

### A.6 Modelo de nota no RELATORIO.md (por tarefa)

```text
### Fx-Tyy — Título (AAAA-MM-DD)
- O que foi feito:
- Decisões e motivos:
- Problemas encontrados e soluções:
- Testes adicionados / cobertura:
- Pendências / dívida técnica:
```

---

## PARTE B — Git: branches, commits e releases

### B.1 Modelo de branches

```
main                      ← sempre estável; só recebe merges de develop; recebe tags
 └── develop              ← integração; só recebe branches de fase concluídas (gate verde)
      ├── phase/00-fundacao
      ├── phase/01-nucleo-sem-ia
      │     ├── feat/f1-t01-modelos-perfil
      │     ├── feat/f1-t02-import-csv
      │     └── fix/f1-t02-linha-vazia
      ├── phase/02-matching
      ├── phase/03-camada-llm
      ├── phase/04-orquestracao
      ├── phase/05-assistente-curriculo
      ├── phase/06-dashboard
      └── phase/07-hardening-release
```

**Por que assim (modularidade e resiliência):**

- Cada **tarefa** vive numa branch curta → se os tokens acabarem no meio dela, o dano é isolado e a branch do ponto de parada está no remoto.
- Cada **fase** vive numa branch longa → o estado "fase em andamento" nunca contamina `develop`/`main`.
- `main` e `develop` só avançam com gate verde → sempre há uma versão boa para voltar.

**Convenção de nomes:**

| Tipo | Padrão | Exemplo |
|------|--------|---------|
| Fase | `phase/NN-nome-curto` | `phase/01-nucleo-sem-ia` |
| Tarefa (nova funcionalidade) | `feat/fN-tNN-descricao` | `feat/f1-t04-deduplicacao` |
| Correção | `fix/fN-tNN-descricao` | `fix/f1-t04-fingerprint-acentos` |
| Docs | `docs/fN-tNN-descricao` | `docs/f0-t07-adrs-iniciais` |
| Refatoração | `refactor/fN-tNN-descricao` | `refactor/f2-t02-extrator` |
| Testes | `test/fN-tNN-descricao` | `test/f2-t06-golden-set` |

### B.2 Preparação inicial e remoto no GitHub (F0-T01)

Passos (executar uma vez; o repositório local e o remoto nascem juntos):

1. Criar o repositório **no GitHub da conta do JP** pelo MCP do GitHub (nome sugerido: `JoaumPdr/jobpilot-ai`; confirmar com o JP), **privado**, branch padrão `main`, com descrição curta.
2. Inicializar o repositório local, configurar `origin` apontando para o repositório criado e fazer o **primeiro commit** já com `.gitignore`, licença e o pacote de documentos em `docs/`. Enviar `main`.
3. Criar `develop` a partir de `main` e enviá-la.
4. Criar `phase/00-fundacao` a partir de `develop` e enviá-la.
5. Configurar proteção de branch em `main` e `develop` (PR obrigatório e CI verde) — se disponível no plano do GitHub; caso contrário, seguir a regra por disciplina e registrar isso no `STATUS.md`.
6. Criar no GitHub os **milestones** das fases (Fase 0 a Fase 7) e labels básicos (`fase-N`, `feat`, `fix`, `docs`, `bloqueada`). O `BACKLOG.md` continua sendo a fonte da verdade das tarefas; issues no GitHub são um espelho **opcional**.
7. Adicionar `.github/PULL_REQUEST_TEMPLATE.md` com o modelo da seção B.5.
8. Habilitar push frequente: toda branch de tarefa é enviada ao remoto logo após o primeiro commit (rotina completa na seção B.9).
9. Verificar: `git status -sb` sem divergência e as três branches visíveis no GitHub. Registrar o link do repositório no `README.md` e no `STATUS.md`.

### B.3 Fluxo de integração

1. Branch de tarefa criada **a partir da branch da fase**.
2. Ao atender os critérios de aceitação, abrir **PR no GitHub** da tarefa → fase via MCP autenticado ou `gh`, usando **merge com histórico** (preserva commits pequenos, útil para retomada). Mesclar só com **CI verde no remoto**.
3. Ao cumprir o **gate da fase**: PR `phase/NN-*` → `develop`.
4. Ao fechar marcos de release (`v0.1.0` no fim da Fase 4, `v1.0.0` na Fase 7): PR `develop` → `main` + **tag anotada publicada no remoto**; criar também um *release* no GitHub com o trecho do `CHANGELOG.md`.
5. Tag a cada fase fechada: `fase-00`, `fase-01`, … **sempre enviadas ao GitHub** (permite voltar rapidamente a qualquer ponto bom).

### B.4 Commits (Conventional Commits em PT-BR)

Formato: `tipo(escopo): descrição no imperativo, minúscula, sem ponto final`

| Tipo | Uso |
|------|-----|
| `feat` | Nova funcionalidade |
| `fix` | Correção de bug |
| `docs` | Somente documentação |
| `test` | Testes |
| `refactor` | Refatoração sem mudar comportamento |
| `chore` | Tooling, dependências, configuração, **`chore(wip)` para trabalho incompleto** |
| `ci` | Pipeline de CI |
| `perf` | Desempenho |
| `build` | Empacotamento/Docker |

Escopos sugeridos: `perfil`, `vagas`, `import`, `dedup`, `filtros`, `candidaturas`, `matching`, `llm`, `pipeline`, `curriculo`, `dashboard`, `infra`, `docs`.

Exemplos:

- `feat(import): validar linhas do csv e registrar erros por linha`
- `test(dedup): cobrir fingerprint com acentos e caixa diferente`
- `docs(api): documentar endpoints de candidaturas`
- `chore(wip): f1-t04 dedup por url canonica feita; falta similaridade e testes de integracao`

**Regras:**

- Um commit = uma mudança coesa e que compila/testa (exceto `chore(wip)` registrado).
- Corpo do commit (opcional) explica o *porquê* quando não for óbvio.
- Referenciar a tarefa no corpo ou no rodapé: `Tarefa: F1-T04`.
- Nunca commitar `.env`, dumps com dados reais, currículo real ou chaves.

### B.5 Modelo de PR (tarefa → fase)

```text
## Tarefa
Fx-Tyy — título

## O que mudou
- ...

## Critérios de aceitação
- [ ] ...

## Testes
- Novos:
- Suíte completa verde: sim/não

## Docs atualizadas
- [ ] api.md  [ ] data-model.md  [ ] RELATORIO.md  [ ] STATUS.md  [ ] outros:

## Checklist de segurança/privacidade
- [ ] Sem segredos  [ ] Sem PII em logs  [ ] Saída de LLM validada (se aplicável)

## Riscos / pendências
```

### B.6 Versionamento

- Versionamento semântico em tags: `v0.1.0` (MVP, fim da Fase 4), `v0.2.0` (Fase 5), `v0.3.0` (Fase 6), `v1.0.0` (Fase 7).
- `CHANGELOG.md` atualizado a cada tag (formato "Adicionado / Alterado / Corrigido").

### B.7 Higiene do repositório

- `.gitignore` desde o primeiro commit: `.env`, `.venv`, caches, `__pycache__`, dumps, arquivos de dados reais. **`uv.lock` e `.python-version` são versionados** (não colocar no `.gitignore`).
- `.env.example` sempre sincronizado.
- Dados reais (currículo, vagas) **nunca** versionados; golden set apenas **anonimizado**.
- Pre-commit (e **pre-push**, ver B.9) com: Ruff (lint + formato), verificação de arquivos grandes, detecção de segredos e **verificação de que o `uv.lock` está sincronizado com o `pyproject.toml`**.
- Mudança de dependência = um único commit contendo `pyproject.toml` + `uv.lock` (ex.: `chore(infra): adicionar httpx como dependência de desenvolvimento`).

### B.8 CI (GitHub Actions)

Pipeline mínimo a partir da F0-T06, executado em todo PR e push nas branches `phase/*`, `develop` e `main`:

1. Instalar o `uv` e as dependências com **`uv sync --locked`** (com cache do `uv`); o job falha se o `uv.lock` estiver desatualizado.
2. Lint e formatação (Ruff), executados com `uv run`.
3. Tipagem (se adotada).
4. Testes (`uv run pytest`) com serviço PostgreSQL; relatório de cobertura com **limite mínimo** configurado.
5. Teste de migração (upgrade/downgrade).

Testes que chamam LLM real ficam **fora** do CI padrão (marcador opt-in).

---

### B.9 Sincronização com o GitHub — rotina de desenvolvimento

**Princípio:** nenhum trabalho confirmado fica só na máquina. O GitHub é o backup e o ponto de retomada.

**Ferramentas.** Use o MCP do GitHub quando estiver disponível e autenticado. Use `gh` autenticado para PRs e CI quando o MCP estiver indisponível e registre a alternativa no `STATUS.md`. Use `git` local para commits, branches, merge local e push. Credenciais ficam nos mecanismos de autenticação das ferramentas.

| Momento | Ação | Verificação |
|---------|------|-------------|
| Início de sessão | `git fetch --all --prune`; se o remoto estiver à frente, `git pull --ff-only` | `git status -sb` sem `behind`; sem divergência |
| Nova branch de tarefa | Primeiro commit → **primeiro push** com upstream | Branch aparece no GitHub |
| Durante a tarefa | Push após cada commit significativo (ciclo verde) | Sem `ahead` ao pausar |
| Tarefa concluída | PR tarefa → fase pelo MCP ou `gh`. O CI roda no GitHub | CI verde antes de mesclar |
| Fase concluída | PR fase → `develop`; tag `fase-NN` publicada | Tag visível no GitHub; CI verde em `develop` |
| Release | PR `develop` → `main`; tag `vX.Y.Z` + release no GitHub | `main` com a tag e o `CHANGELOG.md` atualizado |
| Fim de sessão | Commit (`chore(wip)` se incompleto) + push | Árvore limpa, sem `ahead`, `STATUS.md` com o estado de sincronização |

**Proteções de rotina**

- Hook de **pre-push** (via pre-commit) rodando Ruff e os testes unitários rápidos, para não enviar código quebrado.
- Detecção de segredos antes do commit e antes do push.
- **Sem force push** em `main`, `develop` e `phase/*`. Em branch de tarefa própria, só `--force-with-lease` e com registro.
- Apagar branches remotas, tags ou o repositório, mudar visibilidade e alterar proteções exigem autorização do JP. Branches de tarefa permanecem até a fase fechar; a limpeza é decisão do JP.

**Se algo der errado**

| Situação | O que fazer |
|----------|-------------|
| Push rejeitado (remoto à frente) | `git fetch`, integrar com `git pull --ff-only` ou rebase **apenas da própria branch de tarefa**; nunca force |
| Histórico divergiu | Parar, registrar no `STATUS.md` e avisar o JP |
| MCP sem permissão ou autenticação | Avisar o JP e registrar a alternativa no `STATUS.md`. Usar `gh` ou `git` local somente nas operações cobertas pelas permissões de cada ferramenta |
| CI vermelho no GitHub | Corrigir na branch da tarefa e novo push; não mesclar |
| Segredo enviado ao remoto | Avisar o JP para **revogar a chave imediatamente**; só então tratar o histórico com a orientação dele |

**Visibilidade:** o repositório começa **privado**. A decisão de torná-lo público (objetivo de portfólio) é do JP, após varredura de segredos e conferência de que nenhum dado real (currículo, vagas) foi versionado.
