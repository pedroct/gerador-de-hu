# Relatório: suporte Greenfield e Brownfield

## Baseline

O baseline em `brownfield-baseline.md` registrou que as quatro skills anteriores não exigiam:

- detecção entre spec sem código e spec acompanhada de projeto;
- inspeção Brownfield antes da decomposição;
- evidência de implementação em formato `caminho:linha`;
- matriz requisito × evidência com estados controlados;
- política para evitar itens duplicados de requisitos já implementados.

No cenário da reabertura em até 24 horas, o serviço existente permitia identificar implementação parcial e provável divergência, mas as skills não obrigavam essa análise nem definiam onde registrar o resultado. O baseline preservou a distinção correta: código não deveria virar regra adicional nem Acceptance Criteria.

## Mudanças implementadas

- A skill de backlog agora detecta explicitamente `Greenfield` e `Brownfield`. Presença ambígua assume Brownfield de forma conservadora, com incerteza e limites registrados.
- O modo Greenfield usa somente a spec e registra a ausência de código relevante, sem exigir inspeção inexistente.
- O modo Brownfield lê `references/brownfield-validation.md`, inspeciona o projeto antes de decompor ou refinar e limita a inspeção a operações somente-leitura. Execução de scripts, testes, builds, servidores, migrações ou aplicação requer autorização explícita.
- A nova referência define a matriz `requisito | evidência caminho:linha | status | impacto | confiança` e os únicos status: `Implementado`, `Parcialmente implementado`, `Divergente`, `Não encontrado` e `Impossível validar`.
- O backlog Brownfield cria trabalho para lacunas, divergências e mudanças rastreáveis. Requisitos `Implementado` permanecem na cobertura e não geram duplicatas por padrão; a exceção de documentação de comportamento existente é marcada como não sendo trabalho novo.
- O contrato Markdown passou a exigir modo, raiz ou ausência de código, incerteza, `Validation Summary` e `Implementation Evidence` por item.
- `Implementation Evidence` é metadado de revisão, não campo Azure. `Acceptance Criteria` continua contendo somente Gherkin de Confirmation `Completa`; com `Ausente` ou `Parcial`, continua vazio.
- 3W, 3C e Gherkin agora aceitam evidência Brownfield apenas como contexto de estado atual. Ela não infere Who/What/Why, não confirma valor ou decisão de negócio e não se transforma em regra Gherkin.
- O README documenta os dois fluxos, a segurança da inspeção, os cinco status e exemplos de classificação.

## Testes RED/GREEN

### RED

Foram adicionados seis testes estáticos antes da alteração das skills. A execução inicial rodou 28 testes e falhou nos seis novos casos:

1. detecção Greenfield/Brownfield e fallback ambíguo;
2. referência, matriz e cinco status exatos;
3. inspeção Brownfield somente-leitura;
4. política que impede código de criar requisitos ou duplicatas;
5. separação entre evidência, Azure Boards e Acceptance Criteria;
6. contrato e README para os dois modos.

Os 22 testes anteriores passaram durante o RED.

### GREEN

Com as mudanças implementadas:

- `uv run python -m unittest discover -s gerar-backlog-azure-boards/tests -v`: **28 testes passaram**;
- `quick_validate.py` em cada uma das quatro skills: **4 validações passaram**;
- `git diff --check`: **passou sem saída**.

## Auto-revisão

- **Rastreabilidade:** toda conclusão Brownfield parte de requisito da spec; comportamento incidental no código fica fora dos itens.
- **Evidência:** caminho e linha são obrigatórios quando disponíveis; busca concluída sem achado e impossibilidade de leitura têm representações distintas. Ausência de evidência nunca equivale a `Implementado`.
- **Decisão de negócio:** código pode descrever estado atual, mas não confirma ator, necessidade, valor, autoridade, regra desejada ou consenso.
- **Backlog acionável:** itens representam o delta pedido pela spec. Requisitos já implementados permanecem no summary, salvo pedido explícito de documentação.
- **Separação Azure:** Description/Conversation pode conter síntese rotulada; `Implementation Evidence` e `Validation Summary` são metadados de revisão; Acceptance Criteria contém somente Gherkin confirmado.
- **Segurança:** inspeção Brownfield não executa o projeto sem autorização.
- **Compatibilidade:** as relações entre as skills permanecem acíclicas; backlog chama somente 3C, enquanto 3W e Gherkin continuam skills-folha. Os 22 testes preexistentes continuam verdes.
- **Escopo:** nenhum script de produção, validador estrutural, configuração de agente ou arquivo fora dos caminhos solicitados foi alterado. Nenhum commit ou push foi feito.
