# Task 5 — verificação comportamental da quarta skill

## Status

`DONE`

A skill `generating-azure-boards-backlog-from-spec` foi exercitada nos três cenários, em sequência, apenas como transformação de texto. Nenhum arquivo de produto foi alterado, nenhum work item foi criado ou modificado, nenhum subagente foi despachado e nenhum commit foi criado.

## Método e oráculos

Foram lidos integralmente antes da execução:

- `generating-azure-boards-backlog-from-spec/SKILL.md`;
- `generating-azure-boards-backlog-from-spec/references/backlog-markdown-contract.md`;
- `refining-user-stories-with-3c/SKILL.md` e seu contrato de campos do Azure Boards;
- `refining-user-stories-with-3w/SKILL.md`;
- `refining-user-stories-with-gherkin/SKILL.md` e suas práticas Gherkin;
- o prompt literal do cenário RED da Task 1.

Em cada história, a 3C foi aplicada primeiro, com 3W e Gherkin como sub-skills. O backlog consumiu Card, Conversation, Confirmation e os quatro estados devolvidos sem recalculá-los. A quarta skill foi usada somente para inventário, decomposição, pais, numeração, cobertura e renderização. As chaves abaixo são chaves documentais, não identificadores atribuídos pelo Azure Boards.

---

## Cenário 1 — reexecução da spec do cenário RED

### Entrada 1 — prompt literal da Task 1

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

Embora o prompt histórico diga para não usar uma skill de geração, nesta Task 5 a entrada foi deliberadamente reexecutada com a quarta skill, conforme o brief desta task. O texto da spec permaneceu literal e sem acréscimos.

### Saída 1 — backlog Markdown

<!-- BACKLOG-S1-START -->
````markdown
# Backlog para Azure Boards

## Metadados e cobertura
- Spec de origem: cenário RED literal da Task 1
- Escopo analisado: Objetivos A e B e todas as declarações associadas
- Itens não cobertos: Nenhum

## 1.0.0 [Epic] Reduzir correções manuais de diligências

### Description
O objetivo é reduzir correções manuais de diligências. O escopo reúne a capacidade confirmada de reabertura; a sugestão de auditoria permanece não confirmada na Conversation da história relacionada.

Origem na spec: Objetivo A e declarações imediatamente associadas

### 1.1.0 [Feature] Reabrir diligências de forma controlada

#### Parent
`1.0.0`

#### Description
Permitir a reabertura de uma diligência pelo analista responsável conforme as regras confirmadas, sem promover a sugestão de auditoria a requisito.

Origem na spec: regra confirmada de reabertura sob o Objetivo A

#### 1.1.1 [User Story] Reabrir uma diligência sob responsabilidade do analista

##### Parent
`1.1.0`

##### Description

###### Card
**História:** Como analista responsável pela diligência, quero reabri-la em até 24 horas, com justificativa, para reduzir correções manuais.

**Estado 3W:** Completo — Who, What e Why estão confirmados na spec.

###### Conversation
**Contexto e regras confirmadas**

- O analista precisa ser o responsável pela diligência.
- A reabertura pode ocorrer em até 24 horas.
- A reabertura exige justificativa.
- Após a reabertura, o status volta para `Em análise`.

**Propostas não confirmadas**

- Auditoria detalhada — sugestão de compliance; seus campos ainda não foram decididos.

**Decisões pendentes**

- Pergunta: a auditoria detalhada integrará o escopo e, se integrar, quais campos conterá?
  - Impacto: define comportamento adicional de auditoria, sem alterar as regras de reabertura já confirmadas.
  - Decisor: a identificar.

##### Acceptance Criteria

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

##### Refinement Status
- Card: Estruturado
- Conversation: Suficiente para o escopo
- Confirmation: Completa
- Prontidão: Pronta
- Origem na spec: regra confirmada de reabertura e Objetivo A

## 2.0.0 [Epic] Permitir consulta gerencial de diligências atrasadas

### Description
O objetivo é permitir consulta gerencial de diligências atrasadas para apoiar a decisão sobre redistribuição de trabalho. Definição de atraso, filtros e resultados observáveis continuam fora do comportamento confirmado.

Origem na spec: Objetivo B e declarações imediatamente associadas

### 2.1.0 [Feature] Consultar diligências atrasadas

#### Parent
`2.0.0`

#### Description
Oferecer ao gerente uma capacidade de consulta ligada à decisão de redistribuição, mantendo explícitas as lacunas de comportamento e a proposta técnica não aprovada.

Origem na spec: necessidade gerencial sob o Objetivo B

#### 2.1.1 [User Story] Consultar diligências atrasadas para decidir redistribuição

##### Parent
`2.1.0`

##### Description

###### Card
**História:** Como gerente, quero consultar diligências atrasadas, para decidir a redistribuição de trabalho.

**Estado 3W:** Completo — Who, What e Why estão confirmados, embora as regras observáveis permaneçam pendentes.

###### Conversation
**Contexto confirmado**

- O gerente precisa da consulta para decidir a redistribuição de trabalho.

**Propostas não confirmadas**

- Dois endpoints — sugestão de um desenvolvedor; não foram aprovados como requisito e não definem a solução da história.

**Decisões pendentes**

- Pergunta: qual condição define uma diligência como atrasada?
  - Impacto: impede determinar o conjunto consultado e testar sua correção.
  - Decisor: a identificar.
- Pergunta: quais filtros precisam estar disponíveis?
  - Impacto: impede definir esse comportamento da consulta.
  - Decisor: a identificar.
- Pergunta: quais resultados devem ser observáveis pelo gerente?
  - Impacto: impede confirmar que a consulta sustenta a decisão de redistribuição.
  - Decisor: a identificar.

##### Acceptance Criteria

##### Refinement Status
- Card: Estruturado
- Conversation: Pendente
- Confirmation: Ausente
- Prontidão: Não pronta
- Origem na spec: necessidade gerencial e lacunas declaradas sob o Objetivo B
````
<!-- BACKLOG-S1-END -->

### Verificação das expectativas do cenário 1

| Expectativa | Resultado | Evidência |
|---|---|---|
| Pelo menos dois Épicos quando os objetivos não compartilham pai justificável | PASS | `1.0.0` cobre o Objetivo A e `2.0.0` cobre o Objetivo B; a spec não fornece uma iniciativa comum que justifique fundi-los. |
| Cada Feature e história com Parent explícito | PASS | `1.1.0 → 1.0.0`, `1.1.1 → 1.1.0`, `2.1.0 → 2.0.0`, `2.1.1 → 2.1.0`. |
| Origem na spec em cada história | PASS | `Refinement Status` de `1.1.1` e `2.1.1` contém `Origem na spec`. |
| Endpoint somente em propostas da Conversation | PASS | A única menção a endpoints no backlog está em `Propostas não confirmadas` de `2.1.1`; não virou item, regra ou critério. |
| História de reabertura com Confirmation baseada nas regras confirmadas | PASS | O Gherkin usa apenas responsabilidade, janela de até 24 horas, justificativa e retorno a `Em análise`. |
| História gerencial Não pronta e sem conteúdo em Acceptance Criteria | PASS | `2.1.1` tem `Prontidão: Não pronta`, `Confirmation: Ausente` e seção efetivamente vazia. |
| Estado 3C preservado, sem recálculo pela quarta skill | PASS | Os estados devolvidos pela 3C foram transcritos como valores únicos no `Refinement Status`; a geração apenas os transportou. |

---

## Cenário 2 — spec totalmente confirmada

### Entrada 2 — spec criada para o cenário

```text
Spec: Relatórios de despesas — versão confirmada para teste

Todas as declarações abaixo foram confirmadas e formam o escopo completo deste teste.

Objetivo 1: permitir que empregados e gestores processem relatórios de despesas sem troca de e-mails, reduzindo coordenação manual.

Capacidade 1 — Preparar relatório de despesas

História 1.1 — Criar rascunho
- Ator: empregado.
- Necessidade e valor: criar um rascunho para registrar o relatório e retomá-lo depois.
- Regra: o empregado cria o rascunho informando título e finalidade de negócio.
- Resultado observável: o relatório aparece na lista do empregado com o título, a finalidade e o estado Rascunho.

História 1.2 — Enviar relatório
- Ator: empregado proprietário do rascunho.
- Necessidade e valor: enviar o relatório para iniciar a revisão gerencial sem troca de e-mails.
- Regra: o rascunho só pode ser enviado quando tem título, finalidade de negócio e ao menos uma despesa.
- Resultado observável no envio aceito: o estado passa para Enviado e o relatório deixa de ser editável.
- Resultado observável se faltar qualquer pré-requisito: o envio não é registrado e o estado permanece Rascunho.

Capacidade 2 — Revisar relatório de despesas

História 2.1 — Consultar relatórios para revisão
- Ator: gestor.
- Necessidade e valor: consultar os relatórios sob sua responsabilidade para decidir cada revisão.
- Regra: a consulta apresenta somente relatórios atribuídos ao gestor e no estado Enviado.
- Resultado observável: cada resultado apresenta título, empregado e valor total.

História 2.2 — Decidir a revisão
- Ator: gestor ao qual o relatório foi atribuído.
- Necessidade e valor: aprovar ou rejeitar um relatório Enviado para concluir a revisão sem troca de e-mails.
- Regra: o gestor atribuído pode aprovar ou rejeitar o relatório Enviado.
- Regra: uma rejeição exige motivo; sem motivo, a rejeição não é registrada e o relatório permanece Enviado.
- Resultado observável na aprovação: o estado passa para Aprovado e o empregado vê a decisão.
- Resultado observável na rejeição com motivo: o estado passa para Rejeitado e o empregado vê a decisão e o motivo.
```

Não foram acrescentados prazo, notificação, perfil adicional, moeda, limite, prioridade, aprovação em níveis ou qualquer tratamento não declarado.

### Saída 2 — backlog Markdown

<!-- BACKLOG-S2-START -->
````markdown
# Backlog para Azure Boards

## Metadados e cobertura
- Spec de origem: Relatórios de despesas — versão confirmada para teste
- Escopo analisado: Objetivo 1, Capacidades 1 e 2 e quatro histórias confirmadas
- Itens não cobertos: Nenhum

## 1.0.0 [Epic] Processar relatórios de despesas sem troca de e-mails

### Description
Permitir que empregados e gestores processem relatórios de despesas sem troca de e-mails, reduzindo coordenação manual. O escopo compreende preparação e revisão dos relatórios.

Origem na spec: Objetivo 1

### 1.1.0 [Feature] Preparar relatório de despesas

#### Parent
`1.0.0`

#### Description
Permitir que o empregado crie e envie seu relatório, cobrindo as duas histórias confirmadas de preparação e seus limites declarados.

Origem na spec: Capacidade 1 — Preparar relatório de despesas

#### 1.1.1 [User Story] Criar rascunho de relatório

##### Parent
`1.1.0`

##### Description

###### Card
**História:** Como empregado, quero criar um rascunho de relatório de despesas, para registrar o relatório e retomá-lo depois.

**Estado 3W:** Completo — Who, What e Why foram confirmados.

###### Conversation
**Regras e resultados confirmados**

- O empregado cria o rascunho informando título e finalidade de negócio.
- O relatório aparece na lista do empregado com o título, a finalidade e o estado `Rascunho`.

**Decisões pendentes:** Nenhuma no escopo informado.

##### Acceptance Criteria

```gherkin
# language: pt
Funcionalidade: Criar rascunho de relatório de despesas

  Regra: O rascunho criado fica disponível para o empregado retomar

    Cenário: Criar um rascunho com título e finalidade
      Dado que um empregado informa o título "Visita ao cliente" e a finalidade "Reunião de renovação"
      Quando ele cria o rascunho do relatório de despesas
      Então o relatório deve aparecer na lista do empregado com o título "Visita ao cliente"
      E deve apresentar a finalidade "Reunião de renovação" e o estado "Rascunho"
```

##### Refinement Status
- Card: Estruturado
- Conversation: Suficiente para o escopo
- Confirmation: Completa
- Prontidão: Pronta
- Origem na spec: Capacidade 1, História 1.1 — Criar rascunho

#### 1.1.2 [User Story] Enviar relatório para revisão

##### Parent
`1.1.0`

##### Description

###### Card
**História:** Como empregado proprietário do rascunho, quero enviar o relatório, para iniciar a revisão gerencial sem troca de e-mails.

**Estado 3W:** Completo — Who, What e Why foram confirmados.

###### Conversation
**Regras e resultados confirmados**

- O rascunho só pode ser enviado quando tem título, finalidade de negócio e ao menos uma despesa.
- No envio aceito, o estado passa para `Enviado` e o relatório deixa de ser editável.
- Se faltar qualquer pré-requisito, o envio não é registrado e o estado permanece `Rascunho`.

**Decisões pendentes:** Nenhuma no escopo informado.

##### Acceptance Criteria

```gherkin
# language: pt
Funcionalidade: Enviar relatório de despesas

  Regra: Somente um rascunho com todos os pré-requisitos pode ser enviado

    Cenário: Enviar rascunho completo
      Dado que o empregado possui um rascunho com título, finalidade de negócio e ao menos uma despesa
      Quando o empregado envia o relatório
      Então o estado do relatório deve passar para "Enviado"
      E o relatório deve deixar de ser editável

    Esquema do Cenário: Recusar envio com pré-requisito ausente
      Dado que o rascunho do empregado não possui <pre-requisito>
      Quando o empregado tenta enviar o relatório
      Então o envio não deve ser registrado
      E o estado do relatório deve permanecer "Rascunho"

      Exemplos:
        | pre-requisito          |
        | título                 |
        | finalidade de negócio |
        | ao menos uma despesa   |
```

##### Refinement Status
- Card: Estruturado
- Conversation: Suficiente para o escopo
- Confirmation: Completa
- Prontidão: Pronta
- Origem na spec: Capacidade 1, História 1.2 — Enviar relatório

### 1.2.0 [Feature] Revisar relatório de despesas

#### Parent
`1.0.0`

#### Description
Permitir que o gestor consulte os relatórios sob sua responsabilidade e registre sua decisão, cobrindo as duas histórias confirmadas de revisão.

Origem na spec: Capacidade 2 — Revisar relatório de despesas

#### 1.2.1 [User Story] Consultar relatórios para revisão

##### Parent
`1.2.0`

##### Description

###### Card
**História:** Como gestor, quero consultar os relatórios sob minha responsabilidade, para decidir cada revisão.

**Estado 3W:** Completo — Who, What e Why foram confirmados.

###### Conversation
**Regras e resultados confirmados**

- A consulta apresenta somente relatórios atribuídos ao gestor e no estado `Enviado`.
- Cada resultado apresenta título, empregado e valor total.

**Decisões pendentes:** Nenhuma no escopo informado.

##### Acceptance Criteria

```gherkin
# language: pt
Funcionalidade: Consultar relatórios para revisão

  Regra: A consulta limita os resultados aos relatórios que o gestor deve revisar

    Cenário: Consultar relatórios atribuídos e enviados
      Dado que há um relatório Enviado atribuído ao gestor, um Rascunho atribuído ao gestor e um relatório Enviado atribuído a outro gestor
      Quando o gestor consulta os relatórios para revisão
      Então somente o relatório Enviado atribuído a ele deve ser apresentado
      E o resultado deve apresentar título, empregado e valor total
```

##### Refinement Status
- Card: Estruturado
- Conversation: Suficiente para o escopo
- Confirmation: Completa
- Prontidão: Pronta
- Origem na spec: Capacidade 2, História 2.1 — Consultar relatórios para revisão

#### 1.2.2 [User Story] Decidir a revisão de um relatório

##### Parent
`1.2.0`

##### Description

###### Card
**História:** Como gestor ao qual o relatório foi atribuído, quero aprovar ou rejeitar um relatório Enviado, para concluir a revisão sem troca de e-mails.

**Estado 3W:** Completo — Who, What e Why foram confirmados.

###### Conversation
**Regras e resultados confirmados**

- O gestor atribuído pode aprovar ou rejeitar o relatório Enviado.
- Uma rejeição exige motivo; sem motivo, ela não é registrada e o relatório permanece `Enviado`.
- Na aprovação, o estado passa para `Aprovado` e o empregado vê a decisão.
- Na rejeição com motivo, o estado passa para `Rejeitado` e o empregado vê a decisão e o motivo.

**Decisões pendentes:** Nenhuma no escopo informado.

##### Acceptance Criteria

```gherkin
# language: pt
Funcionalidade: Decidir a revisão de um relatório

  Regra: O gestor atribuído pode concluir a revisão de um relatório Enviado

    Cenário: Aprovar relatório
      Dado que um relatório no estado "Enviado" está atribuído ao gestor
      Quando o gestor aprova o relatório
      Então o estado do relatório deve passar para "Aprovado"
      E o empregado deve ver a decisão

    Cenário: Rejeitar relatório com motivo
      Dado que um relatório no estado "Enviado" está atribuído ao gestor
      Quando o gestor rejeita o relatório com o motivo "Comprovante ausente"
      Então o estado do relatório deve passar para "Rejeitado"
      E o empregado deve ver a decisão e o motivo "Comprovante ausente"

  Regra: Uma rejeição sem motivo não é registrada

    Cenário: Tentar rejeitar sem motivo
      Dado que um relatório no estado "Enviado" está atribuído ao gestor
      Quando o gestor tenta rejeitar o relatório sem informar motivo
      Então a rejeição não deve ser registrada
      E o estado do relatório deve permanecer "Enviado"
```

##### Refinement Status
- Card: Estruturado
- Conversation: Suficiente para o escopo
- Confirmation: Completa
- Prontidão: Pronta
- Origem na spec: Capacidade 2, História 2.2 — Decidir a revisão
````
<!-- BACKLOG-S2-END -->

### Verificação das expectativas do cenário 2

| Expectativa | Resultado | Evidência |
|---|---|---|
| Um objetivo gera a raiz `1.0.0` | PASS | Há exatamente um Epic, `1.0.0`. |
| Duas capacidades geram duas Features | PASS | `1.1.0` e `1.2.0`, ambas com `Parent: 1.0.0`. |
| Duas histórias confirmadas por Feature | PASS | `1.1.1`, `1.1.2` sob a primeira; `1.2.1`, `1.2.2` sob a segunda. |
| Numeração esperada | PASS | A saída contém exatamente `1.0.0`, `1.1.0`, `1.1.1`, `1.1.2`, `1.2.0`, `1.2.1`, `1.2.2`. |
| Gherkin somente nas histórias | PASS | Os quatro blocos Gherkin estão exclusivamente em `Acceptance Criteria` das User Stories; Epic e Features não contêm Gherkin. |
| Nenhuma regra fora da spec | PASS | Cada regra e resultado da Conversation e do Gherkin possui contraparte literal na entrada; valores como títulos e motivos são somente dados concretos de exemplo, não regras novas. |
| Estado 3C preservado | PASS | As quatro histórias receberam da 3C `Estruturado / Suficiente para o escopo / Completa / Pronta`, e esses valores foram somente transcritos. |

---

## Cenário 3 — atualização de backlog existente com lacuna

### Entrada 3 — backlog existente

O backlog abaixo já possuía as chaves publicadas `1.1.1` e `1.1.3`. A antiga `1.1.2` foi removida e sua chave está aposentada; ela não pode ser reutilizada.

<!-- BACKLOG-S3-INPUT-START -->
````markdown
# Backlog para Azure Boards

## Metadados e cobertura
- Spec de origem: Base de conhecimento operacional v1
- Escopo analisado: objetivo de reutilização e capacidade de administrar artigos
- Itens não cobertos: Nenhum

## 1.0.0 [Epic] Reutilizar soluções aprovadas em atendimentos

### Description
Permitir que a equipe de suporte reutilize soluções aprovadas para reduzir diagnósticos repetidos.

Origem na spec: Base de conhecimento operacional v1, Objetivo 1

### 1.1.0 [Feature] Administrar artigos de solução

#### Parent
`1.0.0`

#### Description
Permitir o registro e a publicação de artigos que documentam soluções reutilizáveis pela equipe de suporte.

Origem na spec: Base de conhecimento operacional v1, Capacidade 1

#### 1.1.1 [User Story] Salvar rascunho de artigo

##### Parent
`1.1.0`

##### Description

###### Card
**História:** Como analista de suporte, quero salvar um artigo como rascunho, para retomar sua preparação depois.

**Estado 3W:** Completo.

###### Conversation
**Regras confirmadas**

- O analista salva título e solução em um rascunho.
- O artigo aparece em seus rascunhos com estado `Rascunho`.

##### Acceptance Criteria

```gherkin
# language: pt
Funcionalidade: Salvar rascunho de artigo

  Regra: O rascunho salvo pode ser retomado pelo analista

    Cenário: Salvar artigo como rascunho
      Dado que o analista informou o título e a solução de um artigo
      Quando ele salva o artigo como rascunho
      Então o artigo deve aparecer em seus rascunhos com o estado "Rascunho"
```

##### Refinement Status
- Card: Estruturado
- Conversation: Suficiente para o escopo
- Confirmation: Completa
- Prontidão: Pronta
- Origem na spec: Base de conhecimento operacional v1, História 1.1

#### 1.1.3 [User Story] Publicar artigo de solução

##### Parent
`1.1.0`

##### Description

###### Card
**História:** Como editor da base de conhecimento, quero publicar um artigo em rascunho, para disponibilizar a solução à equipe de suporte.

**Estado 3W:** Completo.

###### Conversation
**Regras confirmadas**

- O editor publica um artigo em estado `Rascunho`.
- O estado passa para `Publicado` e o artigo fica visível aos analistas de suporte.

##### Acceptance Criteria

```gherkin
# language: pt
Funcionalidade: Publicar artigo de solução

  Regra: Um artigo publicado fica disponível à equipe de suporte

    Cenário: Publicar artigo em rascunho
      Dado que o editor possui um artigo no estado "Rascunho"
      Quando ele publica o artigo
      Então o estado do artigo deve passar para "Publicado"
      E o artigo deve ficar visível aos analistas de suporte
```

##### Refinement Status
- Card: Estruturado
- Conversation: Suficiente para o escopo
- Confirmation: Completa
- Prontidão: Pronta
- Origem na spec: Base de conhecimento operacional v1, História 1.3
````
<!-- BACKLOG-S3-INPUT-END -->

Pedido de atualização e spec da nova história:

```text
A chave 1.1.2 foi removida do backlog publicado e deve permanecer aposentada.
Acrescente à Feature 1.1.0 a demanda confirmada abaixo, preservando todas as chaves existentes.

- Ator: analista de suporte.
- Necessidade e valor: arquivar um artigo Publicado que não deve mais orientar atendimentos, para evitar o uso de uma solução retirada.
- Regra confirmada: o analista de suporte pode arquivar um artigo no estado Publicado.
- Resultado observável confirmado: o estado passa para Arquivado e o artigo deixa de aparecer na consulta de artigos publicados.
```

### Saída 3 — backlog atualizado

<!-- BACKLOG-S3-OUTPUT-START -->
````markdown
# Backlog para Azure Boards

## Metadados e cobertura
- Spec de origem: Base de conhecimento operacional v1 e pedido confirmado de arquivamento
- Escopo analisado: objetivo de reutilização, capacidade de administrar artigos e atualização de arquivamento
- Itens não cobertos: Nenhum

## 1.0.0 [Epic] Reutilizar soluções aprovadas em atendimentos

### Description
Permitir que a equipe de suporte reutilize soluções aprovadas para reduzir diagnósticos repetidos.

Origem na spec: Base de conhecimento operacional v1, Objetivo 1

### 1.1.0 [Feature] Administrar artigos de solução

#### Parent
`1.0.0`

#### Description
Permitir o registro, a publicação e o arquivamento de artigos que documentam soluções reutilizáveis pela equipe de suporte.

Origem na spec: Base de conhecimento operacional v1, Capacidade 1, e pedido confirmado de arquivamento

#### 1.1.1 [User Story] Salvar rascunho de artigo

##### Parent
`1.1.0`

##### Description

###### Card
**História:** Como analista de suporte, quero salvar um artigo como rascunho, para retomar sua preparação depois.

**Estado 3W:** Completo.

###### Conversation
**Regras confirmadas**

- O analista salva título e solução em um rascunho.
- O artigo aparece em seus rascunhos com estado `Rascunho`.

##### Acceptance Criteria

```gherkin
# language: pt
Funcionalidade: Salvar rascunho de artigo

  Regra: O rascunho salvo pode ser retomado pelo analista

    Cenário: Salvar artigo como rascunho
      Dado que o analista informou o título e a solução de um artigo
      Quando ele salva o artigo como rascunho
      Então o artigo deve aparecer em seus rascunhos com o estado "Rascunho"
```

##### Refinement Status
- Card: Estruturado
- Conversation: Suficiente para o escopo
- Confirmation: Completa
- Prontidão: Pronta
- Origem na spec: Base de conhecimento operacional v1, História 1.1

#### 1.1.3 [User Story] Publicar artigo de solução

##### Parent
`1.1.0`

##### Description

###### Card
**História:** Como editor da base de conhecimento, quero publicar um artigo em rascunho, para disponibilizar a solução à equipe de suporte.

**Estado 3W:** Completo.

###### Conversation
**Regras confirmadas**

- O editor publica um artigo em estado `Rascunho`.
- O estado passa para `Publicado` e o artigo fica visível aos analistas de suporte.

##### Acceptance Criteria

```gherkin
# language: pt
Funcionalidade: Publicar artigo de solução

  Regra: Um artigo publicado fica disponível à equipe de suporte

    Cenário: Publicar artigo em rascunho
      Dado que o editor possui um artigo no estado "Rascunho"
      Quando ele publica o artigo
      Então o estado do artigo deve passar para "Publicado"
      E o artigo deve ficar visível aos analistas de suporte
```

##### Refinement Status
- Card: Estruturado
- Conversation: Suficiente para o escopo
- Confirmation: Completa
- Prontidão: Pronta
- Origem na spec: Base de conhecimento operacional v1, História 1.3

#### 1.1.4 [User Story] Arquivar artigo retirado de uso

##### Parent
`1.1.0`

##### Description

###### Card
**História:** Como analista de suporte, quero arquivar um artigo Publicado que não deve mais orientar atendimentos, para evitar o uso de uma solução retirada.

**Estado 3W:** Completo — Who, What e Why foram confirmados no pedido de atualização.

###### Conversation
**Regras e resultados confirmados**

- O analista de suporte pode arquivar um artigo no estado `Publicado`.
- O estado passa para `Arquivado`.
- O artigo deixa de aparecer na consulta de artigos publicados.

**Decisões pendentes:** Nenhuma no escopo informado.

##### Acceptance Criteria

```gherkin
# language: pt
Funcionalidade: Arquivar artigo retirado de uso

  Regra: Um artigo arquivado deixa de orientar os atendimentos

    Cenário: Arquivar artigo publicado
      Dado que um artigo no estado "Publicado" não deve mais orientar atendimentos
      Quando o analista de suporte arquiva o artigo
      Então o estado do artigo deve passar para "Arquivado"
      E o artigo deve deixar de aparecer na consulta de artigos publicados
```

##### Refinement Status
- Card: Estruturado
- Conversation: Suficiente para o escopo
- Confirmation: Completa
- Prontidão: Pronta
- Origem na spec: pedido confirmado de arquivamento, todos os quatro tópicos
````
<!-- BACKLOG-S3-OUTPUT-END -->

### Verificação das expectativas do cenário 3

| Expectativa | Resultado | Evidência |
|---|---|---|
| Preservar chaves existentes | PASS | `1.1.1` e `1.1.3` permanecem com os mesmos títulos, pais e conteúdo. |
| Não reutilizar chave removida | PASS | `1.1.2` não aparece na saída. |
| Acrescentar ao final do pai | PASS | A nova história recebeu `1.1.4`, maior sequência já publicada sob `1.1.0` mais um. |
| Preservar a lacuna | PASS | A sequência de histórias é `1.1.1`, `1.1.3`, `1.1.4`; a lacuna em `1.1.2` permanece. |
| Usar modo de atualização | PASS | A validação estrutural foi executada com `--update`, que admite lacunas sem renumeração. |
| Não chamar chave de Azure ID | PASS | A entrada, saída e avaliação tratam `1.1.2` como chave documental aposentada. |

---

## Validação estrutural

Os backlogs das saídas 1 e 2 foram submetidos a `validate_backlog.py` no modo de documento novo. O backlog existente e a saída 3 foram submetidos com `--update`. O conteúdo foi extraído em memória/process substitution a partir dos marcadores deste relatório, sem manter artefatos adicionais.

Resultados esperados e observados após a execução final:

```text
Cenário 1: Backlog structure is valid
Cenário 2: Backlog structure is valid
Cenário 3 — entrada existente: Backlog structure is valid
Cenário 3 — saída atualizada: Backlog structure is valid
```

## Revisão manual final

| Verificação do brief | Cenário 1 | Cenário 2 | Cenário 3 | Conclusão |
|---|---|---|---|---|
| Nenhum requisito sem origem | PASS | PASS | PASS | Todo item possui `Origem na spec`; todas as regras das histórias apontam para declarações da entrada. |
| Nenhuma regra inventada | PASS | PASS | PASS | O comportamento confirmatório é uma reformulação direta das regras e resultados das entradas; dados concretos usados em exemplos não criam política nova. |
| Nenhum conteúdo de Conversation em Acceptance Criteria | PASS | PASS | PASS | Critérios contêm apenas blocos Gherkin copiados da Confirmation; a história sem Confirmation tem seção vazia. |
| Nenhum Gherkin em Epic ou Feature | PASS | PASS | PASS | Todos os blocos Gherkin estão sob User Stories. |
| Nenhuma chave chamada de Azure ID | PASS | PASS | PASS | A numeração é chamada de chave documental; nenhum ID real é alegado. |
| Nenhuma mutação externa sugerida como já executada | PASS | PASS | PASS | Os documentos são backlogs Markdown para revisão; não há afirmação de criação ou alteração no Azure Boards. |

### Rastreabilidade por cenário

- Cenário 1: Objetivo A → `1.0.0` → `1.1.0` → `1.1.1`; Objetivo B → `2.0.0` → `2.1.0` → `2.1.1`. Auditoria e endpoints permanecem com fonte e estado na Conversation, sem gerar itens ou critérios.
- Cenário 2: Objetivo 1 → `1.0.0`; Capacidade 1 → `1.1.0` → histórias 1.1 e 1.2; Capacidade 2 → `1.2.0` → histórias 2.1 e 2.2. Todas as declarações confirmadas estão representadas.
- Cenário 3: o objetivo e a Feature existentes permanecem; `1.1.1` e `1.1.3` são preservadas; o pedido confirmado de arquivamento gera somente `1.1.4`; a chave aposentada `1.1.2` não é reutilizada.

## Conclusão

Os três cenários satisfazem o brief e o contrato. Não surgiu falha nova que justificasse alterar uma instrução de produto. O resultado permanece `DONE`, sem concerns materiais.

---

## Fix round 1 — evidência adicional

### Finding abordado

A revisão não encontrou falha comportamental nova, mas identificou três lacunas de evidência no relatório original:

1. não havia um caso explícito de `Confirmation: Parcial` com Acceptance Criteria vazio;
2. não havia comparação pré/pós, campo a campo, dos estados emitidos pela 3C e transcritos pela quarta skill;
3. a fronteira de contexto fresco não estava documentada explicitamente.

Esta seção acrescenta as três evidências sem substituir nem editar os backlogs anteriores.

### Fronteira do agente fresco e entrada

O controller criou um agente novo, em contexto separado desta execução original, exclusivamente para produzir a evidência do fix. Esse agente entregou dois artefatos brutos, preservados sem edição nesta revisão:

- `task-5-fresh-evidence.md`: spec recebida, payload 3C anterior à geração, comparação e transcrição do comando de validação;
- `task-5-fresh-backlog.md`: backlog Markdown renderizado a partir daquele payload.

A entrada desse agente foi a spec registrada em `task-5-fresh-evidence.md:3-17`. Ela contém literalmente:

```text
- Objetivo A: reduzir correções manuais de diligências.
- O analista responsável pode reabrir uma diligência em até 24 horas, com justificativa; o status volta para Em análise; essas regras foram confirmadas.
- Auditoria detalhada foi sugerida por compliance, mas os campos ainda não foram decididos.
- Objetivo B: permitir consulta gerencial de diligências atrasadas.
- O gerente precisa decidir redistribuição de trabalho, mas atraso, filtros e resultados observáveis ainda não foram definidos.
- Um desenvolvedor sugeriu dois endpoints; isso não foi aprovado como requisito.
- Objetivo C: permitir que o analista registre uma contestação de diligência. O analista, o registro da contestação e o valor de preservar a justificativa foram confirmados; a Conversation confirmou que a contestação deve ser registrada. O evento que encerra a contestação e o resultado observável ainda não foram decididos.
```

Os Objetivos A e B preservam o cenário RED; o Objetivo C é a variação focal criada para produzir legitimamente `Confirmation: Parcial`: há uma decisão confirmada, mas faltam evento de encerramento e resultado observável. O agente fresco executou 3C antes da renderização e registrou separadamente o payload bruto e o backlog resultante.

### Comparação pré/pós dos estados 3C

Cada linha abaixo cita, de um lado, o payload bruto anterior à quarta skill em `task-5-fresh-evidence.md` e, do outro, o `Refinement Status` efetivamente renderizado em `task-5-fresh-backlog.md`.

| História | Estado | Payload 3C bruto | Backlog renderizado | Comparação |
|---|---|---|---|---|
| A — Reabertura | Card | `Estruturado` (`fresh-evidence:58`) | `Estruturado` (`fresh-backlog:68`) | Idêntico |
| A — Reabertura | Conversation | `Suficiente para o escopo` (`fresh-evidence:59`) | `Suficiente para o escopo` (`fresh-backlog:69`) | Idêntico |
| A — Reabertura | Confirmation | `Completa` (`fresh-evidence:60`) | `Completa` (`fresh-backlog:70`) | Idêntico |
| A — Reabertura | Prontidão | `Pronta` (`fresh-evidence:61`) | `Pronta` (`fresh-backlog:71`) | Idêntico |
| B — Consulta gerencial | Card | `Estruturado` (`fresh-evidence:100`) | `Estruturado` (`fresh-backlog:118`) | Idêntico |
| B — Consulta gerencial | Conversation | `Em andamento` (`fresh-evidence:101`) | `Em andamento` (`fresh-backlog:119`) | Idêntico |
| B — Consulta gerencial | Confirmation | `Ausente` (`fresh-evidence:102`) | `Ausente` (`fresh-backlog:120`) | Idêntico |
| B — Consulta gerencial | Prontidão | `Não pronta` (`fresh-evidence:103`) | `Não pronta` (`fresh-backlog:121`) | Idêntico |
| C — Contestação | Card | `Estruturado` (`fresh-evidence:140`) | `Estruturado` (`fresh-backlog:166`) | Idêntico |
| C — Contestação | Conversation | `Em andamento` (`fresh-evidence:141`) | `Em andamento` (`fresh-backlog:167`) | Idêntico |
| C — Contestação | Confirmation | `Parcial` (`fresh-evidence:142`) | `Parcial` (`fresh-backlog:168`) | Idêntico |
| C — Contestação | Prontidão | `Não pronta` (`fresh-evidence:143`) | `Não pronta` (`fresh-backlog:169`) | Idêntico |

Resultado: `12/12` valores são idênticos. A quarta skill não recalculou Card, Conversation, Confirmation nem Prontidão.

### Acceptance Criteria vazio com Confirmation Parcial

No payload 3C da história C, a regra de registrar a contestação está confirmada, mas o evento que encerra a contestação e o resultado observável continuam pendentes (`task-5-fresh-evidence.md:112-149`). A própria 3C devolveu:

```text
- Confirmation: Parcial
- Prontidão: Não pronta
```

O backlog transcreveu esses valores em `task-5-fresh-backlog.md:163-169` e manteve Acceptance Criteria efetivamente vazio. A visualização com `sed -n l`, na qual cada `$` marca o fim físico da linha, comprova que existe somente uma linha vazia entre os headings:

```console
$ sed -n '163,166l' /Users/pedroct/skills/.superpowers/sdd/2026-09-10-azure-boards-backlog-skill/task-5-fresh-backlog.md
##### Acceptance Criteria$
$
##### Refinement Status$
- Card: Estruturado$
```

Não há placeholder, comentário, narrativa de Conversation nem bloco Gherkin no campo.

### História gerencial com Confirmation Ausente

No payload 3C da história B, definição de atraso, filtros e resultado observável são perguntas bloqueadoras; nenhum exemplo legítimo foi produzido (`task-5-fresh-evidence.md:70-109`). A 3C devolveu:

```text
- Confirmation: Ausente
- Prontidão: Não pronta
```

O backlog transcreveu os estados em `task-5-fresh-backlog.md:115-121` e também deixou Acceptance Criteria efetivamente vazio:

```console
$ sed -n '115,118l' /Users/pedroct/skills/.superpowers/sdd/2026-09-10-azure-boards-backlog-skill/task-5-fresh-backlog.md
##### Acceptance Criteria$
$
##### Refinement Status$
- Card: Estruturado$
```

A proposta dos dois endpoints permanece na Conversation como não aprovada e não aparece nos critérios.

### Comando e saída exatos da validação fresca

O agente fresco executou a partir de `/Users/pedroct/skills/generating-azure-boards-backlog-from-spec` o comando registrado em `task-5-fresh-evidence.md:352-361`:

```console
$ uv run python scripts/validate_backlog.py /Users/pedroct/skills/.superpowers/sdd/2026-09-10-azure-boards-backlog-skill/task-5-fresh-backlog.md
Backlog structure is valid
```

Exit code registrado: `0`.

### Checklist final revisado

| Verificação | Resultado | Evidência adicionada |
|---|---|---|
| Execução com fronteira explícita de contexto fresco | PASS | Agente e dois artefatos separados identificados; entrada literal preservada acima. |
| Estados 3C preservados sem recálculo | PASS | Comparação direta de 12 valores entre payload bruto e backlog; `12/12` idênticos. |
| Confirmation Completa preservada | PASS | História A: `Completa / Pronta`, com Gherkin limitado às regras confirmadas. |
| Confirmation Ausente produz AC vazio | PASS | História B: `Ausente / Não pronta`; intervalo entre headings contém somente linha vazia. |
| Confirmation Parcial produz AC vazio | PASS | História C: `Parcial / Não pronta`; intervalo entre headings contém somente linha vazia. |
| Validação estrutural fresca | PASS | Comando literal acima, saída `Backlog structure is valid`, exit code `0`. |
| Ausência de mutação externa | PASS | Os artefatos são Markdown local; nenhum work item, ação de Git ou arquivo de produto foi alterado. |

### Conclusão revisada

As três lacunas eram de demonstração, não falhas da skill. Com a evidência fresca, ficam cobertos os três estados de Confirmation (`Completa`, `Ausente` e `Parcial`), os dois gates negativos com Acceptance Criteria vazio e a preservação pré/pós de todos os estados 3C. O checklist final permanece `PASS` e o status da Task 5 permanece `DONE`, agora sem lacunas de evidência conhecidas.
