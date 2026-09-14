---
name: generating-azure-boards-backlog-from-spec
description: Use when a product or software specification must be decomposed into an Azure Boards Epic, Feature, and User Story/Bug hierarchy or rendered as a reviewable backlog Markdown document.
---

# Generating Azure Boards Backlog From Spec

## Outcome
Transforme somente requisitos rastreáveis em Épicos, Features e itens de folha (Histórias ou Bugs). Funciona com uma spec sem implementação disponível (Greenfield) ou com uma spec acompanhada de projeto existente (Brownfield). A numeração é documental; não é ID do Azure Boards.

## Detecção do modo

Determine e registre o modo antes de decompor ou refinar:

- **Greenfield:** há spec disponível e nenhum código-fonte relevante no escopo acessível. Registre a ausência e não exija uma inspeção inexistente.
- **Brownfield:** há spec e código-fonte ou projeto relevante disponível. Antes de decompor ou refinar, leia e aplique [references/brownfield-validation.md](references/brownfield-validation.md), inspecione a implementação em modo somente leitura e compare-a apenas com os requisitos da spec.
- Se a presença de código relevante for ambígua, escolha Brownfield conservadoramente, registre a incerteza e os limites da busca e não invente evidência.

## Workflow
1. Leia a spec inteira e crie um inventário de objetivos, atores, capacidades, regras, restrições, exemplos, conflitos e lacunas com suas origens.
2. Detecte o modo. Em Brownfield, conclua a inspeção segura e a matriz `requisito | evidência caminho:linha | status | impacto | confiança` antes da decomposição. Em Greenfield, prossiga somente com a spec e registre que código relevante está ausente.
3. Agrupe objetivos amplos em Épicos; capacidades significativas em Features; resultados coesos para um ator em itens de folha (Histórias ou Bugs). Não crie itens para preencher níveis.
4. Em Brownfield, gere trabalho acionável para lacunas, divergências e mudanças exigidas pela spec. Requisitos classificados como `Implementado` permanecem na cobertura e não geram itens duplicados por padrão. Se o usuário pedir documentação de comportamento existente, o item pode ser mantido como `Implementado`, explicitando que não representa trabalho novo. Para cada item de folha, decida o tipo por [references/backlog-markdown-contract.md](references/backlog-markdown-contract.md#política-de-tipo-user-story-vs-bug): use `Bug` quando a spec classifica aquele resultado específico como `Defeito` ou o status Brownfield é `Divergente`; use `User Story` nos demais casos, inclusive para capacidade nova dentro de uma spec classificada como `Defeito`. A decisão é por item, nunca herdada cegamente da classificação única da spec; registre o tipo escolhido e a justificativa junto à evidência do item.
5. Sugestões, propostas ou hipóteses não confirmadas nunca originam Épico, Feature, item de folha ou regra; registre-as somente em `Itens não cobertos` ou na Conversation de uma demanda confirmada, preservando origem e estado. Código existente também não cria requisito nem confirma decisão de negócio.
6. Para cada História ou Bug, **REQUIRED SUB-SKILL:** use refining-user-stories-with-3c. Em Brownfield, forneça a evidência de implementação somente como contexto rotulado do estado atual. Consuma o resultado da 3C sem recalcular 3W, Conversation, Confirmation ou prontidão. Isso vale igualmente para Bugs: o Card de um Bug ainda usa 3W (Who é afetado pelo comportamento incorreto, What é o comportamento correto esperado, Why é o dano evitado).
7. Numere `E.0.0`, `E.F.0`, `E.F.S`; preserve chaves existentes em atualizações. Declare cada relação no bloco `Parent`; posição e numeração não substituem o pai explícito. Histórias e Bugs sob a mesma Feature compartilham a mesma sequência `S` (são tipos irmãos de folha, não sequências separadas).
8. Renderize modo, raiz ou ausência de código, `Validation Summary`, evidência por item e política de cobertura conforme [references/backlog-markdown-contract.md](references/backlog-markdown-contract.md).
9. Execute `uv run python scripts/validate_backlog.py CAMINHO`; com backlog existente, acrescente `--update`. Corrija violações estruturais e revise semanticamente rastreabilidade, agrupamento, cobertura Brownfield e ausência de regras fabricadas.
10. Entregue o backlog mesmo com Histórias ou Bugs `Não pronta`. Para cada um, liste as lacunas de Card, Conversation e Confirmation que a bloqueiam e sugira ao usuário registrá-las em `## Lacunas e perguntas abertas` da spec de origem e rodar `interviewing-request-gaps` (quando instalada); depois de cada rodada de respostas, regenere o backlog e repita a sugestão até todos os itens de folha ficarem `Prontos` ou até o usuário adiar explicitamente uma lacuna.
11. Se houver copy voltada ao usuário nos requisitos ou nos itens de folha, indique ao usuário a skill `reviewing-copy-in-requirements` como revisão manual opcional. Essa indicação não bloqueia a geração, não cria trabalho novo e não é uma chamada direta à skill.

## Boundaries
- Gere Markdown; não crie work items.
- Não invente Area Path, Iteration Path, Story Points, prioridade, responsável ou datas.
- Item de folha (História ou Bug) rastreável mas incompleto permanece `Não pronta`; com Confirmation `Ausente` ou `Parcial`, Acceptance Criteria fica efetivamente vazio.
- Requisito sem pai justificável entra em `Itens não cobertos`.
- Evidência de implementação pertence a `Implementation Evidence`, `Validation Summary` e, quando útil, a uma síntese rotulada em Description/Conversation; nunca a `Acceptance Criteria`.
- Inspeção Brownfield não autoriza executar scripts, testes, builds, servidores, migrações ou a aplicação do projeto.
- A sugestão de `interviewing-request-gaps` para Histórias ou Bugs `Não pronta` é indicação ao usuário, nunca uma chamada direta a essa skill; não atrase nem condicione a entrega do backlog atual a essa rodada.
- A sugestão de `reviewing-copy-in-requirements` é opcional e manual; não a trate como subskill obrigatória nem condicione a entrega do backlog à revisão de copy.
- A escolha entre User Story e Bug é por item, com justificativa registrada; não decida por conveniência nem herde cegamente a classificação única da spec quando ela cobrir mais de um resultado.
