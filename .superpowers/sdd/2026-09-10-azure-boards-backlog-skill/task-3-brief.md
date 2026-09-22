### Task 3: Criar a quarta skill e seu contrato Markdown

**Files:**
- Modify: `generating-azure-boards-backlog-from-spec/SKILL.md`
- Modify: `generating-azure-boards-backlog-from-spec/agents/openai.yaml`
- Create: `generating-azure-boards-backlog-from-spec/references/backlog-markdown-contract.md`

**Interfaces:**
- Consumes: conteúdo de uma spec e, opcionalmente, backlog Markdown existente.
- Consumes: resultado completo de `refining-user-stories-with-3c` por história.
- Produces: um arquivo Markdown conforme `references/backlog-markdown-contract.md`.

- [ ] **Step 1: Escrever `SKILL.md` mínimo orientado pelas falhas RED**

O corpo deve conter estas decisões concretas:

```markdown
---
name: generating-azure-boards-backlog-from-spec
description: Use when a product or software specification must be decomposed into an Azure Boards Epic, Feature, and User Story hierarchy or rendered as a reviewable backlog Markdown document.
---

# Generating Azure Boards Backlog From Spec

## Outcome
Transforme somente requisitos rastreáveis em Épicos, Features e Histórias. A numeração é documental; não é ID do Azure Boards.

## Workflow
1. Leia a spec inteira e crie um inventário de objetivos, atores, capacidades, regras, restrições, exemplos, conflitos e lacunas com suas origens.
2. Agrupe objetivos amplos em Épicos; capacidades significativas em Features; resultados coesos para um ator em Histórias. Não crie itens para preencher níveis.
3. Para cada história, **REQUIRED SUB-SKILL:** use refining-user-stories-with-3c. Consuma seu resultado sem recalcular 3W, Conversation, Confirmation ou prontidão.
4. Numere `E.0.0`, `E.F.0`, `E.F.S`; preserve chaves existentes em atualizações.
5. Renderize conforme [references/backlog-markdown-contract.md](references/backlog-markdown-contract.md).
6. Execute `uv run python scripts/validate_backlog.py CAMINHO`; com backlog existente, acrescente `--update`. Corrija violações estruturais e revise semanticamente rastreabilidade, agrupamento e ausência de regras fabricadas.

## Boundaries
- Gere Markdown; não crie work items.
- Não invente Area Path, Iteration Path, Story Points, prioridade, responsável ou datas.
- História rastreável mas incompleta permanece `Não pronta` e sem conteúdo em Acceptance Criteria.
- Requisito sem pai justificável entra em `Itens não cobertos`.
```

- [ ] **Step 2: Escrever o contrato de referência**

Criar `references/backlog-markdown-contract.md` copiando do design:

```text
- definição de Epic, Feature e User Story;
- tabela de numeração e regras de atualização;
- template Markdown completo;
- conteúdo permitido em Description e Acceptance Criteria;
- Refinement Status fora dos campos Azure;
- rastreabilidade e Itens não cobertos;
- diferença entre Markdown de revisão e campos HTML do Azure Boards.
```

Incluir links oficiais:

```text
https://learn.microsoft.com/en-us/azure/devops/boards/backlogs/define-features-epics
https://learn.microsoft.com/en-us/azure/devops/boards/work-items/guidance/agile-process-workflow
https://learn.microsoft.com/en-us/azure/devops/boards/queries/titles-ids-descriptions
```

- [ ] **Step 3: Conferir metadados da interface**

`agents/openai.yaml` deve ser exatamente compatível com:

```yaml
interface:
  display_name: "Gerar backlog para Azure Boards"
  short_description: "Converte specs em backlog hierárquico revisável"
  default_prompt: "Use $generating-azure-boards-backlog-from-spec para analisar esta spec e gerar um backlog Markdown para Azure Boards."
```

- [ ] **Step 4: Validar a skill**

Run:

```bash
uv run --with pyyaml python /Users/pedroct/.codex/skills/.system/skill-creator/scripts/quick_validate.py /Users/pedroct/skills/generating-azure-boards-backlog-from-spec
```

Expected: `Skill is valid!`.

---

