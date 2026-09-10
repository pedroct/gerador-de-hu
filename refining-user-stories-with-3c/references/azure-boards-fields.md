# Registro da história no Azure Boards

Fontes oficiais da Microsoft:

- [Agile workflow in Azure Boards](https://learn.microsoft.com/en-us/azure/devops/boards/work-items/guidance/agile-process-workflow)
- [Query by titles, IDs, or rich-text fields](https://learn.microsoft.com/en-us/azure/devops/boards/queries/titles-ids-descriptions)

No processo Agile, a Microsoft orienta que `Description` detalhe **quem**, **o que** e **por quê**, sem explicar como desenvolver, e forneça informação suficiente para estimativa, tarefas e testes. `Acceptance Criteria` contém as condições que precisam ser atendidas antes do fechamento da história e serve de base aos testes de aceitação. Ambos são campos HTML:

| Campo | Reference name | Conteúdo 3C |
|---|---|---|
| Description | `System.Description` | Card 3W e síntese atual da Conversation |
| Acceptance Criteria | `Microsoft.VSTS.Common.AcceptanceCriteria` | Confirmation acordada e verificável |

## Description

Use esta forma como padrão adaptável:

```markdown
### Card
**História:** Como ..., quero ..., para ...
**Estado 3W:** Completo | Incompleto

### Conversation
**Contexto e regras confirmadas**
- ...

**Propostas não confirmadas**
- ... — fonte: ...

**Decisões pendentes**
- Pergunta: ...
  - Impacto: ...
  - Decisor: ... | a identificar

**Síntese do refinamento**
- Decisão: ... — fonte/data, se informadas
```

Mantenha uma síntese viva: atualize ou remova informação superada em vez de acumular versões contraditórias. Não invente fonte, data, decisor ou resposta. Uma pessoa ou papel citado — inclusive como alguém que ainda não participou — não é automaticamente decisor; não crie uma decisão de “validar com essa pessoa” sem autoridade explícita. Registre `a identificar` até a autoridade ser informada. Detalhes de solução ficam como proposta técnica, não como parte do Card.

## Acceptance Criteria

Inclua apenas regras confirmadas e exemplos completos produzidos pela skill Gherkin. Não inclua:

- perguntas ou decisões pendentes;
- hipóteses e propostas ainda não aceitas;
- notas de reunião ou histórico da conversa;
- implementação, tarefas ou contrato técnico que não seja comportamento explicitamente contratado;
- explicações sobre por que a história ainda não está pronta.

Sem regra confirmada suficiente, deixe o campo vazio. Não apresente explicação, placeholder nem bloco de código vazio como conteúdo do campo. Use somente a nota operacional `Ação no Azure Boards: deixe o campo sem conteúdo` e informe que os bloqueadores estão em `Description`.

Forma obrigatória na resposta quando o campo estiver vazio:

```markdown
## Azure Boards — Acceptance Criteria

**Ação no Azure Boards:** deixe o campo sem conteúdo.
```

## Formato de saída

Se o usuário for copiar pelo editor do Azure Boards, forneça conteúdo legível com títulos, listas e bloco de código. Se ele pedir payload REST, CSV ou automação, converta para o formato solicitado; para REST, serialize os dois campos como HTML válido. Não execute a gravação sem solicitação explícita.
