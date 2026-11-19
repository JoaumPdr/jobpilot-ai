# ADR 0011 — Distribuição local da v1.0.0 com Docker Compose
- Data: 2026-11-19
- Status: aceito

## Contexto
O fluxo de desenvolvimento usa `uv` no host e já conta com um Docker Compose para PostgreSQL 16, com volume nomeado e verificação de saúde. A primeira distribuição precisa funcionar em uma máquina diferente da usada no desenvolvimento, preservar os dados do usuário e oferecer recuperação verificável.

## Decisão
Adotar Docker Compose para a primeira distribuição local e reproduzível da `v1.0.0`, com API FastAPI, interface Streamlit no navegador e PostgreSQL persistente, sem exigir Python, `uv` ou PostgreSQL instalados no host. A entrega inclui configuração inicial segura por `.env`, procedimentos documentados de backup e restauração e validação por uma terceira pessoa em ambiente limpo.

## Alternativas consideradas
- **Distribuir pelo fluxo de desenvolvimento com `uv`.** Reaproveita a instalação atual, mas exige preparar o ambiente Python e iniciar os componentes manualmente.
- **Empacotar para Docker Compose.** Reaproveita o serviço PostgreSQL existente e coordena a inicialização dos componentes. Exige Docker com Compose no host.
- **Distribuir por instalador gráfico ou executável independente.** Pode reduzir o uso do terminal, mas exige solução própria para preparar, atualizar e manter os serviços e os dados.

## Consequências
- API, interface e banco poderão subir de forma coordenada, preservando a arquitetura do monólito modular. A configuração de distribuição reaproveitará o PostgreSQL, seu volume e a verificação de saúde conforme aplicável.
- No Windows, o usuário poderá precisar do Docker Desktop. A primeira instalação envolve comandos de terminal e a edição do `.env`. A documentação indicará como proteger a configuração local e as cópias de dados.
- O gate da Fase 7 exigirá evidência de instalação por terceiro, persistência após reinício e recriação dos containers com o volume preservado e recuperação de dados a partir de um backup documentado.
- Uma experiência de instalação simplificada poderá ser avaliada para a `v1.1.0`: instalador gráfico para Windows, executável independente, assistente visual de configuração, atalho que gerencia serviços, atualizador automático, backup pela interface e diagnóstico visual avançado.
