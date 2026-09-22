# Evidência comportamental em contexto novo — Task 5

## 1. Spec

```text
- Objetivo A: reduzir correções manuais de diligências.
- O analista responsável pode reabrir uma diligência em até 24 horas, com justificativa; o status volta para Em análise; essas regras foram confirmadas.
- Auditoria detalhada foi sugerida por compliance, mas os campos ainda não foram decididos.
- Objetivo B: permitir consulta gerencial de diligências atrasadas.
- O gerente precisa decidir redistribuição de trabalho, mas atraso, filtros e resultados observáveis ainda não foram definidos.
- Um desenvolvedor sugeriu dois endpoints; isso não foi aprovado como requisito.
- Objetivo C: permitir que o analista registre uma contestação de diligência. O analista, o registro da contestação e o valor de preservar a justificativa foram confirmados; a Conversation confirmou a regra de que a justificativa informada deve ser preservada no registro. O resultado observável apresentado ao analista após o registro ainda não foi decidido.
```

## 2. Payload bruto da 3C por história

Este payload é o resultado da 3C anterior à geração do backlog. Ele separa Card, Conversation, Confirmation, prontidão e os fatos/decisões usados.

### História A — Reabrir diligência sob as regras confirmadas

#### Card

- História: Como analista responsável, quero reabrir uma diligência em até 24 horas, com justificativa, para reduzir correções manuais de diligências.
- 3W:
  - Who — Confirmado: analista responsável.
  - What — Confirmado: reabrir uma diligência em até 24 horas, com justificativa.
  - Why — Confirmado: reduzir correções manuais de diligências.
- Estado 3W: Completo.

#### Conversation

- Fatos confirmados: o analista responsável pode reabrir uma diligência em até 24 horas; a reabertura exige justificativa; o status volta para `Em análise`.
- Decisão confirmada: as regras de ator, prazo, justificativa e status resultante foram confirmadas.
- Proposta não confirmada: compliance sugeriu auditoria detalhada, mas os campos ainda não foram decididos; essa proposta não integra a regra nem o escopo da história.
- Pergunta pendente não bloqueadora deste escopo: quais campos uma eventual auditoria detalhada deve conter? Impacto: impede incluir auditoria como requisito. Responsável pela decisão: a identificar.

#### Confirmation

- Regras confirmadas: o analista responsável pode reabrir a diligência no limite de até 24 horas, mediante justificativa, e o status resultante é `Em análise`.
- Exemplos de aceitação:

```gherkin
# language: pt
Funcionalidade: Reabertura de diligência

  Regra: O analista responsável pode reabrir uma diligência em até 24 horas mediante justificativa

    Cenário: Reabrir no limite de 24 horas com justificativa
      Dado que uma diligência está no limite de 24 horas aplicável à sua reabertura
      Quando o analista responsável a reabre com uma justificativa
      Então o status da diligência volta para "Em análise"
```

- Dúvidas e hipóteses: os campos de uma auditoria detalhada continuam pendentes, mas a auditoria é apenas proposta e não bloqueia a Confirmation do escopo confirmado de reabertura.
- Estado da Confirmation: Completa.

#### Estado 3C e prontidão

- Card: Estruturado
- Conversation: Suficiente para o escopo
- Confirmation: Completa
- Prontidão: Pronta

#### Fatos e decisões preservados

- Fato: o objetivo é reduzir correções manuais de diligências.
- Decisão confirmada: somente o analista responsável reabre a diligência, em até 24 horas, com justificativa; o status volta para `Em análise`.
- Proposta: auditoria detalhada, sugerida por compliance.
- Decisão pendente: campos da eventual auditoria detalhada.

### História B — Consultar diligências atrasadas para redistribuir trabalho

#### Card

- História: Como gerente, quero consultar diligências atrasadas, para decidir a redistribuição de trabalho.
- 3W:
  - Who — Confirmado: gerente.
  - What — Confirmado: consultar diligências atrasadas.
  - Why — Confirmado: decidir a redistribuição de trabalho.
- Estado 3W: Completo.

#### Conversation

- Fatos confirmados: o gerente precisa consultar diligências atrasadas para decidir a redistribuição de trabalho.
- Decisões comportamentais confirmadas: nenhuma além da necessidade e do valor expressos no Card.
- Proposta não aprovada: um desenvolvedor sugeriu dois endpoints; a proposta não integra o requisito.
- Perguntas bloqueadoras:
  - O que define uma diligência como atrasada? Impacto: impede identificar a população consultada. Responsável pela decisão: a identificar.
  - Quais filtros são necessários? Impacto: impede definir o comportamento da consulta. Responsável pela decisão: a identificar.
  - Qual resultado observável a consulta deve apresentar? Impacto: impede verificar a aceitação. Responsável pela decisão: a identificar.

#### Confirmation

- Regras confirmadas: nenhuma regra comportamental suficiente para formar exemplo legítimo.
- Exemplos de aceitação: nenhum bloco Gherkin.
- Dúvidas e hipóteses: a definição de atraso, os filtros e o resultado observável estão pendentes; os dois endpoints são somente proposta não aprovada.
- Estado da Confirmation: Ausente.

#### Estado 3C e prontidão

- Card: Estruturado
- Conversation: Em andamento
- Confirmation: Ausente
- Prontidão: Não pronta

#### Fatos e decisões preservados

- Fato: o ator é o gerente.
- Fato: a consulta deve apoiar a decisão de redistribuição de trabalho.
- Decisões pendentes: definição de atraso, filtros e resultados observáveis.
- Proposta: dois endpoints sugeridos por um desenvolvedor, sem aprovação como requisito.

### História C — Registrar contestação e preservar a justificativa

#### Card

- História: Como analista, quero registrar uma contestação de diligência, para preservar a justificativa.
- 3W:
  - Who — Confirmado: analista.
  - What — Confirmado: registrar uma contestação de diligência.
  - Why — Confirmado: preservar a justificativa.
- Estado 3W: Completo.

#### Conversation

- Fatos confirmados: o ator é o analista; a capacidade é registrar uma contestação de diligência; o valor é preservar a justificativa.
- Regra confirmada: a justificativa informada deve ser preservada no registro da contestação.
- Decisão pendente bloqueadora: qual resultado observável deve ser apresentado ao analista após o registro? Impacto: impede formar um exemplo de aceitação completo. Responsável pela decisão: a identificar.

#### Confirmation

- Regra confirmada: a justificativa informada deve ser preservada no registro da contestação.
- Exemplos de aceitação: nenhum bloco Gherkin completo, pois o resultado observável após o registro não foi decidido.
- Dúvidas e hipóteses: permanece pendente o resultado observável que deve ser apresentado ao analista.
- Estado da Confirmation: Parcial.

#### Estado 3C e prontidão

- Card: Estruturado
- Conversation: Em andamento
- Confirmation: Parcial
- Prontidão: Não pronta

#### Fatos e decisões preservados

- Fatos confirmados: analista, registro da contestação e valor de preservar a justificativa.
- Regra confirmada na Conversation: a justificativa informada deve ser preservada no registro da contestação.
- Decisão pendente: resultado observável apresentado ao analista após o registro.

## 3. Backlog Markdown que transcreve os estados

O mesmo conteúdo foi salvo separadamente em `task-5-fresh-backlog.md`.

```markdown
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
```

## 4. Comparação item a item dos quatro estados

| História | Estado | Trecho no payload 3C | Trecho no backlog | Resultado |
|---|---|---|---|---|
| A — Reabertura | Card | `- Card: Estruturado` | `- Card: Estruturado` | Idêntico |
| A — Reabertura | Conversation | `- Conversation: Suficiente para o escopo` | `- Conversation: Suficiente para o escopo` | Idêntico |
| A — Reabertura | Confirmation | `- Confirmation: Completa` | `- Confirmation: Completa` | Idêntico |
| A — Reabertura | Prontidão | `- Prontidão: Pronta` | `- Prontidão: Pronta` | Idêntico |
| B — Consulta gerencial | Card | `- Card: Estruturado` | `- Card: Estruturado` | Idêntico |
| B — Consulta gerencial | Conversation | `- Conversation: Em andamento` | `- Conversation: Em andamento` | Idêntico |
| B — Consulta gerencial | Confirmation | `- Confirmation: Ausente` | `- Confirmation: Ausente` | Idêntico |
| B — Consulta gerencial | Prontidão | `- Prontidão: Não pronta` | `- Prontidão: Não pronta` | Idêntico |
| C — Contestação | Card | `- Card: Estruturado` | `- Card: Estruturado` | Idêntico |
| C — Contestação | Conversation | `- Conversation: Em andamento` | `- Conversation: Em andamento` | Idêntico |
| C — Contestação | Confirmation | `- Confirmation: Parcial` | `- Confirmation: Parcial` | Idêntico |
| C — Contestação | Prontidão | `- Prontidão: Não pronta` | `- Prontidão: Não pronta` | Idêntico |

Verificação adicional da transcrição:

- Na história B, o payload diz `Exemplos de aceitação: nenhum bloco Gherkin.`; no backlog, entre `##### Acceptance Criteria` e `##### Refinement Status` há somente espaço em branco.
- Na história C, o payload diz `Exemplos de aceitação: nenhum bloco Gherkin completo`; no backlog, entre `##### Acceptance Criteria` e `##### Refinement Status` há somente espaço em branco.
- Auditoria aparece como `Proposta não confirmada` na Conversation e como `Proposta não confirmada` em Itens não cobertos; não existe item nem regra de auditoria.
- Endpoints aparecem como `Proposta não aprovada` na Conversation e como `Proposta não aprovada` em Itens não cobertos; não existe item nem regra de endpoint.

## 5. Validação estrutural do backlog

Comando executado a partir de `/Users/pedroct/skills/generating-azure-boards-backlog-from-spec`:

```console
$ uv run python scripts/validate_backlog.py /Users/pedroct/skills/.superpowers/sdd/2026-09-10-azure-boards-backlog-skill/task-5-fresh-backlog.md
Backlog structure is valid
```

Exit code: `0`.
