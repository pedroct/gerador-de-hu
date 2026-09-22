# Task 1: Registrar o comportamento RED sem a quarta skill

## Files

- Read: `docs/superpowers/specs/2026-09-10-azure-boards-backlog-skill-design.md`
- Read: `refining-user-stories-with-3c/SKILL.md`
- Read: `refining-user-stories-with-3w/SKILL.md`
- Read: `refining-user-stories-with-gherkin/SKILL.md`
- Create: nenhum artefato de produto; registre o resultado apenas no relatório indicado pelo controller.

## Interfaces

- Consumes: uma spec textual com dois objetivos, regras confirmadas, propostas técnicas e decisões pendentes.
- Produces: baseline observado para orientar a forma mínima da quarta skill.

## Step 1: Executar o cenário sem a quarta skill

Em contexto fresco, não use qualquer skill de geração de backlog. Use as skills 3C, 3W e Gherkin existentes e responda internamente ao pedido:

```text
Analise a spec abaixo e gere um backlog Markdown para Azure Boards na hierarquia
1.0.0 Épico, 1.1.0 Feature e 1.1.1 História. Use as skills 3C, 3W e
Gherkin existentes, mas nenhuma skill de geração de backlog.

Spec:
- Objetivo A: reduzir correções manuais de diligências.
- O analista responsável pode reabrir uma diligência em até 24 horas, com
  justificativa; o status volta para Em análise; essas regras foram confirmadas.
- Auditoria detalhada foi sugerida por compliance, mas os campos ainda não foram decididos.
- Objetivo B: permitir consulta gerencial de diligências atrasadas.
- O gerente precisa decidir redistribuição de trabalho, mas atraso, filtros e
  resultados observáveis ainda não foram definidos.
- Um desenvolvedor sugeriu dois endpoints; isso não foi aprovado como requisito.

Produza um único documento Markdown. Não faça perguntas e não invente regras.
```

## Step 2: Avaliar o baseline

Registre se ocorreu qualquer destes sintomas:

- hierarquia achatada ou pai implícito;
- numeração duplicada ou inconsistente;
- endpoint promovido a requisito;
- perda da origem na spec;
- história gerencial marcada pronta apesar das lacunas;
- Acceptance Criteria preenchido com hipóteses;
- Description sem Card/Conversation;
- formato não reutilizável nos campos do Azure Boards.

## Step 3: Fixar os critérios GREEN

Liste somente as falhas realmente observadas e os critérios GREEN correspondentes. Não crie ou modifique arquivos das skills.
