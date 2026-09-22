# Task 1 — baseline comportamental sem a quarta skill

## Condições da execução

- Cenário executado somente com `refining-user-stories-with-3c`, `refining-user-stories-with-3w` e `refining-user-stories-with-gherkin`.
- Nenhuma skill de geração de backlog foi usada.
- Nenhuma pergunta foi feita e nenhuma regra foi acrescentada à spec.
- Nenhum work item foi criado ou alterado no Azure Boards.

## Backlog produzido no baseline

````markdown
# Backlog para Azure Boards

## 1.0.0 [Épico] Reduzir correções manuais de diligências

### Description

Reduzir correções manuais de diligências.

**Origem:** spec, “Objetivo A: reduzir correções manuais de diligências”.

### 1.1.0 [Feature] Reabrir diligências

#### Description

Permitir que o analista responsável reabra uma diligência conforme as regras confirmadas, sem incluir a proposta ainda não decidida de auditoria detalhada.

**Origem:** spec, regra confirmada de reabertura e sugestão de compliance associadas ao Objetivo A.

#### 1.1.1 [História] Reabrir uma diligência sob responsabilidade do analista

##### Azure Boards — Description

###### Card

| W | Status | Formulação | Evidência | Lacunas |
|---|---|---|---|---|
| Who | Confirmado | Analista responsável pela diligência | Regra confirmada na spec | Nenhuma para o Card |
| What | Confirmado | Reabrir a diligência em até 24 horas, com justificativa | Regra confirmada na spec | Nenhuma para o Card |
| Why | Confirmado | Reduzir correções manuais de diligências | Objetivo A da spec | Nenhuma para o Card |

**História:** Como analista responsável, quero reabrir uma diligência em até 24 horas, com justificativa, para reduzir correções manuais.

**Estado 3W:** Completo.

###### Conversation

**Contexto e regras confirmadas**

- O analista precisa ser o responsável pela diligência.
- A reabertura pode ocorrer em até 24 horas.
- A reabertura exige justificativa.
- Após a reabertura, o status volta para `Em análise`.

**Propostas não confirmadas**

- Auditoria detalhada — sugerida por compliance; seus campos ainda não foram decididos.

**Decisões pendentes**

- Pergunta: a proposta de auditoria detalhada fará parte do escopo e, se fizer, quais campos serão registrados?
  - Impacto: define eventual comportamento adicional de auditoria, mas não altera as regras de reabertura já confirmadas.
  - Decisor: a identificar.

##### Azure Boards — Acceptance Criteria

```gherkin
# language: pt
Funcionalidade: Reabrir uma diligência

  Regra: A reabertura confirmada devolve a diligência para análise

    Cenário: Analista responsável reabre a diligência dentro do prazo
      Dado que o analista é responsável pela diligência
      E que a diligência está dentro do prazo de reabertura de até 24 horas
      Quando o analista reabre a diligência com uma justificativa
      Então o status da diligência deve voltar para "Em análise"
```

##### Estado 3C e prontidão

- Card: Estruturado.
- Conversation: Suficiente para o escopo confirmado.
- Confirmation: Completa para as regras confirmadas desta história.
- Prontidão: Pronta para o escopo confirmado; a proposta de auditoria detalhada não foi promovida a requisito.

## 2.0.0 [Épico] Permitir consulta gerencial de diligências atrasadas

### Description

Permitir consulta gerencial de diligências atrasadas para apoiar decisões de redistribuição de trabalho.

**Origem:** spec, “Objetivo B: permitir consulta gerencial de diligências atrasadas”.

### 2.1.0 [Feature] Consultar diligências atrasadas

#### Description

Dar ao gerente uma capacidade de consulta voltada à decisão de redistribuição, mantendo em aberto a definição de atraso, filtros e resultados observáveis.

**Origem:** spec, necessidade gerencial e lacunas associadas ao Objetivo B.

#### 2.1.1 [História] Consultar diligências atrasadas para decidir redistribuição

##### Azure Boards — Description

###### Card

| W | Status | Formulação | Evidência | Lacunas |
|---|---|---|---|---|
| Who | Confirmado | Gerente | Necessidade explícita na spec | Nenhuma para o Card |
| What | Confirmado | Consultar diligências atrasadas | Objetivo B da spec | Definição de atraso, filtros e resultados observáveis pertencem à Conversation |
| Why | Confirmado | Decidir a redistribuição de trabalho | Necessidade explícita na spec | Nenhuma para o Card |

**História:** Como gerente, quero consultar diligências atrasadas para decidir a redistribuição de trabalho.

**Estado 3W:** Completo.

###### Conversation

**Contexto confirmado**

- O gerente precisa da consulta para decidir a redistribuição de trabalho.

**Propostas não confirmadas**

- Dois endpoints — sugestão de um desenvolvedor, não aprovada como requisito.

**Decisões pendentes**

- Pergunta: qual condição define uma diligência como atrasada?
  - Impacto: impede determinar o conjunto consultado e testar sua correção.
  - Decisor: a identificar.
- Pergunta: quais filtros precisam estar disponíveis?
  - Impacto: impede definir o comportamento observável da consulta.
  - Decisor: a identificar.
- Pergunta: quais resultados devem ser apresentados ao gerente?
  - Impacto: impede confirmar se a consulta sustenta a decisão de redistribuição.
  - Decisor: a identificar.

##### Azure Boards — Acceptance Criteria

**Ação no Azure Boards:** deixe o campo sem conteúdo.

##### Estado 3C e prontidão

- Card: Estruturado.
- Conversation: Pendente.
- Confirmation: Ausente.
- Prontidão: Não pronta; definição de atraso, filtros e resultados observáveis alteram implementação e teste.
````

## Avaliação sintoma por sintoma

| Sintoma | Ocorreu? | Evidência observada |
|---|---|---|
| Hierarquia achatada ou pai implícito | **Sim** | Os níveis aparecem aninhados e numerados, mas nenhuma Feature declara formalmente seu Épico pai e nenhuma História declara formalmente sua Feature pai. A relação existe apenas por posição e numeração. |
| Numeração duplicada ou inconsistente | Não | Foram emitidas chaves únicas e coerentes: `1.0.0` → `1.1.0` → `1.1.1` e `2.0.0` → `2.1.0` → `2.1.1`. |
| Endpoint promovido a requisito | Não | Os dois endpoints aparecem somente em `Propostas não confirmadas`, com fonte e estado explícitos. |
| Perda da origem na spec | Não | Épicos e Features citam o objetivo ou trecho correspondente; histórias mantêm evidência por W, regra e proposta. |
| História gerencial marcada pronta apesar das lacunas | Não | A história `2.1.1` está `Não pronta`, com Conversation pendente e Confirmation ausente. |
| Acceptance Criteria preenchido com hipóteses | Não | `1.1.1` contém apenas as regras declaradas confirmadas; `2.1.1` instrui deixar o campo vazio. |
| Description sem Card/Conversation | Não | Ambas as histórias contêm blocos separados de Card e Conversation. |
| Formato não reutilizável nos campos do Azure Boards | Não | Cada história separa explicitamente `Azure Boards — Description` de `Azure Boards — Acceptance Criteria`; o estado operacional fica fora desses campos. |

## Falha realmente observada e critério GREEN correspondente

### Falha observada: relação pai-filho apenas implícita

O Markdown comunica visualmente a hierarquia, mas não fornece uma referência de pai verificável. Reordenação, extração parcial ou transformação do documento pode perder ou interpretar incorretamente a relação.

**Critério GREEN:** cada Feature deve declarar exatamente um `Parent` com a chave documental do Épico pai, e cada História deve declarar exatamente um `Parent` com a chave documental da Feature pai. A referência deve corresponder ao prefixo hierárquico e apontar para um item existente no mesmo documento.

## Auto-revisão

- Comparei o documento efetivamente produzido com os oito sintomas, sem registrar como falha aquilo que não se manifestou.
- A decomposição preservou os dois objetivos em duas árvores independentes e usou numeração sequencial sem duplicação.
- A sugestão técnica dos endpoints e a sugestão de auditoria foram preservadas como propostas, não como requisitos ou critérios.
- O Gherkin da história `1.1.1` não define o marco inicial das 24 horas nem cria um comportamento para auditoria; apenas expressa a regra confirmada no nível permitido pela fonte.
- A história `2.1.1` permaneceu visível e rastreável, mas não pronta e sem conteúdo confirmatório.
- O único critério GREEN fixado responde à única falha observada: a ausência de referências explícitas de pai.
- Limitação metodológica: o cenário foi produzido em um contexto que também exigiu a leitura do design da futura skill. Para reduzir esse viés, o backlog foi montado apenas pelos contratos das três skills existentes e pelo prompt; a comparação com os sintomas foi feita sobre a saída já produzida.

---

## Fix round 1 — baseline válido em contexto cego

### Finding abordado

O baseline anterior foi produzido depois da leitura do design futuro e, portanto, não satisfazia a exigência de contexto realmente fresco. A mitigação descrita na auto-revisão anterior não elimina essa contaminação.

**Decisão de validade:** o bloco anterior “Backlog produzido no baseline”, sua avaliação e suas conclusões ficam substituídos para fins de baseline. O único baseline comportamental válido desta tarefa passa a ser a saída cega preservada integralmente em:

`/Users/pedroct/skills/.superpowers/sdd/2026-09-10-azure-boards-backlog-skill/task-1-blind-output.md`

### Origem cega da saída

- A saída foi produzida por um agente separado em contexto isolado.
- Esse agente recebeu somente o prompt literal do cenário e as três skills existentes, com as referências requeridas por elas.
- O agente cego não recebeu o design da quarta skill nem a lista dos oito sintomas usada nesta avaliação.
- Esta avaliação ocorreu depois da produção e sobre o arquivo verbatim, sem editar seu conteúdo.
- Identidade do arquivo avaliado: 156 linhas; SHA-256 `ca1eda27a899c44c50845ea27b3e9db73e437644b785160f823f69b423006342`.

### Avaliação dos oito sintomas sobre o baseline cego

| Sintoma | Ocorreu? | Evidência no baseline válido |
|---|---|---|
| Hierarquia achatada ou pai implícito | **Sim** | Épicos, Features e Histórias usam títulos aninhados e chaves coerentes, mas não há nenhum campo ou referência `Parent`; o pai só pode ser inferido da posição e da numeração. |
| Numeração duplicada ou inconsistente | Não | As chaves são únicas e sequenciais dentro de cada pai: `1.0.0`, `1.1.0`, `1.1.1`, `1.1.2`, `2.0.0`, `2.1.0` e `2.1.1`. |
| Endpoint promovido a requisito | Não | Os dois endpoints aparecem somente como “Proposta não confirmada”; a saída diz expressamente que a sugestão não foi aprovada como requisito e não define a solução. |
| Perda da origem na spec | Não | Os mapas 3W possuem coluna `Evidência`, citam o Objetivo A, o Objetivo B, o ator, as regras confirmadas e a origem da sugestão de compliance; a proposta dos endpoints também mantém seu autor e estado. |
| História gerencial marcada pronta apesar das lacunas | Não | A história `2.1.1` está `Não pronta`, com Conversation pendente, Confirmation ausente e bloqueadores explícitos sobre atraso, filtros e resultados observáveis. |
| Acceptance Criteria preenchido com hipóteses | Não | `1.1.1` usa somente ator, prazo, justificativa, reabertura e retorno a `Em análise`, todos presentes na regra confirmada; `1.1.2` e `2.1.1` mandam deixar o campo sem conteúdo. |
| Description sem Card/Conversation | Não | As três histórias contêm Card/Mapa 3W e Conversation dentro de `Azure Boards — Description`. |
| Formato não reutilizável nos campos do Azure Boards | Não | Cada história separa `Azure Boards — Description` de `Azure Boards — Acceptance Criteria`, mantendo o estado 3C fora dos dois blocos copiáveis. |

### Falhas realmente observadas e critérios GREEN correspondentes

#### 1. Relação pai-filho apenas implícita

O baseline não fornece uma referência de pai verificável; a relação depende da ordem dos títulos e da interpretação das chaves.

**Critério GREEN:** cada Feature deve declarar exatamente um `Parent` com a chave documental de um Épico existente, e cada História deve declarar exatamente um `Parent` com a chave documental de uma Feature existente. A referência deve concordar com a numeração hierárquica.

#### 2. Sugestão não confirmada promovida a item de backlog

A auditoria detalhada foi apenas sugerida por compliance, mas o baseline criou `1.1.2 História — Auditoria detalhada da reabertura`. Marcar o item como incompleto e não pronto preserva a incerteza, porém sua inclusão na hierarquia ainda promove uma proposta sem confirmação a uma história candidata. Esta é uma falha adicional realmente observada; ela não altera a resposta “Não” do sintoma específico “endpoint promovido a requisito”, pois os endpoints não viraram item nem requisito.

**Critério GREEN:** conteúdo explicitamente identificado como sugestão ou proposta não confirmada, sem evidência suficiente de demanda, não deve gerar Épico, Feature ou História. Deve permanecer em lacunas, itens não cobertos ou Conversation de um item rastreável, com sua origem e estado preservados.

### Comando e verificação realizada

Leitura integral e inspeção dirigida do arquivo verbatim:

```text
wc -l task-1-blind-output.md
sed -n '1,320p' task-1-blind-output.md
shasum -a 256 task-1-blind-output.md
rg -n '^## |^### |^#### |^##### |Parent|endpoint|Prontidão|Acceptance Criteria|Card|Conversation|Origem|Evidência' task-1-blind-output.md
```

A comparação foi feita item a item contra os oito sintomas literais do brief e, em separado, contra a regra de decomposição aplicável à proposta de auditoria.

### Resultado do Fix round 1

- Baseline válido: `task-1-blind-output.md`, sem conhecimento do design futuro durante a geração.
- Oito sintomas avaliados: um ocorreu e sete não ocorreram.
- Falhas realmente observadas: pai implícito e criação de história para sugestão não confirmada.
- Critérios GREEN fixados somente para essas duas falhas.
- Nenhum arquivo de produto ou skill foi alterado.
- Nenhum commit foi criado.
