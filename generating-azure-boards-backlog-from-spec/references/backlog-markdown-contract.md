# Contrato do backlog Markdown para Azure Boards

Este contrato define o documento de revisão produzido pela skill. A hierarquia segue o processo Agile do Azure Boards, mas as chaves do documento não são IDs de work item.

## Definições da hierarquia

- **Epic:** iniciativa ou objetivo amplo que agrupa múltiplas capacidades. O título expressa o objetivo; `Description` registra problema ou oportunidade, resultado esperado, escopo e origem na spec. Não agrega critérios Gherkin das histórias.
- **Feature:** capacidade significativa que entrega valor e agrupa histórias relacionadas. O título expressa a capacidade; `Description` registra capacidade, valor, fronteiras e origem na spec. Não duplica histórias filhas nem seus critérios.
- **User Story:** resultado coeso para um ator, refinável de modo independente. O título diferencia o resultado; `Description` recebe Card e Conversation da 3C; `Acceptance Criteria` recebe somente a Confirmation acordada.

Não crie itens apenas para preencher um nível. Uma demanda rastreável pode permanecer como história incompleta e `Não pronta`. Sugestões, propostas ou hipóteses não confirmadas nunca originam item ou regra; mantenha-as somente em `Itens não cobertos` ou na Conversation de uma demanda confirmada. Conteúdo sem pai justificável também fica em `Itens não cobertos`.

## Numeração e atualização

| Nível | Formato | Exemplo | Pai explícito |
|---|---|---|---|
| Epic | `E.0.0` | `1.0.0` | Não se aplica |
| Feature | `E.F.0` | `1.1.0` | Exatamente um Epic `E.0.0` |
| User Story | `E.F.S` | `1.1.1` | Exatamente uma Feature `E.F.0` |

- `E`, `F` e `S` são inteiros positivos sequenciais; os zeros identificam o nível, não fazem parte da sequência.
- Em documento novo, cada sequência começa em 1: Epics na raiz, Features sob cada Epic e histórias sob cada Feature.
- Toda Feature e toda User Story declaram a chave de seu pai no bloco `Parent`. O item referenciado existe no mesmo documento, tem o tipo pai correto e usa prefixo compatível: uma Feature `E.F.0` referencia o Epic `E.0.0`; uma User Story `E.F.S` referencia a Feature `E.F.0`. Aninhamento visual ou compatibilidade numérica não bastam.
- Ao atualizar um backlog existente, preserve as chaves publicadas e acrescente novas chaves ao final do respectivo pai.
- Não renumere itens existentes e não reutilize chaves removidas; por isso uma atualização pode conter lacunas.
- Nunca apresente a chave documental como ID atribuído pelo Azure Boards.

## Template completo

```markdown
# Backlog para Azure Boards

## Metadados e cobertura
- Spec de origem: [documento, versão ou localização]
- Escopo analisado: [seções ou limites]
- Itens não cobertos: Nenhum

## 1.0.0 [Epic] Título do épico

### Description
Objetivo, valor e escopo.

Origem na spec: [seção/âncora/localização disponível]

### 1.1.0 [Feature] Título da feature

#### Parent
`1.0.0`

#### Description
Capacidade, resultado e limites de escopo.

Origem na spec: [seção/âncora/localização disponível]

#### 1.1.1 [User Story] Título da história

##### Parent
`1.1.0`

##### Description

###### Card
[conteúdo do Card retornado pela 3C]

###### Conversation
[conteúdo da Conversation retornado pela 3C]

##### Acceptance Criteria

##### Refinement Status
- Card: [estado único retornado pela 3C]
- Conversation: [estado único retornado pela 3C]
- Confirmation: [estado único retornado pela 3C]
- Prontidão: [estado único retornado pela 3C]
- Origem na spec: [seção/âncora/localização disponível]
```

Repita os blocos nos mesmos níveis de cabeçalho: Epic em `##`, Feature em `###` e User Story em `####`; as seções de cada item usam um nível adicional.

## Conteúdo dos campos

### Description

- Em Epic: problema ou oportunidade, resultado esperado, escopo e `Origem na spec`.
- Em Feature: capacidade, valor, fronteiras e `Origem na spec`.
- Em User Story: contém, nesta ordem e exatamente uma vez, os headings `###### Card` e `###### Conversation`. Sob cada heading, transcreva o conteúdo correspondente retornado pela `refining-user-stories-with-3c`; não recalcule nem reestruture o conteúdo.
- Lacunas, conflitos e decisões pendentes podem aparecer na Conversation com suas fontes e estados. Não complete ator, valor, regra ou solução por plausibilidade.

### Acceptance Criteria

- Contém zero ou mais blocos cercados `gherkin`, copiados dos blocos retornados pela Confirmation da 3C, e nenhum outro conteúdo.
- Não acrescente regras narrativas, títulos, listas, comentários, placeholders ou texto fora dos blocos Gherkin.
- Com Confirmation `Ausente` ou `Parcial`, deixe a seção efetivamente em branco: entre o heading `##### Acceptance Criteria` e o heading seguinte pode haver somente espaço em branco.
- Com Confirmation `Completa`, copie zero ou mais blocos Gherkin retornados; não crie, complete ou reformule regras.

## Refinement Status

`Refinement Status` é metadado do documento de preparação, fora dos campos do Azure Boards. Ele registra os estados devolvidos pela 3C e a origem da história; não é anexado automaticamente a `Description` nem a `Acceptance Criteria`.

Para `Card`, `Conversation`, `Confirmation` e `Prontidão`, escreva exatamente uma linha e exatamente um valor retornado pela 3C. Não serialize alternativas com barras ou listas. Os valores possíveis são: `Estruturado` ou `Incompleto` para Card; `Pendente`, `Em andamento` ou `Suficiente para o escopo` para Conversation; `Ausente`, `Parcial` ou `Completa` para Confirmation; `Pronta` ou `Não pronta` para Prontidão. Transcreva o único valor recebido, sem recalcular estados ou gates.

## Rastreabilidade e itens não cobertos

- Todo Epic, Feature e User Story deve indicar uma seção, âncora ou localização disponível na spec.
- Preserve ambas as fontes quando houver conflito e encaminhe a decisão à Conversation.
- Compare o inventário inicial com a hierarquia final. Inclua em `Itens não cobertos` todo requisito não representado, requisito sem pai justificável, sugestão, proposta ou hipótese não confirmada e candidato sem origem rastreável.
- Não esconda lacunas criando pais artificiais, histórias especulativas ou critérios fabricados.

Se não houver entrada, serialize exatamente `- Itens não cobertos: Nenhum`. Caso contrário, use `- Itens não cobertos:` e repita um bloco por entrada, sempre com os quatro campos:

```markdown
- Itens não cobertos:
  - Conteúdo: [conteúdo não coberto]
    - Origem: [seção/âncora/localização disponível]
    - Estado: [estado na fonte]
    - Justificativa: [por que não integra a hierarquia]
```

## Markdown de revisão e campos do Azure Boards

O artefato gerado é Markdown para revisão humana e não autoriza criar ou modificar work items. Em uma importação posterior:

- `Description` corresponde a `System.Description`.
- `Acceptance Criteria` corresponde a `Microsoft.VSTS.Common.AcceptanceCriteria`.
- Esses campos são HTML no Azure Boards; a etapa de importação deve converter o Markdown preservando títulos, listas e blocos Gherkin.
- `Parent`, `Refinement Status`, metadados, cobertura e `Itens não cobertos` pertencem ao documento de preparação e exigem mapeamento explícito caso outra automação venha a consumi-los.

Não invente Area Path, Iteration Path, Story Points, prioridade, responsável ou datas. Não gere tarefas técnicas abaixo das histórias.

## Referências oficiais

- [Define features and epics](https://learn.microsoft.com/en-us/azure/devops/boards/backlogs/define-features-epics)
- [Agile process workflow](https://learn.microsoft.com/en-us/azure/devops/boards/work-items/guidance/agile-process-workflow)
- [Titles, IDs, and descriptions](https://learn.microsoft.com/en-us/azure/devops/boards/queries/titles-ids-descriptions)
