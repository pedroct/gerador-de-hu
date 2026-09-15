# Backlog para Azure Boards

## 1.0.0 [Epic] Corrigir diligências
### Description
Origem na spec: seção 2.

### 1.1.0 [Feature] Reabrir diligência
#### Parent
`1.0.0`
#### Description
Origem na spec: seção 2.1.

#### 1.1.1 [User Story] Reabrir dentro do prazo
##### Parent
`1.1.0`
##### Description
###### Card
História confirmada.
###### Conversation
Regra confirmada.
##### Acceptance Criteria
```gherkin
# language: pt
Funcionalidade: Reabrir diligência

  Cenário: Reabrir uma diligência dentro do prazo
    Dado que uma diligência pode ser reaberta dentro do prazo
    Quando o analista responsável a reabre com uma justificativa
    Então o status da diligência deve voltar para "Em análise"
```
##### Refinement Status
- Card: Estruturado
- Conversation: Suficiente para o escopo
- Confirmation: Completa
- Prontidão: Pronta
- Origem na spec: seção 2.1.1
