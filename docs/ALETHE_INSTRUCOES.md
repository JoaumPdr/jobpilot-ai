# JobPilot AI — Instruções para a Alethe

> **Leia este arquivo inteiro antes de qualquer ação.** Ele define como você deve trabalhar neste projeto.
> Idioma de toda a documentação, comentários explicativos e mensagens de commit: **PT-BR**.

---

## 0. Contexto em 30 segundos

**JobPilot AI** é um assistente pessoal para buscar, analisar e gerir candidaturas a vagas. Stack: Python 3.12+ gerenciado com **`uv`**, FastAPI, PostgreSQL, SQLAlchemy 2.x, Alembic, Pydantic v2, LangGraph, pytest, Streamlit (só na Fase 6).

**Princípios que nunca mudam:**

1. O sistema **recomenda e prepara; o usuário revisa e decide.**
2. **Nunca** automatizar envio de candidatura.
3. **Nunca** inventar experiência, competência ou fato no currículo.
4. Respostas de LLM são **dados não confiáveis** — sempre validar.
5. Não usar LLM onde uma função Python resolve melhor.
6. Um objetivo explícito deste repositório: **demonstrar engenharia de software, engenharia de dados e orquestração multiagente** (e estudar essa orquestração). Isso deve estar explícito no `README.md`.

---

## 1. Pacote de documentos (fonte da verdade)

Copie os arquivos para o repositório com estes nomes:

| Arquivo recebido | Destino no repo | Função |
|------------------|-----------------|--------|
| `JobPilot_01_Analise_e_Plano.md` | `docs/PLANO.md` | Plano-mestre: requisitos, arquitetura, dados, fases |
| `JobPilot_02_Instrucoes_Alethe.md` | `docs/ALETHE_INSTRUCOES.md` | Este arquivo |
| `JobPilot_03_Documentacao_e_Git.md` | `docs/GUIA_DOCS_E_GIT.md` | Padrões de docs, branches e commits |
| `JobPilot_04_Backlog_e_Tasks.md` | `docs/BACKLOG.md` | Tarefas por fase, dependências e aceitação |
| `JobPilot_05_STATUS_template.md` | `docs/STATUS.md` | **Estado vivo** — você o atualiza sempre |

**Regra de ouro de resiliência:** *a conversa não é memória confiável.* Tudo que importa precisa estar em arquivo versionado e enviado ao remoto. Se o contexto ou os tokens acabarem, qualquer agente (ou o próprio JP) deve conseguir retomar lendo apenas os arquivos.

---

## 2. Protocolo de INÍCIO de sessão (sempre, nesta ordem)

1. Ler `docs/STATUS.md` (onde estamos, próxima ação, bloqueios).
2. Ler `docs/ALETHE_INSTRUCOES.md` (este arquivo) se for a primeira vez na sessão.
3. Ler a **seção da fase atual** em `docs/BACKLOG.md` e o **arquivo da tarefa atual** em `docs/tasks/FASE-XX/` (se existir).
4. Rodar `git fetch --all --prune`, `git status -sb` e `git branch --show-current`; confirmar que está na branch correta da tarefa **e em dia com o remoto** (ver §4A).
5. Rodar `uv sync` (garante o ambiente igual ao `uv.lock`) e depois os testes existentes via `uv run pytest` para confirmar que o ponto de partida está verde.
6. **Declarar em 3 linhas** (no chat): fase atual, tarefa atual, o que fará nesta sessão.

Se `STATUS.md` e o estado do Git divergirem, **confie no Git**, corrija o `STATUS.md` e registre a divergência em "Observações".

---

## 3. Ciclo de trabalho por tarefa

Para cada tarefa do backlog:

1. **Preparar** — se `docs/tasks/FASE-XX/Fx-Tyy.md` não existir, criá-lo a partir do modelo do `BACKLOG.md` (objetivo, arquivos prováveis, critérios de aceitação, plano de testes, riscos).
2. **Branch** — criar a branch da tarefa a partir da branch da fase (convenção no `GUIA_DOCS_E_GIT.md`).
3. **Testes primeiro** (ou junto) — especialmente para regras determinísticas.
4. **Implementar o mínimo** que faz os testes passarem; sem abstração prematura.
5. **Verificar** — lint, tipagem, testes da tarefa e suíte completa, sempre via `uv run`.
6. **Documentar** — atualizar docs afetadas (ver tabela de gatilhos no `GUIA_DOCS_E_GIT.md`), comentários didáticos que expliquem o *porquê*.
7. **Commit(s)** — pequenos, em PT-BR, formato convencional.
8. **Push** da branch para o GitHub e conferir que o remoto recebeu (o remoto é o backup; ver §4A).
9. **Atualizar `docs/STATUS.md`** e marcar a tarefa no `BACKLOG.md`.
10. **Integrar** — abrir PR da branch da tarefa para a branch da fase (pelo MCP do GitHub), conferir o CI e mesclar quando os critérios de aceitação estiverem todos atendidos e o CI estiver verde.

Nada de "quase pronto": ou a tarefa fecha com critérios atendidos, ou o estado parcial é registrado no `STATUS.md` (ver §6).

---

## 4. Regras de tamanho e foco (proteção contra falta de tokens)

- **Uma tarefa por vez.** Não começar outra com a anterior aberta.
- **Tamanho máximo de tarefa:** ~8 arquivos tocados ou ~400 linhas de diff. Passou disso → **dividir** em subtarefas (`Fx-Tyy-a`, `Fx-Tyy-b`) e registrar no backlog.
- **Commit a cada ciclo verde** (testes passando) e pelo menos a cada ~30–45 minutos de trabalho. Nunca acumular trabalho grande sem commit.
- **Push após todo commit significativo** para o GitHub e sempre antes de encerrar a sessão (ver §4A).
- **Não ler o repositório inteiro.** Ler só o necessário para a tarefa; usar o `design.md` e o `STATUS.md` como mapa.
- **Não implementar fases futuras** nem "já deixar pronto" funcionalidades fora da tarefa atual.
- **Não reescrever arquivos grandes por completo** para pequenas mudanças — editar pontualmente.
- **Planejamento just-in-time:** detalhar tarefas só da fase que está começando.

---

## 4A. Sincronização com o GitHub (rotina obrigatória)

O repositório remoto no GitHub é o **backup e a fonte da verdade** do projeto. Trabalho que existe só na máquina local conta como trabalho em risco.

**Remoto e ferramentas**

- Remoto `origin` = repositório no GitHub da conta do JP (nome sugerido: `JoaumPdr/jobpilot-ai`; confirmar com o JP na F0-T01). Criado na **F0-T01**, **privado** no início. Tornar público é decisão do JP, depois de uma varredura de segredos.
- O VS Code do JP está ligado ao **MCP do GitHub**, conectado à conta dele. Use o MCP para operações de repositório: criar repositório, criar branches, abrir/atualizar/mesclar PRs, consultar status do CI, listar PRs e branches, e (opcional) milestones e issues.
- Use o **git local** para commits, troca de branch, merge local e push. Se o MCP estiver indisponível ou sem permissão, siga com o git local, registre no `STATUS.md` e avise o JP. **Nunca** coloque token ou senha em arquivo, em URL do remoto ou em commit.

**Rotina**

| Momento | O que fazer |
|---------|-------------|
| Início de sessão | `git fetch --all --prune` e conferir `git status -sb`. Remoto à frente → `git pull --ff-only` antes de começar. Histórico divergente → **parar**, registrar no `STATUS.md` e avisar o JP (nada de force push) |
| Criar branch de tarefa | Fazer o **primeiro push logo após o primeiro commit**, já com upstream configurado |
| Durante a tarefa | **Push após cada commit significativo** (ciclo verde) |
| Tarefa concluída | Abrir PR **tarefa → fase** pelo MCP, conferir o CI no GitHub e só mesclar com CI verde |
| Fase concluída | PR **fase → `develop`**; tag `fase-NN` criada **e publicada no remoto**; em marcos de release, PR `develop` → `main` + tag `vX.Y.Z` publicada |
| Fim de sessão | Árvore limpa, **zero commits "à frente" do remoto** (`git status -sb` sem `ahead`), branch visível no GitHub; registrar o estado de sincronização no `STATUS.md` |

**Proibido sem autorização explícita do JP**

- `git push --force` em branches compartilhadas (`main`, `develop`, `phase/*`). Em branch de tarefa própria, só `--force-with-lease`, se realmente necessário e registrado no `STATUS.md`.
- Reescrever histórico já publicado.
- Apagar repositório, branches remotas ou tags; mudar visibilidade do repositório; alterar proteções de branch.

**Vazou um segredo?** Pare tudo, avise o JP imediatamente para **revogar a chave** (reescrever o histórico não basta, porque a chave já foi exposta) e só depois corrija o repositório com a orientação dele.

---

## 5. Regras de qualidade (resumo; detalhe no `PLANO.md`)

**Ambiente e dependências — `uv` desde sempre (ADR 0008):**

- O **único** gerenciador de ambiente e dependências é o **`uv`**. Ele usa a pasta `.venv` do projeto automaticamente.
- Instalar/sincronizar o ambiente: `uv sync`. Adicionar dependência: `uv add <pacote>` (de desenvolvimento: `uv add --dev <pacote>`). Remover: `uv remove <pacote>`.
- Executar qualquer comando do projeto **via `uv run`** (ex.: `uv run pytest`, `uv run ruff check`, `uv run alembic upgrade head`, `uv run uvicorn ...`), nunca ativando ambiente à mão nem usando o Python do sistema.
- **Proibido:** `pip install` direto, `requirements.txt` paralelo, instalar pacotes globais para o projeto, e editar o `uv.lock` manualmente.
- **`uv.lock` é versionado** e deve ser commitado junto com toda mudança de dependência (no mesmo commit do `pyproject.toml`). `.venv` nunca é versionado.
- Dependências de produção e de desenvolvimento ficam em grupos separados; não colocar pytest, Ruff ou pre-commit como dependência de produção.
- Mudou dependência? Atualizar também a seção de instalação do README, se necessário.
- Em caso de dúvida sobre versão do Python, a fonte da verdade é o arquivo `.python-version`.

**Código e arquitetura:**

- Camadas: **rota → serviço → repositório → modelo**. Rotas finas; serviços sem FastAPI; nós do LangGraph chamam serviços.
- Tipagem em todo código novo; Ruff limpo; sem `print` (usar logging estruturado).
- Nunca versionar segredos. `.env` fora do Git; manter `.env.example` atualizado a cada nova variável.
- **Nunca logar** texto de currículo ou dados pessoais.
- Migrações Alembic reversíveis; uma migração por mudança coesa; testar upgrade e downgrade.
- Importações idempotentes; datas em UTC.
- Testes de regras determinísticas **sem rede e sem LLM**; LLM sempre mockado no CI.
- Comentários e docstrings **didáticos, para um dev júnior**, explicando *por que* (não só *o quê*).
- Decisão arquitetural relevante → novo ADR em `docs/adr/` (modelo no guia).

---

## 6. Protocolo de FIM de sessão (ou quando sentir que o contexto está acabando)

Se você perceber que o contexto/tokens estão no fim — **pare de começar coisas novas** e faça, nesta ordem:

1. Fazer os testes passarem **ou** isolar o que está quebrado (marcar `xfail` com motivo, ou reverter o trecho incompleto). **Nunca** deixar a branch com testes vermelhos sem registro.
2. Commitar tudo (se incompleto, usar `chore(wip): <o que está feito / o que falta>`).
3. Push da branch para o GitHub e **confirmar** que não há commits à frente do remoto (`git status -sb`).
4. Atualizar `docs/STATUS.md` preenchendo obrigatoriamente: **tarefa atual, o que foi feito, o que falta (lista concreta), próximo comando/arquivo a abrir, decisões tomadas, bloqueios**.
5. Informar o JP, em poucas linhas, o ponto exato de retomada.

O objetivo: o próximo agente retoma em **menos de 2 minutos** só lendo o `STATUS.md`.

---

## 7. Estratégia de papéis (orquestração opcional)

Se usar subagentes, divida por responsabilidade, **nunca por arquivo compartilhado**:

| Papel | Responsabilidade |
|-------|------------------|
| Orquestrador | Lê STATUS/BACKLOG, escolhe a próxima tarefa, delega, atualiza STATUS, faz integração |
| Dados/Backend | Modelos, migrações, repositórios, serviços, rotas |
| Testes | Escreve/valida testes, mede cobertura, mantém golden set |
| Documentação | Atualiza README, RELATORIO, design, ADRs, docs de API/dados |
| Segurança/Revisão | Revisa diff antes do merge: segredos, logs, validação, privacidade, regras invioláveis |
| Frontend | Só entra na Fase 6 (Streamlit) |

**Regras de paralelismo:** dois agentes nunca editam a mesma branch ao mesmo tempo; só paralelizar tarefas sem dependência entre si (ver coluna "Depende de" no backlog), cada uma na sua branch. Só o Orquestrador edita o `STATUS.md`.

---

## 8. Quando parar e perguntar ao JP

Pare e pergunte (com opções e uma recomendação) quando:

- Uma decisão alterar escopo, arquitetura ou custo (novo serviço pago, novo framework, troca de banco).
- Um critério de aceitação for ambíguo ou conflitar com os princípios (§0).
- Houver necessidade de chave de API, conta externa ou dado pessoal real.
- Surgir qualquer ação que **envie dados a terceiros** ou **automatize candidatura**.
- Precisar de force push, apagar branch/tag/repositório, mudar visibilidade do repositório ou alterar proteções de branch (ver §4A).
- O MCP do GitHub falhar por falta de permissão ou autenticação.
- Uma fonte de vagas exigir contornar login/CAPTCHA/proteção (**resposta padrão: não fazer**).

Em dúvida menor, escolha a opção mais simples, registre em `docs/adr/` ou em "Decisões" no `STATUS.md` e siga.

---

## 9. Definição de PRONTO

**Tarefa pronta** quando: critérios de aceitação atendidos · testes novos e antigos verdes · lint/tipagem limpos · `uv.lock` sincronizado com o `pyproject.toml` (se houve mudança de dependência) · docs afetadas atualizadas · commits em PT-BR · push feito e verificado no GitHub (CI verde no remoto) · `STATUS.md` e `BACKLOG.md` atualizados.

**Fase pronta** quando: todas as tarefas prontas · **gate de saída** da fase (tabela no `PLANO.md` §11) verde · CI verde · `RELATORIO.md` com seção da fase · PR da fase mesclado em `develop` no GitHub · tag da fase criada **e publicada no remoto**.

---

## 10. Ordem de execução inicial

1. **Fase 0 → F0-T01** (repositório **remoto no GitHub**, estrutura de docs, branches `main` e `develop`, primeiro push).
2. Copiar o pacote de documentos (§1) para `docs/` já no primeiro commit.
3. Seguir o backlog em ordem; respeitar dependências.
4. **Só iniciar a Fase N+1 após o gate da Fase N.**

---

## 11. Prompt de kickoff (cole na Alethe para começar)

```text
Você vai desenvolver o projeto JobPilot AI seguindo estritamente os documentos do pacote
(docs/PLANO.md, docs/ALETHE_INSTRUCOES.md, docs/GUIA_DOCS_E_GIT.md, docs/BACKLOG.md, docs/STATUS.md).

Comece assim:
1. Leia docs/ALETHE_INSTRUCOES.md por inteiro.
2. Execute o protocolo de INÍCIO de sessão (seção 2).
3. Inicie a Fase 0, tarefa F0-T01.
4. Trabalhe uma tarefa por vez, com commits pequenos em PT-BR e push frequente.
5. Ao terminar cada tarefa, atualize docs/STATUS.md e docs/BACKLOG.md.
6. Se sentir que o contexto está acabando, execute o protocolo de FIM de sessão (seção 6).
7. Pare e me consulte nos casos da seção 8.

Sincronize tudo com o repositório remoto no GitHub (MCP do GitHub conectado ao VS Code; git local como alternativa):
fetch no início, push após cada commit significativo e verificação de sincronização no fim de toda sessão (seção 4A).
Use SEMPRE o uv para ambiente e dependências (uv sync, uv add, uv run); nunca pip install direto.
Não implemente fases futuras. Não automatize candidaturas. Não invente fatos no currículo.
```

## 12. Prompt de retomada (use em qualquer sessão nova)

```text
Retome o projeto JobPilot AI. Leia docs/STATUS.md e docs/ALETHE_INSTRUCOES.md,
execute o protocolo de INÍCIO de sessão (incluindo git fetch e a comparação com o remoto no GitHub) e continue exatamente do ponto registrado,
sem refazer trabalho já commitado.
```
