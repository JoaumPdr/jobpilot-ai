# ADR 0001 — Monólito modular em Python
- Data: 2026-11-14
- Status: aceito

## Contexto
O projeto JobPilot AI precisa de uma arquitetura inicial simples, fácil de entender e manter, que permita evolução incremental. O escopo do MVP (Fases 0–4) não justifica complexidade de microsserviços.

## Decisão
Adotar um **monólito modular** em Python, com separação clara de camadas (API → Serviços → Repositórios → Modelos) e módulos organizados por domínio (perfil, vagas, matching, LLM, orquestração, etc.).

## Alternativas consideradas
- **Microsserviços:** Maior complexidade operacional, necessidade de service discovery, balanceamento de carga, deploy independente. Não justificado para o MVP.
- **Monólito sem modularidade:** Risco de acoplamento e dificuldade de manutenção à medida que o projeto cresce.

## Consequências
- Melhorias: Simplicidade de deploy, desenvolvimento mais rápido, comunicação entre módulos via chamadas de função locais.
- Piores: Não há isolamento de falhas por serviço; todo o aplicativo é implantado como uma unidade.
- Revisitar: Se o projeto crescer além do MVP, avaliar extração de módulos para serviços independentes.
