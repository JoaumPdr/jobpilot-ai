# ADR 0005 — LLM atrás de interface `LLMProvider`
- Data: 2026-11-14
- Status: aceito

## Contexto
A Fase 3 (Camada LLM) exige integração com modelos de linguagem para análise de vagas. É necessário abstrair o provedor para permitir troca, teste com mock e controle de custo.

## Decisão
Adotar uma **interface `LLMProvider`** com:
- Implementação falsa (mock) para todos os testes.
- Provedor real configurável via `.env` (`LLM_PROVIDER`, `LLM_MODEL`, `LLM_API_KEY`).
- Configurações de timeout, retry, max tokens e orçamento.
- Cache de respostas (`llm_cache`) para evitar chamadas duplicadas.

## Alternativas consideradas
- **Chamar LLM diretamente nos serviços:** Acopla a lógica de negócio a um provedor específico, dificulta testes e troca de modelo.
- **Usar LangChain/LlamaIndex como abstração:** Adiciona dependência pesada; a interface própria é suficiente para o escopo atual.

## Consequências
- Melhorias: Testes determinísticos sem chamar LLM real, troca de provedor apenas por `.env`, controle de custo e cache.
- Piores: Requer manutenção da interface própria à medida que novos provedores são adicionados.
