# Contrato do backlog Markdown para Azure Boards

Este contrato define o documento de revisão produzido pela skill. A hierarquia segue o processo Agile do Azure Boards, mas as chaves do documento não são IDs de work item.

O documento sempre declara um modo:

- **Greenfield:** a spec está disponível e não há código-fonte relevante no escopo acessível. A cobertura registra a ausência; não se exige matriz de implementação.
- **Brownfield:** a spec e um projeto relevante estão presentes, ou a presença de código permanece ambígua. A cobertura inclui raiz, limites, incerteza, matriz requisito × evidência e política aplicada aos itens.

## Definições da hierarquia

- **Epic:** iniciativa ou objetivo amplo que agrupa múltiplas capacidades. O título expressa o objetivo; `Description` registra problema ou oportunidade, resultado esperado, escopo e origem na spec. Não agrega critérios Gherkin das histórias.
- **Feature:** capacidade significativa que entrega valor e agrupa histórias relacionadas. O título expressa a capacidade; `Description` registra capacidade, valor, fronteiras e origem na spec. Não duplica histórias filhas nem seus critérios.
- **User Story:** resultado coeso para um ator, refinável de modo independente. O título diferencia o resultado; `Description` recebe Card e Conversation da 3C; `Acceptance Criteria` recebe somente a Confirmation acordada.
- **Bug:** defeito confirmado — o comportamento atual diverge de uma regra, garantia ou expectativa já estabelecida para aquele fluxo, e a spec de origem (ou o status Brownfield `Divergente`) trata isso como incorreto, não como capacidade ausente. Segue a mesma disciplina de refinamento 3C de uma User Story (Card via 3W, Conversation, Confirmation via Gherkin); o título expressa o comportamento incorreto observado e o esperado. `Description` recebe Card e Conversation da 3C; `Acceptance Criteria` recebe somente a Confirmation acordada.

Não crie itens apenas para preencher um nível. Uma demanda rastreável pode permanecer como item de folha incompleto e `Não pronta`. Sugestões, propostas ou hipóteses não confirmadas nunca originam item ou regra; mantenha-as somente em `Itens não cobertos` ou na Conversation de uma demanda confirmada. Conteúdo sem pai justificável também fica em `Itens não cobertos`.

## Título curto

O título no heading do item (`[Epic] Título...`) permanece completo e descritivo — é o que aparece no documento e no `Parent` de outros itens. Todo item também declara, em uma subseção própria `Título curto`, uma versão reduzida desse mesmo título: até 60 caracteres, mantendo o sentido essencial sem repetir o tipo, o ator quando óbvio pelo contexto, ou o código documental. O publicador usa exclusivamente essa versão curta no campo `Title` do Azure Boards (prefixada pela data de geração e pela chave documental) porque o título completo de uma User Story ou Bug, no estilo comportamental "Ator faz X para Y", frequentemente ultrapassa o que a interface do Azure Boards mostra sem truncar.

Exemplo: heading `#### 1.1.1 [User Story] Gestor da Aplicação cadastra e mantém a hierarquia de lotações` recebe `Título curto` = `Cadastro de hierarquia de lotações`.

## Política de tipo (User Story vs. Bug)

User Story e Bug são tipos irmãos de folha: usam o mesmo esquema de numeração `E.F.S`, compartilham a mesma sequência `S` sob a mesma Feature (não são contadores separados por tipo) e seguem a mesma disciplina de refinamento 3C. Uma Feature pode ter filhos mistos, por exemplo `1.1.1 [User Story]` e `1.1.2 [Bug]`. Não crie um terceiro tipo nem misture os dois em um único item.

A classificação da spec de origem (`Defeito`, `Melhoria` ou `Outro`) é um metadado único por pedido inteiro, mas o backlog pode decompor esse pedido em vários itens de folha — a decisão entre Bug e User Story é tomada **por item**, nunca herdada cegamente da classificação geral da spec. Uma mesma spec pode originar tanto Bugs quanto Histórias.

Para cada item de folha:

- Use **Bug** quando o item corrige um comportamento que a spec de origem classifica como `Defeito` para aquele resultado específico, **ou** cujo status na matriz Brownfield é `Divergente` de uma regra/garantia já estabelecida no mesmo fluxo. O comportamento atual é tratado como incorreto, não como capacidade ausente.
- Use **User Story** quando a spec classifica o resultado como `Melhoria` ou `Outro`, **ou** quando o item representa uma capacidade nova — inclusive dentro de uma spec cuja classificação geral seja `Defeito`, se aquele item específico for além da correção do defeito relatado (ex.: uma prevenção proativa adicional decidida em entrevista, que o próprio pedido não chegou a apontar como comportamento incorreto).
- Registre, junto à evidência do item (`Implementation Evidence` ou síntese rotulada na Conversation), o tipo escolhido e a justificativa (classificação da spec e/ou status Brownfield que a sustentam).

## Numeração e atualização

| Nível | Formato | Exemplo | Pai explícito |
|---|---|---|---|
| Epic | `E.0.0` | `1.0.0` | Não se aplica |
| Feature | `E.F.0` | `1.1.0` | Exatamente um Epic `E.0.0` |
| User Story | `E.F.S` | `1.1.1` | Exatamente uma Feature `E.F.0` |
| Bug | `E.F.S` | `1.1.2` | Exatamente uma Feature `E.F.0` |

User Story e Bug compartilham a mesma sequência `S` sob a mesma Feature: não são contadores separados por tipo.

- `E`, `F` e `S` são inteiros positivos sequenciais; os zeros identificam o nível, não fazem parte da sequência.
- Em documento novo, cada sequência começa em 1: Epics na raiz, Features sob cada Epic e itens de folha (Histórias e Bugs juntos) sob cada Feature.
- Toda Feature e todo item de folha declaram a chave de seu pai no bloco `Parent`. O item referenciado existe no mesmo documento, tem o tipo pai correto e usa prefixo compatível: uma Feature `E.F.0` referencia o Epic `E.0.0`; um item de folha `E.F.S` referencia a Feature `E.F.0`. Aninhamento visual ou compatibilidade numérica não bastam.
- Ao atualizar um backlog existente, preserve as chaves publicadas e acrescente novas chaves ao final do respectivo pai.
- Não renumere itens existentes e não reutilize chaves removidas; por isso uma atualização pode conter lacunas.
- Nunca apresente a chave documental como ID atribuído pelo Azure Boards.

## Depende de e Bloqueia

Campo opcional, presente apenas quando o item nasceu do fluxo de `especificar-telas-ux-ui` (uma seção
`## Necessidade de especificação de tela` na spec de origem, com o documento companheiro `Spec: Telas
UX-UI`). Um item funcional (User Story ou Bug) que depende de tela declara `Depende de` com uma ou mais
chaves `E.F.S`, uma por plataforma que precisa de especificação; o item de design correspondente (sempre
`User Story`) declara `Bloqueia` com a chave `E.F.S` do item funcional que ele libera.

- É texto informativo dentro de `Description`, na mesma seção da Conversation — não é um novo nível hierárquico e não substitui `Parent`.
- Não altera a prontidão calculada pela 3C: um item pode estar `Pronto` segundo Card, Conversation e
  Confirmation mesmo com `Depende de` apontando para um item de design ainda não `Pronto`. A 3C continua
  sendo a única dona da prontidão geral.
- Não cria nem representa o link formal Predecessor/Sucessor do Azure Boards; essa relação, quando
  existir na importação, é responsabilidade de uma etapa de publicação futura.
- Sempre um item de design por plataforma necessária: um item funcional que depende de tela em web e em
  mobile declara `Depende de` com as duas chaves.

## Template completo

```markdown
# Backlog para Azure Boards

## Metadados e cobertura
- Data de geração: `[AAAA-MM-DD]`
- Spec de origem: [documento, versão ou localização]
- Escopo analisado: [seções ou limites]
- Modo: Greenfield | Brownfield
- Raiz analisada: [caminho | Não se aplica — nenhum código-fonte relevante disponível]
- Código-fonte relevante: [Presente | Ausente | Presença ambígua]
- Incerteza de detecção: [Nenhuma | descrição e limites da busca]
- Itens não cobertos: Nenhum

## 1.0.0 [Epic] Título do épico

### Título curto
[até 60 caracteres]

### Description
Objetivo, valor e escopo.

Origem na spec: [seção/âncora/localização disponível]

### 1.1.0 [Feature] Título da feature

#### Parent
`1.0.0`

#### Título curto
[até 60 caracteres]

#### Description
Capacidade, resultado e limites de escopo.

Origem na spec: [seção/âncora/localização disponível]

#### 1.1.1 [User Story] Título da história

##### Parent
`1.1.0`

##### Título curto
[até 60 caracteres]

##### Description

###### Card
[conteúdo do Card retornado pela 3C]

###### Conversation
[conteúdo da Conversation retornado pela 3C]

[Se aplicável: `Depende de: 1.1.2` (chave do item de design; uma por plataforma pendente) — ou `Bloqueia: 1.1.1` quando este item for a User Story de design gerada por especificar-telas-ux-ui; ambos informativos, não substituem Parent nem alteram a prontidão da 3C]

Origem na spec: [seção/âncora/localização disponível]

##### Implementation Evidence *(metadado de revisão — não é copiado para o Azure Boards; o campo `Description` termina no fim da Conversation acima)*
[Em Greenfield: `Não se aplica — modo Greenfield; nenhum código-fonte relevante disponível.`]
[Em Brownfield: linhas da matriz relacionadas ao item, ou síntese rotulada com status, referências `caminho:linha`, impacto e confiança]

##### Acceptance Criteria

#### 1.1.2 [Bug] Título do bug

##### Parent
`1.1.0`

##### Título curto
[até 60 caracteres]

##### Description

###### Card
[conteúdo do Card retornado pela 3C, enquadrado como comportamento incorreto → esperado]

###### Conversation
[conteúdo da Conversation retornado pela 3C]

[Se aplicável: `Depende de: 1.1.2` (chave do item de design; uma por plataforma pendente) — informativo, não substitui Parent nem altera a prontidão da 3C]

Origem na spec: [seção/âncora/localização disponível]

##### Implementation Evidence *(metadado de revisão — não é copiado para o Azure Boards; o campo `Description` termina no fim da Conversation acima)*
[Em Greenfield: `Não se aplica — modo Greenfield; nenhum código-fonte relevante disponível.`]
[Em Brownfield: linhas da matriz relacionadas ao item, ou síntese rotulada com status, referências `caminho:linha`, impacto e confiança — inclua a justificativa do tipo `Bug` (classificação da spec e/ou status Brownfield que a sustentam)]

##### Acceptance Criteria
```

Repita os blocos nos mesmos níveis de cabeçalho: Epic em `##`, Feature em `###` e item de folha (User Story ou Bug) em `####`; as seções de cada item usam um nível adicional.

## Metadados mínimos

- `Data de geração` registra a data (formato `AAAA-MM-DD`, entre crases) em que este documento foi gerado pela primeira vez. É fixa: uma atualização do backlog (modo `--update` do validador) nunca a recalcula para a data corrente, porque o publicador usa esse valor — nunca o relógio — para prefixar o título de cada item no Azure Boards, e recalculá-la quebraria a comparação de título na retomada de uma publicação parcial. Ela também desambigua itens de backlogs diferentes que reusam a mesma numeração `E.F.S`.
- `Modo` contém um único valor: `Greenfield` ou `Brownfield`.
- Em Greenfield, `Raiz analisada` e `Código-fonte relevante` registram explicitamente que não há código relevante. Não invente raiz nem evidência.
- Em Brownfield, `Raiz analisada` identifica o caminho efetivamente inspecionado. Se a presença ou relevância do projeto era ambígua, use `Presença ambígua` e descreva a incerteza e os limites da busca.
- Em Brownfield, mantenha a matriz definida em [brownfield-validation.md](brownfield-validation.md) como insumo de análise e use-a para decidir cobertura, evidência e tipo do item; não a serialize em uma seção própria do backlog.
- Use exatamente os status `Implementado`, `Parcialmente implementado`, `Divergente`, `Não encontrado` e `Impossível validar`; ausência de evidência nunca é serializada como `Implementado`.

## Conteúdo dos campos

### Description

- Em Epic: problema ou oportunidade, resultado esperado, escopo e `Origem na spec`.
- Em Feature: capacidade, valor, fronteiras e `Origem na spec`.
- Em User Story ou Bug: contém, nesta ordem e exatamente uma vez, os headings `###### Card` e `###### Conversation`. Sob cada heading, transcreva o conteúdo correspondente retornado pela `refinar-historias-3c`; não recalcule nem reestruture o conteúdo. Preserve as barras invertidas de quebra de linha dura do template da `História:` (Card) exatamente como a `refinar-historias-3c` as produz — sem elas, o conversor Markdown→HTML do publicador junta as linhas Como/quero/para em um parágrafo único.
- Lacunas, conflitos e decisões pendentes podem aparecer na Conversation com suas fontes e estados. Não complete ator, valor, regra ou solução por plausibilidade.

### Implementation Evidence

- O heading carrega sempre a anotação `*(metadado de revisão — não é copiado para o Azure Boards; o campo Description termina no fim da Conversation acima)*`, como no template — ela marca visualmente, para quem for copiar o conteúdo para o Azure Boards, onde `Description` termina.
- É o único bloco de evidência técnica separado dos campos copiáveis do Azure Boards.
- Em Greenfield, declare que não se aplica porque não há código-fonte relevante disponível.
- Em Brownfield, associe ao item somente evidências que tenham origem na spec. Registre status, referências `caminho:linha`, impacto e confiança; quando não houver referência, preserve `Nenhuma evidência encontrada` ou o motivo que tornou a validação impossível.
- Uma síntese pode também aparecer em `Description`/Conversation quando ajuda a distinguir estado atual e mudança desejada, sempre rotulada como evidência de implementação.
- Evidência de implementação nunca pertence a `Acceptance Criteria` e nunca confirma ator, valor, decisão de negócio ou regra desejada.

### Acceptance Criteria

- Contém zero ou mais blocos cercados `gherkin`, copiados dos blocos retornados pela Confirmation da 3C, e nenhum outro conteúdo.
- Não acrescente regras narrativas, títulos, listas, comentários, placeholders ou texto fora dos blocos Gherkin.
- Com Confirmation `Ausente` ou `Parcial`, deixe a seção efetivamente em branco: entre o heading `##### Acceptance Criteria` e o heading seguinte pode haver somente espaço em branco.
- Com Confirmation `Completa`, copie zero ou mais blocos Gherkin retornados; não crie, complete ou reformule regras.
- Não copie caminhos, símbolos, trechos de código, status Brownfield nem conclusões da matriz para esta seção. Gherkin expressa somente a Confirmation completa, baseada em comportamento desejado confirmado na Conversation.

## Rastreabilidade e itens não cobertos

- Todo Epic, Feature e item de folha (User Story ou Bug) deve indicar uma seção, âncora ou localização disponível na spec.
- Preserve ambas as fontes quando houver conflito e encaminhe a decisão à Conversation.
- Compare o inventário inicial com a hierarquia final. Inclua em `Itens não cobertos` todo requisito não representado, requisito sem pai justificável, sugestão, proposta ou hipótese não confirmada e candidato sem origem rastreável.
- Não esconda lacunas criando pais artificiais, itens de folha especulativos ou critérios fabricados.

### Política Brownfield para criação de itens

- Gere backlog acionável para lacunas, divergências e mudanças exigidas pela spec. O item descreve o delta desejado, não uma tarefa genérica de “alinhar o código”.
- Requisitos `Implementado` permanecem cobertos pela análise e não geram duplicatas por padrão.
- Quando o usuário pedir documentação de comportamento existente, um item `Implementado` pode ser mantido; registre em `Implementation Evidence` que ele representa documentação do estado atual e não trabalho novo.
- `Impossível validar` não cria uma regra nem um item de produto por si só. Mantenha a incerteza e só crie item quando houver mudança rastreável já exigida pela spec.
- Código fora do escopo da spec não cria item. Propostas e hipóteses continuam em `Itens não cobertos` ou Conversation, nunca em Acceptance Criteria.
- Decida o tipo de cada item de folha gerado (User Story ou Bug) conforme a [Política de tipo](#política-de-tipo-user-story-vs-bug); a decisão é por item, não herdada da classificação única da spec.

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

- O rótulo `[User Story]` ou `[Bug]` no título indica o tipo de work item do processo Agile a criar na importação.
- `Description` corresponde a `System.Description`.
- `Acceptance Criteria` corresponde a `Microsoft.VSTS.Common.AcceptanceCriteria`.
- Esses campos são HTML no Azure Boards; a etapa de importação deve converter o Markdown preservando títulos, listas e blocos Gherkin.
- `Parent`, `Implementation Evidence`, metadados e `Itens não cobertos` pertencem ao documento de preparação e exigem mapeamento explícito caso outra automação venha a consumi-los.

Não invente Area Path, Iteration Path, Story Points, prioridade, responsável ou datas. Não gere tarefas técnicas abaixo dos itens de folha.

## Referências oficiais

- [Define features and epics](https://learn.microsoft.com/en-us/azure/devops/boards/backlogs/define-features-epics)
- [Agile process workflow](https://learn.microsoft.com/en-us/azure/devops/boards/work-items/guidance/agile-process-workflow)
- [Titles, IDs, and descriptions](https://learn.microsoft.com/en-us/azure/devops/boards/queries/titles-ids-descriptions)
- [Bug work item type (Agile process)](https://learn.microsoft.com/en-us/azure/devops/boards/work-items/guidance/agile-process-workflow#bug)
