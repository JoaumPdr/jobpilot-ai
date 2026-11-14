# ADR 0009 — GitHub como remoto e fonte da verdade
- Data: 2026-11-14
- Status: aceito

## Contexto
O projeto precisa de um repositório remoto para backup, colaboração e CI. É necessário definir a estratégia de sincronização com o GitHub.

## Decisão
O repositório remoto no GitHub (`JoaumPdr/jobpilot-ai`, privado) é o **backup e a fonte da verdade** do projeto. Operado pelo MCP do GitHub no VS Code (repositório, branches, PRs, CI) e pelo git local (commits e push). Push após cada commit significativo; nenhum trabalho confirmado fica só local; sem force push em branches compartilhadas; tags publicadas no remoto.

## Alternativas consideradas
- **Git local apenas:** Sem backup, sem CI, sem possibilidade de colaboração.
- **GitLab/Bitbucket:** Funcionariam, mas o JP já tem conta e MCP configurado no GitHub.

## Consequências
- Melhorias: Backup contínuo, CI automático, PRs para revisão, tags para retorno rápido a versões boas.
- Piores: Dependência de conta GitHub; credenciais nunca entram em arquivos, URLs do remoto ou commits.
- Proteções: Branches `main` e `develop` devem ter proteção (PR obrigatório, CI verde) — se não disponível no plano, seguir por disciplina e registrar no STATUS.md.
