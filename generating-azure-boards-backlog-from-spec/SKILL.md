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
3. Sugestões, propostas ou hipóteses não confirmadas nunca originam Épico, Feature, História ou regra; registre-as somente em `Itens não cobertos` ou na Conversation de uma demanda confirmada, preservando origem e estado.
4. Para cada história, **REQUIRED SUB-SKILL:** use refining-user-stories-with-3c. Consuma seu resultado sem recalcular 3W, Conversation, Confirmation ou prontidão.
5. Numere `E.0.0`, `E.F.0`, `E.F.S`; preserve chaves existentes em atualizações. Declare cada relação no bloco `Parent`; posição e numeração não substituem o pai explícito.
6. Renderize conforme [references/backlog-markdown-contract.md](references/backlog-markdown-contract.md).
7. Execute `uv run python scripts/validate_backlog.py CAMINHO`; com backlog existente, acrescente `--update`. Corrija violações estruturais e revise semanticamente rastreabilidade, agrupamento e ausência de regras fabricadas.

## Boundaries
- Gere Markdown; não crie work items.
- Não invente Area Path, Iteration Path, Story Points, prioridade, responsável ou datas.
- História rastreável mas incompleta permanece `Não pronta`; com Confirmation `Ausente` ou `Parcial`, Acceptance Criteria fica efetivamente vazio.
- Requisito sem pai justificável entra em `Itens não cobertos`.
