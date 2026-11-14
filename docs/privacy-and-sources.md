# JobPilot AI — Privacidade e Fontes de Vagas

> Documento base da política de privacidade (LGPD) e regras para fontes externas de vagas.
> Atualizado a cada nova fonte de vagas adicionada.

---

## 1. Privacidade de dados (LGPD)

O JobPilot AI é um assistente pessoal para gerir candidaturas a vagas. Os dados tratados incluem:

- **Dados do candidato:** nome, e-mail, currículo em texto, skills, experiências, formação, idiomas, preferências de emprego.
- **Dados de vagas:** título, empresa, descrição, localização, modalidade, senioridade, URL, salário.
- **Dados de candidaturas:** status, histórico de mudanças, observações.

### Princípios aplicados

1. **Minimização de dados:** Apenas os dados necessários para o funcionamento do sistema são coletados e armazenados.
2. **Nenhum dado pessoal em logs:** Textos de currículo, nomes, e-mails e outros PII **nunca** são gravados em logs.
3. **Dados do usuário ficam local:** O banco de dados PostgreSQL roda localmente (Docker Compose). Nenhum dado é enviado a terceiros sem ação explícita do usuário.
4. **LLM recebe dados mínimos:** Quando a camada LLM é usada (Fase 3+), apenas o estritamente necessário é enviado ao provedor, e a descrição da vaga é tratada como *dado delimitado*, nunca como instrução.
5. **Direito do usuário:** O usuário pode editar, excluir ou exportar seus dados a qualquer momento (via API ou interface).

### Variáveis de ambiente

Segredos (chaves de API, senhas de banco) ficam exclusivamente no arquivo `.env`, que **não é versionado**. O `.env.example` contém apenas placeholders sem valores reais.

---

## 2. Política de fontes de vagas

O JobPilot AI obtém vagas das seguintes fontes, em ordem de preferência:

| Fonte | Método | Autorizada? | Observações |
|-------|--------|-------------|-------------|
| Entrada manual | Usuário cadastra via API | ✅ Sim | Fonte primária do MVP |
| CSV | Usuário importa arquivo | ✅ Sim | Validação linha a linha, relatório de erros |
| APIs oficiais | Coletor autorizado (Fase 7) | ⚠️ Condicional | Somente com API oficial/feed permitido, respeitando termos de uso e rate limits |
| Scraping | Extração automática de sites | ❌ Não | **Não é feito.** Nunca contornar login, CAPTCHA ou proteções. |

### Checklist para nova fonte (Fase 7-T03)

Antes de adicionar qualquer coletor de vagas externo:

- [ ] A fonte disponibiliza API oficial ou feed público permitido.
- [ ] Os termos de uso da fonte foram lidos e permitem o uso pretendido.
- [ ] O coletor respeita rate limits e limites de quota da fonte.
- [ ] O coletor pode ser desabilitado a qualquer momento.
- [ ] Nenhum dado pessoal do candidato é enviado à fonte externa.
- [ ] `docs/privacy-and-sources.md` foi atualizado com a nova fonte.
- [ ] ADR registrado para a decisão de adicionar a fonte.

---

## 3. Dados não confiáveis

Respostas de LLM e dados de fontes externas são tratados como **dados não confiáveis**:

- Saídas de LLM são validadas por Pydantic antes de serem persistidas.
- Itens sem evidência vão para `unknown_requirements`, nunca são inventados.
- Currículo do usuário nunca é inventado ou alterado automaticamente sem aprovação explícita (Fase 5).
