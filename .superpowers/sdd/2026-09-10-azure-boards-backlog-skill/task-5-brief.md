### Task 5: Verificar o comportamento da quarta skill

**Files:**
- Read: `generating-azure-boards-backlog-from-spec/SKILL.md`
- Read: `generating-azure-boards-backlog-from-spec/references/backlog-markdown-contract.md`
- Test: `generating-azure-boards-backlog-from-spec/scripts/validate_backlog.py`
- Create: nenhum artefato persistente; agentes retornam resultados em mensagens finais

**Interfaces:**
- Consumes: cenário da Task 1 e uma variação totalmente confirmada.
- Produces: evidência comportamental GREEN e REFACTOR.

- [ ] **Step 1: Reexecutar o cenário original com a quarta skill**

Usar um agente em contexto fresco com acesso explícito à quarta skill e à spec do cenário RED.

Expected:

```text
- pelo menos dois Épicos quando os objetivos não puderem compartilhar justificadamente o mesmo pai;
- cada Feature e história com Parent explícito;
- origem na spec em cada história;
- endpoint somente em propostas da Conversation;
- história de reabertura com Confirmation baseada nas regras confirmadas;
- história gerencial Não pronta e sem conteúdo em Acceptance Criteria;
- Estado 3C preservado, sem recálculo pela quarta skill.
```

- [ ] **Step 2: Testar uma spec totalmente confirmada**

Fornecer uma spec com um objetivo, duas capacidades e duas histórias confirmadas por Feature. Verificar numeração `1.0.0`, `1.1.0`, `1.1.1`, `1.1.2`, `1.2.0`, `1.2.1`, `1.2.2`, além de Gherkin somente nas histórias.

- [ ] **Step 3: Testar atualização de backlog existente**

Fornecer um backlog com chaves `1.1.1` e `1.1.3`, informar que `1.1.2` foi removida e pedir uma nova história. Expected: preservar as chaves e atribuir `1.1.4`; nunca reutilizar `1.1.2`.

- [ ] **Step 4: Revisar manualmente os três resultados**

Confirmar:

```text
- nenhum requisito sem origem;
- nenhuma regra inventada;
- nenhum conteúdo de Conversation em Acceptance Criteria;
- nenhum Gherkin em Épico ou Feature;
- nenhuma chave chamada de Azure ID;
- nenhuma mutação externa sugerida como já executada.
```

Se surgir uma falha nova, alterar somente a instrução que fecha a brecha e repetir o mesmo cenário em contexto fresco.

---

