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
3. Ler a entrada pertinente em `docs/BACKLOG.md` e, quando existir, a ficha em `docs/tasks/FASE-XX/Fx-Tyy.md`. Sem ficha, os critérios do backlog bastam para começar.
4. Rodar `git fetch --all --prune`, `git status -sb` e `git branch --show-current`; confirmar que está na branch correta da tarefa **e em dia com o remoto** (ver §4A).
5. Rodar `uv sync` (garante o ambiente igual ao `uv.lock`) e depois os testes existentes via `uv run pytest` para confirmar que o ponto de partida está verde.
6. Confirmar que a sessão herdou a política e os playbooks do JobPilot AI (§7A). Avaliar modelo e esforço do líder para a tarefa (§7C).
7. Declarar fase, tarefa, próxima ação, estratégia e adequação do modelo do líder. Quando houver motivo para trocar, aguardar confirmação antes de implementar (§7C).

Se `STATUS.md` e o estado do Git divergirem, **confie no Git**, corrija o `STATUS.md` e registre a divergência em "Observações".

---

## 3. Ciclo de trabalho por tarefa

Para cada tarefa do backlog:

1. **Preparar** — reavaliar o modelo e esforço do líder a cada transição de tarefa (§7C). Decidir se a tarefa precisa de ficha conforme §3A. Se precisar e ela ainda não existir, criá-la a partir do modelo do `BACKLOG.md`. Caso contrário, o planejamento fica no backlog.
2. **Branch** — criar a branch da tarefa a partir da branch da fase (convenção no `GUIA_DOCS_E_GIT.md`).
3. **Testes primeiro** (ou junto) — especialmente para regras determinísticas.
4. **Implementar o mínimo** que faz os testes passarem; sem abstração prematura.
5. **Verificar** — lint, tipagem, testes da tarefa e suíte completa, sempre via `uv run`.
6. **Documentar** — atualizar docs afetadas (ver tabela de gatilhos no `GUIA_DOCS_E_GIT.md`), comentários didáticos que expliquem o *porquê*.
7. **Commit(s)** — pequenos, em PT-BR, formato convencional.
8. **Push** da branch para o GitHub e conferir que o remoto recebeu (o remoto é o backup; ver §4A).
9. **Atualizar `docs/STATUS.md`**, marcar a tarefa no `BACKLOG.md` e atualizar a ficha da tarefa (se existir).
10. **Integrar** — abrir PR da branch da tarefa para a branch da fase pelo MCP do GitHub autenticado ou por `gh`, conferir o CI e mesclar quando os critérios de aceitação estiverem todos atendidos e o CI estiver verde.

Nada de "quase pronto": ou a tarefa fecha com critérios atendidos, ou o estado parcial é registrado no `STATUS.md` (ver §6).

### 3A. Política de fichas de tarefa (`docs/tasks/FASE-XX/Fx-Tyy.md`)

A ficha é o **planejamento detalhado da execução** de uma tarefa. Ela é **opcional e just-in-time** — não é etapa burocrática obrigatória para toda tarefa. A regra de ouro:

- **BACKLOG** decide **o que** fazer e **quando** a tarefa está pronta (critérios canônicos).
- **Ficha** explica **como** executar e verificar.
- **STATUS** registra **onde estamos** e como retomar.

Regras de criação:

1. **Sem fichas retroativas.** Tarefas já concluídas (Fase 0) não recebem ficha; o histórico delas vive no `BACKLOG.md`, no `RELATORIO.md` e nos commits.
2. Criar a ficha **quando a tarefa estiver prestes a começar**, nunca antecipadamente para todas as tarefas futuras da fase.
3. **Criar ficha quando** a tarefa envolver múltiplas etapas técnicas, decisão arquitetural, vários arquivos, risco relevante ou plano de testes não trivial.
4. **Tarefa pequena e direta** → o planejamento permanece no próprio `BACKLOG.md`, desde que os critérios de aceitação sejam suficientes para orientar a execução.
5. Se uma tarefa inicialmente simples **revelar complexidade** durante a preparação, criar a ficha **antes** de iniciar a implementação.
6. Ficha existente é **complemento**, não substituta: os critérios de aceitação canônicos continuam no BACKLOG; a ficha referencia e detalha como verificá-los, sem alterar escopo por conta própria.

---

## 4. Regras de tamanho e foco (proteção contra falta de tokens)

- **Uma tarefa por vez.** Não começar outra com a anterior aberta.
- **Tamanho máximo de tarefa:** ~8 arquivos tocados ou ~400 linhas de diff. Passou disso → **avaliar** a divisão em subtarefas (`Fx-Tyy-a`, `Fx-Tyy-b`) e registrar no backlog. O limite é um alerta, não uma regra cega: se dividir quebrar uma unidade coesa (ex.: um esquema e a migração que o cria), manter a tarefa inteira e justificar na ficha ou no `STATUS.md`.
- **Commit a cada ciclo verde** (testes passando) e pelo menos a cada ~30–45 minutos de trabalho. Nunca acumular trabalho grande sem commit.
- **Push após todo commit significativo** para o GitHub e sempre antes de encerrar a sessão (ver §4A).
- **Não ler o repositório inteiro.** Ler só o necessário para a tarefa; usar o `design.md` e o `STATUS.md` como mapa.
- **Não implementar fases futuras** nem "já deixar pronto" funcionalidades fora da tarefa atual.
- **Não reescrever arquivos grandes por completo** para pequenas mudanças — editar pontualmente.
- **Planejamento just-in-time:** detalhar a tarefa só quando ela for começar (ficha quando aplicável, §3A); não detalhar a fase inteira antecipadamente.

---

## 4A. Sincronização com o GitHub (rotina obrigatória)

O repositório remoto no GitHub é o **backup e a fonte da verdade** do projeto. Trabalho que existe só na máquina local conta como trabalho em risco.

**Remoto e ferramentas**

- Remoto `origin` = repositório no GitHub da conta do JP (nome sugerido: `JoaumPdr/jobpilot-ai`; confirmar com o JP na F0-T01). Criado na **F0-T01**, **privado** no início. Tornar público é decisão do JP, depois de uma varredura de segredos.
- Use o **MCP do GitHub** quando estiver disponível e autenticado. Use **`gh` autenticado** para PRs e CI quando o MCP estiver indisponível e registre a alternativa no `STATUS.md`. Em caso de falha de permissão ou autenticação, avise o JP e siga a §8.
- Use o **git local** para commits, troca de branch, merge local e push. Mantenha tokens e senhas nos mecanismos de autenticação das ferramentas.

**Rotina**

| Momento | O que fazer |
|---------|-------------|
| Início de sessão | `git fetch --all --prune` e conferir `git status -sb`. Remoto à frente → `git pull --ff-only` antes de começar. Histórico divergente → **parar**, registrar no `STATUS.md` e avisar o JP (nada de force push) |
| Criar branch de tarefa | Fazer o **primeiro push logo após o primeiro commit**, já com upstream configurado |
| Durante a tarefa | **Push após cada commit significativo** (ciclo verde) |
| Tarefa concluída | Abrir PR **tarefa → fase** pelo MCP ou por `gh`, conferir o CI no GitHub e só mesclar com CI verde |
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

## 7. Orquestração do desenvolvimento

O **Codex CLI** lidera o desenvolvimento com login pela assinatura do ChatGPT. A **Alethe** coordena a delegação quando houver ganho de qualidade ou de tempo. O líder resolve diretamente tarefas pequenas e claras e responde pela seleção dos workers, pelos briefs, pela revisão e pela integração.

Se usar subagentes, divida por responsabilidade, **nunca por arquivo compartilhado**:

| Papel | Responsabilidade |
|-------|------------------|
| Líder | Lê STATUS/BACKLOG, prepara a tarefa, delega, revisa os resultados, integra mudanças e atualiza o STATUS |
| Dados/Backend | Modelos, migrações, repositórios, serviços, rotas |
| Testes | Escreve/valida testes, mede cobertura, mantém golden set |
| Documentação | Atualiza README, RELATORIO, design, ADRs, docs de API/dados |
| Segurança/Revisão | Revisa diff antes do merge: segredos, logs, validação, privacidade, regras invioláveis |
| Frontend | Só entra na Fase 6 (Streamlit) |

### 7A. Ativação da política do projeto

No Windows, inicie o Codex CLI pelo launcher a partir da raiz do checkout.

```powershell
.\scripts\JobPilot-Codex.ps1
```

De outro diretório, invoque o script pelo caminho com `&`. O launcher identifica a raiz pela localização do próprio arquivo. Ele usa a CLI da Alethe versionada em `.agents/skills/alethe`. Os hooks são fornecidos pelo plugin instalado e habilitado no Codex.

O launcher, o Codex e a Alethe são ferramentas de desenvolvimento. A instalação e a execução do JobPilot AI para o usuário final seguem as instruções do README.

O launcher espera `alethe-orchestrate.json` e `alethe-playbooks.yaml` em `%LOCALAPPDATA%\Alethe\JobPilot-AI`. Ele define `ALETHE_ORCHESTRATE_POLICY`, `ALETHE_ORCHESTRATE_PLAYBOOKS` e `ALETHE_ORCHESTRATE_HOME` no ambiente do processo antes de iniciar o Codex. Ao sair, restaura os valores anteriores. Quando disponível, o Python do ambiente do projeto entra no PATH dessa execução para o launcher e os hooks.

O diagnóstico apresenta os caminhos efetivos, perfil, provedor detectado, autenticação conforme a evidência disponível e modelo e esforço por tier. Rode `.\scripts\JobPilot-Codex.ps1 check` para repetir a verificação sem abrir outra sessão. Se faltar um arquivo ou houver erro de configuração, restaure a cópia local do projeto e repita o diagnóstico. Os arquivos locais e as credenciais ficam fora do Git.

Dentro do Codex, rode `.\scripts\JobPilot-Codex.ps1 check-session`. Esse modo verifica os caminhos herdados antes de configurar seu próprio processo. Se a sessão tiver chegado pelo Codex direto ou por uma interface que não herdou os caminhos, informe o problema e reabra pelo launcher antes de delegar.

### 7B. Workers, playbooks e cotas

- **Codex** é a opção inicial para workers. **Copilot** é a preferência para testes e implementação auxiliar quando o adaptador estiver validado. Use-o para revisão independente somente se houver modo de leitura verificável. **Antigravity** tem preferência para pesquisa e exploração quando a CLI nativa estiver disponível. **OpenCode** é a contingência com modelo gratuito explícito. **Claude** depende de autenticação autorizada e de confirmação de que a execução não acrescenta custo.
- Use o perfil **Base**. Declare `tier` e `provider` em cada item de `workers`. A Alethe fixa modelo e esforço pelo tier. Confira ambos no `dry-run` e preserve as escolhas ao retomar uma sessão. Na v24, os campos `model` e `effort` no plano são aceitos somente com `tier: standard`. Use-os quando a etapa do playbook exigir uma combinação diferente da padrão.
- Confira disponibilidade, tipo de autenticação e cotas antes de delegar. Use 80% como alerta e 90% como limite de bloqueio nas janelas mensuráveis. Quando a cota estiver baixa, proponha ao JP uma troca para um provedor apto no mesmo tier ou pause a delegação. Trate leitura ausente ou vencida como desconhecida e solicite autorização para delegar nessa condição. Serviços com cobrança adicional exigem autorização explícita. Fallback automático para API paga fica desabilitado.
- Mantenha uma execução ativa por vez, com até dois workers simultâneos. Peça autorização para exceder esse limite. Defina orçamento de chamadas, tempo e tokens proporcional ao plano. Registre o consumo efetivamente reportado e a utilidade dos resultados. Quando o provedor não reportar a métrica, registre a ausência.
- Se o provedor estiver indisponível, informe a causa observada. Execute diretamente quando for adequado. Se a delegação continuar necessária, proponha um provedor habilitado com capacidade equivalente e aplique as regras de custo e cota antes de usá-lo. Sem uma alternativa apta, pause a delegação.

| Tier | Uso | Modelo Codex | Esforço |
|---|---|---|---|
| Cheap | Triagem e tarefas mecânicas verificáveis | `gpt-5.6-luna` | `low` |
| Standard | Implementação e revisão de rotina | `gpt-6.2-sol` | `medium` |
| Strong | Decisões, revisão crítica e escalonamentos justificados | `gpt-6.2-astra` | `high` |

Use o launcher nas operações da Alethe deste projeto, inclusive quando a skill indicar um comando da CLI. Escolha o playbook, defina os workers e confira os tiers e os modelos no `dry-run`. Passe o plano como primeiro argumento após o subcomando. O launcher verifica tier e provedor em `validate`, `dry-run` e `run`. Uma omissão interrompe o comando antes de a CLI aplicar o padrão de `economy`. Salve o plano JSON em UTF-8 sem BOM.

```powershell
.\scripts\JobPilot-Codex.ps1 alethe playbook --pick
.\scripts\JobPilot-Codex.ps1 alethe validate $plano
.\scripts\JobPilot-Codex.ps1 alethe dry-run $plano
# Depois de conferir a prévia, as cotas e as autorizações
.\scripts\JobPilot-Codex.ps1 alethe new 'Título da execução' --playbook plan-execute
.\scripts\JobPilot-Codex.ps1 alethe run $plano --in current --detach
.\scripts\JobPilot-Codex.ps1 alethe wait --timeout 30
```

- Use `direct` para trabalho pequeno, `cascade` para mudanças mecânicas verificáveis, `scout-then-build` para módulos desconhecidos e `plan-execute` para etapas sequenciais. Use `review-gate` no diff final de mudanças relevantes, `parallel-worktrees` para unidades independentes e `advisor-escalation` quando evidências justificarem um modelo superior. Escolha `best-of-n` ou auditorias extensas somente quando o ganho justificar o consumo.
- Use o estágio e a ficha atual como mapa. Leia os trechos necessários dos documentos técnicos. Envie objetivo, caminhos autorizados, restrições e checagens a cada worker. Peça caminhos e linhas, diffs, resultados e riscos. Consulte logs brutos apenas para diagnosticar falhas. Para uma correção relacionada, prefira retomar a sessão e faça no máximo uma nova tentativa por unidade após identificar a causa corrigível.
- Pesquisadores e revisores operam em somente leitura. Escritas delegadas usam worktrees isoladas, com branches e arquivos disjuntos. O líder aplica os diffs revisados, roda os testes e linters, confere o CI quando houver PR e atualiza o `STATUS.md`.
- Proíba delegação recursiva. Use os bloqueios fornecidos pela CLI e pela Alethe e inclua a regra no brief. Só habilite adaptadores personalizados após verificar o executável, argumentos, modelo, permissões, saída e limites com `validate`, `dry-run` e um teste controlado autorizado. Adaptadores `custom` da Alethe v24 operam em modo de escrita isolada. Use um provedor nativo em modo somente leitura para pesquisa e revisão.
- Mantenha `allowUnsafe` desabilitado e entregue apenas dados sintéticos ou expurgados. Dados pessoais, currículos reais e segredos ficam fora de prompts, diffs e logs enviados a provedores.

### 7C. Modelo e esforço do líder

No início da sessão e a cada transição de tarefa, avalie fase, complexidade técnica, decisões arquiteturais, riscos de segurança, complexidade dos testes, integrações externas e consumo estimado. Use a matriz como ponto de partida. A complexidade da tarefa determina a recomendação.

| Fase | Modelo | Esforço |
|---|---|---|
| F0 | Sol | Medium |
| F1 | Sol | Medium |
| F2 | Sol | Medium ou High |
| F3 | Sol ou Astra | High |
| F4 | Astra | High |
| F5 | Sol ou Astra | Medium ou High |
| F6 | Sol | Medium |
| F7 | Sol ou Astra | High |

Confira o modelo e o esforço da sessão no seletor `/model` ou nos metadados disponíveis do turno. Trate a configuração padrão como padrão de inicialização e declare quando a combinação efetiva da sessão não for verificável. A Alethe aplica seus tiers aos workers. A configuração da sessão principal pertence ao Codex.

Se a combinação for adequada, prossiga segundo as autorizações da tarefa. Quando houver motivo para trocar, informe a combinação atual quando verificável, recomende modelo e esforço concretos, explique o motivo e peça ao JP para selecionar a combinação com `/model`. Aguarde a confirmação antes de implementar. Registre a troca como efetiva somente quando houver evidência da sessão ou confirmação explícita do JP.

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

Sincronize tudo com o repositório remoto no GitHub. Use o MCP autenticado ou gh para PRs e CI e o git local para branches, commits e push:
fetch no início, push após cada commit significativo e verificação de sincronização no fim de toda sessão (seção 4A).
Use SEMPRE o uv para ambiente e dependências (uv sync, uv add, uv run); nunca pip install direto.
Não implemente fases futuras. Não automatize candidaturas. Não invente fatos no currículo.
```

## 12. Prompt de retomada (use em qualquer sessão nova)

```text
Retome o JobPilot AI a partir do ponto registrado. Leia AGENTS.md,
docs/STATUS.md e docs/ALETHE_INSTRUCOES.md. Execute o protocolo de INÍCIO
da §2, incluindo a comparação com o GitHub, a suíte de partida e a
verificação de que esta sessão herdou a política do projeto.
Antes de editar, informe fase, tarefa, próxima ação e estratégia.
Avalie a adequação do modelo e esforço do líder conforme §7C. Quando
houver motivo para troca, recomende a combinação e aguarde minha
confirmação após o ajuste manual em /model.
Se houver delegação, use o launcher e declare o tier de cada worker
conforme §7B. Em caso de divergência relevante ou mudanças locais
inesperadas, pare e solicite orientação.
```
