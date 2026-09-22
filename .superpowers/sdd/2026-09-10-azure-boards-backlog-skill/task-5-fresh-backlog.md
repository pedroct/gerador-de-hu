# Backlog para Azure Boards

## Metadados e cobertura
- Spec de origem: spec fornecida no pedido da Task 5
- Escopo analisado: Objetivos A, B e C e os fatos, decisões, propostas e lacunas associados
- Itens não cobertos:
  - Conteúdo: Auditoria detalhada sugerida por compliance, com campos ainda não decididos.
    - Origem: Objetivo A, terceira frase
    - Estado: Proposta não confirmada
    - Justificativa: A sugestão não foi confirmada como requisito e não pode originar item nem regra.
  - Conteúdo: Dois endpoints sugeridos por um desenvolvedor.
    - Origem: Objetivo B, terceira frase
    - Estado: Proposta não aprovada
    - Justificativa: A solução técnica não foi aprovada como requisito e não pode originar item nem regra.

## 1.0.0 [Epic] Reduzir correções manuais de diligências

### Description
Objetivo de reduzir correções manuais de diligências. O escopo representado é a capacidade confirmada de reabertura pelo analista responsável.

Origem na spec: Objetivo A

### 1.1.0 [Feature] Reabrir diligência

#### Parent
`1.0.0`

#### Description
Permite ao analista responsável reabrir uma diligência conforme as regras confirmadas de prazo, justificativa e estado resultante. Auditoria detalhada permanece fora do escopo confirmado.

Origem na spec: Objetivo A, segunda e terceira frases

#### 1.1.1 [User Story] Reabrir diligência sob as regras confirmadas

##### Parent
`1.1.0`

##### Description

###### Card
- História: Como analista responsável, quero reabrir uma diligência em até 24 horas, com justificativa, para reduzir correções manuais de diligências.
- 3W:
  - Who — Confirmado: analista responsável.
  - What — Confirmado: reabrir uma diligência em até 24 horas, com justificativa.
  - Why — Confirmado: reduzir correções manuais de diligências.
- Estado 3W: Completo.

###### Conversation
- Fatos confirmados: o analista responsável pode reabrir uma diligência em até 24 horas; a reabertura exige justificativa; o status volta para `Em análise`.
- Decisão confirmada: as regras de ator, prazo, justificativa e status resultante foram confirmadas.
- Proposta não confirmada: compliance sugeriu auditoria detalhada, mas os campos ainda não foram decididos; essa proposta não integra a regra nem o escopo da história.
- Pergunta pendente não bloqueadora deste escopo: quais campos uma eventual auditoria detalhada deve conter? Impacto: impede incluir auditoria como requisito. Responsável pela decisão: a identificar.

##### Acceptance Criteria

```gherkin
# language: pt
Funcionalidade: Reabertura de diligência

  Regra: O analista responsável pode reabrir uma diligência em até 24 horas mediante justificativa

    Cenário: Reabrir no limite de 24 horas com justificativa
      Dado que uma diligência está no limite de 24 horas aplicável à sua reabertura
      Quando o analista responsável a reabre com uma justificativa
      Então o status da diligência volta para "Em análise"
```

##### Refinement Status
- Card: Estruturado
- Conversation: Suficiente para o escopo
- Confirmation: Completa
- Prontidão: Pronta
- Origem na spec: Objetivo A, primeira à terceira frases

## 2.0.0 [Epic] Permitir consulta gerencial de diligências atrasadas

### Description
Objetivo de permitir consulta gerencial de diligências atrasadas para apoiar decisões de redistribuição de trabalho. Definições comportamentais essenciais permanecem pendentes.

Origem na spec: Objetivo B

### 2.1.0 [Feature] Consultar diligências atrasadas

#### Parent
`2.0.0`

#### Description
Capacidade gerencial de consultar diligências atrasadas para decidir redistribuição de trabalho, sem definição ainda de atraso, filtros ou resultados observáveis. Endpoints sugeridos não fazem parte do requisito.

Origem na spec: Objetivo B, primeira à terceira frases

#### 2.1.1 [User Story] Consultar diligências atrasadas para redistribuir trabalho

##### Parent
`2.1.0`

##### Description

###### Card
- História: Como gerente, quero consultar diligências atrasadas, para decidir a redistribuição de trabalho.
- 3W:
  - Who — Confirmado: gerente.
  - What — Confirmado: consultar diligências atrasadas.
  - Why — Confirmado: decidir a redistribuição de trabalho.
- Estado 3W: Completo.

###### Conversation
- Fatos confirmados: o gerente precisa consultar diligências atrasadas para decidir a redistribuição de trabalho.
- Decisões comportamentais confirmadas: nenhuma além da necessidade e do valor expressos no Card.
- Proposta não aprovada: um desenvolvedor sugeriu dois endpoints; a proposta não integra o requisito.
- Perguntas bloqueadoras:
  - O que define uma diligência como atrasada? Impacto: impede identificar a população consultada. Responsável pela decisão: a identificar.
  - Quais filtros são necessários? Impacto: impede definir o comportamento da consulta. Responsável pela decisão: a identificar.
  - Qual resultado observável a consulta deve apresentar? Impacto: impede verificar a aceitação. Responsável pela decisão: a identificar.

##### Acceptance Criteria

##### Refinement Status
- Card: Estruturado
- Conversation: Em andamento
- Confirmation: Ausente
- Prontidão: Não pronta
- Origem na spec: Objetivo B, primeira à terceira frases

## 3.0.0 [Epic] Permitir o registro de contestação de diligência

### Description
Objetivo de permitir que o analista registre uma contestação de diligência e preserve sua justificativa. O resultado observável apresentado após o registro permanece pendente.

Origem na spec: Objetivo C

### 3.1.0 [Feature] Registrar contestação de diligência

#### Parent
`3.0.0`

#### Description
Capacidade confirmada de registrar uma contestação de diligência para preservar a justificativa, ainda sem resultado observável decidido.

Origem na spec: Objetivo C

#### 3.1.1 [User Story] Registrar contestação e preservar a justificativa

##### Parent
`3.1.0`

##### Description

###### Card
- História: Como analista, quero registrar uma contestação de diligência, para preservar a justificativa.
- 3W:
  - Who — Confirmado: analista.
  - What — Confirmado: registrar uma contestação de diligência.
  - Why — Confirmado: preservar a justificativa.
- Estado 3W: Completo.

###### Conversation
- Fatos confirmados: o ator é o analista; a capacidade é registrar uma contestação de diligência; o valor é preservar a justificativa.
- Regra confirmada: a justificativa informada deve ser preservada no registro da contestação.
- Decisão pendente bloqueadora: qual resultado observável deve ser apresentado ao analista após o registro? Impacto: impede formar um exemplo de aceitação completo. Responsável pela decisão: a identificar.

##### Acceptance Criteria

##### Refinement Status
- Card: Estruturado
- Conversation: Em andamento
- Confirmation: Parcial
- Prontidão: Não pronta
- Origem na spec: Objetivo C
