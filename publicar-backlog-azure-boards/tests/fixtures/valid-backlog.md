# Backlog para Azure Boards

## Metadados e cobertura
- Data de geração: `2026-09-10`
- Spec de origem: `docs/specs/spec-exemplo.md`

## 1.0.0 [Epic] Corrigir diligências

### Description
Objetivo, valor e escopo do épico.

Origem na spec: seção 2.

### 1.1.0 [Feature] Reabrir diligência

#### Parent
`1.0.0`

#### Description
Capacidade e limites da feature.

Origem na spec: seção 2.1.

#### 1.1.1 [User Story] Reabrir dentro do prazo

##### Parent
`1.1.0`

##### Description
###### Card
História confirmada.

###### Conversation
Regra confirmada.

Origem na spec: seção 2.1.1.

##### Implementation Evidence *(metadado de revisão — não é copiado para o Azure Boards; o campo Description termina no fim da Conversation acima)*
`src/diligencias.py:42` — comportamento atual.

##### Acceptance Criteria
```gherkin
# language: pt
Funcionalidade: Reabrir diligência

  Cenário: Reabrir uma diligência dentro do prazo
    Dado que uma diligência pode ser reaberta dentro do prazo
    Quando o analista responsável a reabre com uma justificativa
    Então o status da diligência deve voltar para "Em análise"
```
