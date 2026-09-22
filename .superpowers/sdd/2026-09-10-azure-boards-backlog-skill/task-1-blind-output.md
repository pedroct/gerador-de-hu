# Backlog — Diligências

## 1.0.0 Épico — Reduzir correções manuais de diligências

Objetivo: reduzir correções manuais de diligências.

### 1.1.0 Feature — Reabertura controlada de diligências

Permitir que diligências sejam reabertas conforme as regras de negócio confirmadas, mantendo separada a proposta ainda não confirmada de auditoria detalhada.

#### 1.1.1 História — Reabrir uma diligência

##### Azure Boards — Description

**Card — Mapa 3W**

| W | Status | Formulação | Evidência | Lacunas |
|---|---|---|---|---|
| Who | Confirmado | Analista responsável pela diligência | A spec identifica explicitamente esse ator. | Nenhuma para o ator. |
| What | Confirmado | Reabrir uma diligência em até 24 horas, com justificativa | Capacidade, prazo e exigência de justificativa foram confirmados. | Definir o evento a partir do qual as 24 horas são contadas. |
| Why | Confirmado | Reduzir correções manuais de diligências | Objetivo A da spec. | Não foi fornecida medida de resultado. |

**História proposta**

Como analista responsável pela diligência, quero reabri-la em até 24 horas, com justificativa, para reduzir correções manuais de diligências.

**Estado 3W:** Completo. Ator, capacidade e benefício estão confirmados; a referência inicial do prazo permanece como regra pendente.

**Conversation**

Decisões confirmadas:

- Somente o analista responsável pode reabrir a diligência.
- A reabertura pode ocorrer em até 24 horas.
- A reabertura exige justificativa.
- Após a reabertura, o status volta para `Em análise`.

Pergunta pendente:

- Qual evento inicia a contagem das 24 horas? Impacto: altera a implementação e os testes do limite temporal. Responsável pela decisão: a identificar.

##### Azure Boards — Acceptance Criteria

```gherkin
Regra: Reabertura da diligência pelo analista responsável

  Cenário: Reabrir uma diligência dentro do prazo com justificativa
    Dado que a diligência está dentro do período confirmado de até 24 horas para reabertura
    E que o analista solicitante é o responsável pela diligência
    Quando o analista solicita a reabertura com uma justificativa
    Então a diligência é reaberta
    E seu status volta para "Em análise"
```

##### Estado 3C e prontidão

- Card: Estruturado.
- Conversation: Em andamento.
- Confirmation: Parcial.
- Prontidão: Não pronta.
- Bloqueador: falta definir o evento que inicia a contagem das 24 horas, o que impede testar o limite temporal de forma completa.

#### 1.1.2 História — Auditoria detalhada da reabertura

##### Azure Boards — Description

**Card — Mapa 3W**

| W | Status | Formulação | Evidência | Lacunas |
|---|---|---|---|---|
| Who | Pendente | [a definir] | Compliance sugeriu auditoria detalhada, mas a spec não identifica o ator ou beneficiário. | Identificar quem precisa da auditoria e em qual contexto. |
| What | Fraco | [capacidade de auditoria detalhada a definir] | Há uma sugestão, ainda não confirmada. | Confirmar se a auditoria será requisito e quais informações devem compô-la. |
| Why | Pendente | [benefício ou risco tratado a definir] | Nenhum resultado esperado foi informado. | Definir qual decisão, obrigação ou risco justifica a auditoria. |

**Rascunho incompleto**

Como [ator ou beneficiário a definir], quero [capacidade de auditoria detalhada a definir], para [benefício ou risco tratado a definir].

**Estado 3W:** Incompleto. Os três Ws dependem de decisões não fornecidas.

**Conversation**

Proposta não confirmada:

- Compliance sugeriu auditoria detalhada.

Perguntas pendentes:

- A auditoria detalhada será um requisito? Impacto: determina se a história deve integrar o escopo. Responsável pela decisão: a identificar.
- Quem utilizará ou se beneficiará da auditoria? Impacto: define o ator e o contexto da necessidade. Responsável pela decisão: a identificar.
- Quais campos devem compor a auditoria? Impacto: define o comportamento observável e a possibilidade de teste. Responsável pela decisão: a identificar.
- Qual resultado ou risco justifica a auditoria? Impacto: define o valor da história. Responsável pela decisão: a identificar.

##### Azure Boards — Acceptance Criteria

**Ação no Azure Boards:** deixe o campo sem conteúdo.

##### Estado 3C e prontidão

- Card: Incompleto.
- Conversation: Pendente.
- Confirmation: Ausente.
- Prontidão: Não pronta.
- Bloqueadores: a sugestão ainda não foi confirmada; ator, capacidade, benefício, campos e comportamento observável permanecem indefinidos.

## 2.0.0 Épico — Permitir consulta gerencial de diligências atrasadas

Objetivo: permitir consulta gerencial de diligências atrasadas.

### 2.1.0 Feature — Consulta gerencial de atrasos

Dar suporte à decisão gerencial sobre redistribuição de trabalho, sem assumir definição de atraso, filtros, resultados ou solução técnica.

#### 2.1.1 História — Consultar diligências atrasadas

##### Azure Boards — Description

**Card — Mapa 3W**

| W | Status | Formulação | Evidência | Lacunas |
|---|---|---|---|---|
| Who | Confirmado | Gerente | A spec identifica o gerente como responsável pela decisão de redistribuição. | Nenhuma para o ator. |
| What | Confirmado | Consultar diligências atrasadas | Objetivo B da spec. | Definir o que caracteriza atraso, os filtros e os resultados observáveis da consulta. |
| Why | Confirmado | Decidir a redistribuição de trabalho | A spec informa explicitamente essa decisão. | Não foram definidos os dados necessários para sustentar a decisão. |

**História proposta**

Como gerente, quero consultar diligências atrasadas, para decidir a redistribuição de trabalho.

**Estado 3W:** Completo. Ator, capacidade e benefício estão confirmados; as regras que tornam a capacidade implementável e testável permanecem pendentes.

**Conversation**

Proposta não confirmada:

- Um desenvolvedor sugeriu dois endpoints. A sugestão não foi aprovada como requisito e não define a solução da história.

Perguntas pendentes:

- O que caracteriza uma diligência atrasada? Impacto: define quais diligências pertencem à consulta. Responsável pela decisão: a identificar.
- Quais filtros são necessários? Impacto: define como o gerente delimita a consulta. Responsável pela decisão: a identificar.
- Quais resultados observáveis a consulta deve apresentar? Impacto: define o que será entregue e testado. Responsável pela decisão: a identificar.
- Quais dados o gerente precisa para decidir a redistribuição? Impacto: conecta a consulta ao valor pretendido. Responsável pela decisão: a identificar.
- Há alguma interface técnica contratada como requisito? Impacto: determina se a proposta de endpoints impõe uma restrição válida. Responsável pela decisão: a identificar.

##### Azure Boards — Acceptance Criteria

**Ação no Azure Boards:** deixe o campo sem conteúdo.

##### Estado 3C e prontidão

- Card: Estruturado.
- Conversation: Pendente.
- Confirmation: Ausente.
- Prontidão: Não pronta.
- Bloqueadores: definição de atraso, filtros e resultados observáveis ainda não foram decididos; a proposta de dois endpoints não é requisito confirmado.
