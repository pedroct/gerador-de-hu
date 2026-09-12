---
name: generating-azure-boards-backlog-from-spec
description: Use when a product or software specification must be decomposed into an Azure Boards Epic, Feature, and User Story hierarchy or rendered as a reviewable backlog Markdown document.
---

# Generating Azure Boards Backlog From Spec

## Outcome
Transforme somente requisitos rastreáveis em Épicos, Features e Histórias. Funciona com uma spec sem implementação disponível (Greenfield) ou com uma spec acompanhada de projeto existente (Brownfield). A numeração é documental; não é ID do Azure Boards.

## Detecção do modo

Determine e registre o modo antes de decompor ou refinar:

- **Greenfield:** há spec disponível e nenhum código-fonte relevante no escopo acessível. Registre a ausência e não exija uma inspeção inexistente.
- **Brownfield:** há spec e código-fonte ou projeto relevante disponível. Antes de decompor ou refinar, leia e aplique [references/brownfield-validation.md](references/brownfield-validation.md), inspecione a implementação em modo somente leitura e compare-a apenas com os requisitos da spec.
- Se a presença de código relevante for ambígua, escolha Brownfield conservadoramente, registre a incerteza e os limites da busca e não invente evidência.

## Workflow
1. Leia a spec inteira e crie um inventário de objetivos, atores, capacidades, regras, restrições, exemplos, conflitos e lacunas com suas origens.
2. Detecte o modo. Em Brownfield, conclua a inspeção segura e a matriz `requisito | evidência caminho:linha | status | impacto | confiança` antes da decomposição. Em Greenfield, prossiga somente com a spec e registre que código relevante está ausente.
3. Agrupe objetivos amplos em Épicos; capacidades significativas em Features; resultados coesos para um ator em Histórias. Não crie itens para preencher níveis.
4. Em Brownfield, gere trabalho acionável para lacunas, divergências e mudanças exigidas pela spec. Requisitos classificados como `Implementado` permanecem na cobertura e não geram itens duplicados por padrão. Se o usuário pedir documentação de comportamento existente, o item pode ser mantido como `Implementado`, explicitando que não representa trabalho novo.
5. Sugestões, propostas ou hipóteses não confirmadas nunca originam Épico, Feature, História ou regra; registre-as somente em `Itens não cobertos` ou na Conversation de uma demanda confirmada, preservando origem e estado. Código existente também não cria requisito nem confirma decisão de negócio.
6. Para cada história, **REQUIRED SUB-SKILL:** use refining-user-stories-with-3c. Em Brownfield, forneça a evidência de implementação somente como contexto rotulado do estado atual. Consuma o resultado da 3C sem recalcular 3W, Conversation, Confirmation ou prontidão.
7. Numere `E.0.0`, `E.F.0`, `E.F.S`; preserve chaves existentes em atualizações. Declare cada relação no bloco `Parent`; posição e numeração não substituem o pai explícito.
8. Renderize modo, raiz ou ausência de código, `Validation Summary`, evidência por item e política de cobertura conforme [references/backlog-markdown-contract.md](references/backlog-markdown-contract.md).
9. Execute `uv run python scripts/validate_backlog.py CAMINHO`; com backlog existente, acrescente `--update`. Corrija violações estruturais e revise semanticamente rastreabilidade, agrupamento, cobertura Brownfield e ausência de regras fabricadas.
10. Entregue o backlog mesmo com Histórias `Não pronta`. Para cada uma, liste as lacunas de Card, Conversation e Confirmation que a bloqueiam e sugira ao usuário registrá-las em `## Lacunas e perguntas abertas` da spec de origem e rodar `interviewing-request-gaps` (quando instalada); depois de cada rodada de respostas, regenere o backlog e repita a sugestão até todas as Histórias ficarem `Prontas` ou até o usuário adiar explicitamente uma lacuna.

## Boundaries
- Gere Markdown; não crie work items.
- Não invente Area Path, Iteration Path, Story Points, prioridade, responsável ou datas.
- História rastreável mas incompleta permanece `Não pronta`; com Confirmation `Ausente` ou `Parcial`, Acceptance Criteria fica efetivamente vazio.
- Requisito sem pai justificável entra em `Itens não cobertos`.
- Evidência de implementação pertence a `Implementation Evidence`, `Validation Summary` e, quando útil, a uma síntese rotulada em Description/Conversation; nunca a `Acceptance Criteria`.
- Inspeção Brownfield não autoriza executar scripts, testes, builds, servidores, migrações ou a aplicação do projeto.
- A sugestão de `interviewing-request-gaps` para Histórias `Não pronta` é indicação ao usuário, nunca uma chamada direta a essa skill; não atrase nem condicione a entrega do backlog atual a essa rodada.
