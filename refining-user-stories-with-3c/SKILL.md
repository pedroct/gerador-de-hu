---
name: refining-user-stories-with-3c
description: Use when refining user stories through Card, Conversation, and Confirmation, especially when preparing Azure Boards Description and Acceptance Criteria or when a card is being treated as a complete requirement.
---

# Refining User Stories With 3C

## Objetivo

Trate a história como três aspectos complementares: o **Card** identifica e ancora a necessidade; a **Conversation** constrói entendimento compartilhado; a **Confirmation** registra exemplos que demonstram o comportamento acordado. Um cartão detalhado não substitui conversa, e critérios escritos sem acordo não constituem confirmação.

## Fluxo

1. **Preserve a evidência.** Mantenha separados fatos confirmados, propostas, hipóteses e decisões pendentes. Uma sugestão em chat, documento ou reunião não vira regra até ser aceita por quem tem autoridade sobre a decisão.
2. **Card — cartão.** **REQUIRED SUB-SKILL:** use refining-user-stories-with-3w. O cartão é um lembrete conciso e negociável, não uma especificação. Registre história ou rascunho, contexto essencial e estado 3W.
3. **Conversation — conversa.** Conduza ou prepare a troca necessária entre negócio, produto, desenvolvimento e outros decisores relevantes. Para cada lacuna, registre pergunta, impacto, responsável pela decisão e resposta quando obtida. Menção, participação ou ausência de conversa com alguém não prova autoridade decisória nem cria uma decisão atribuída à pessoa; sem atribuição explícita, use `a identificar`. Sintetize exemplos discutidos e decisões; não fabrique consenso quando a conversa não ocorreu.
4. **Confirmation — confirmação.** **REQUIRED SUB-SKILL:** refining-user-stories-with-gherkin. Encaminhe à Gherkin a história ou Card, os fatos e as decisões registradas na Conversation, incluindo as regras decididas. Confirmação exige critérios utilizáveis como base de testes de aceitação; repetir o cartão ou listar intenções não basta.
5. **Avalie os gates.** Classifique `Card` como `Estruturado` ou `Incompleto`; `Conversation` como `Pendente`, `Em andamento` ou `Suficiente para o escopo`; `Confirmation` como `Ausente`, `Parcial` ou `Completa`. A história está `Pronta` apenas com Card estruturado, conversa suficiente e confirmação completa, sem decisão bloqueadora.

A 3C é a única dona da prontidão geral. Estados locais da 3W e Gherkin são insumos; não os trate como vereditos concorrentes: a única prontidão geral é a consolidada pela 3C.

## Azure Boards

Antes de formatar a entrega, leia [references/azure-boards-fields.md](references/azure-boards-fields.md).

- `Description` recebe Card e síntese viva da Conversation: 3W, contexto, regras e decisões confirmadas, propostas não confirmadas e perguntas ou bloqueadores pendentes.
- `Acceptance Criteria` recebe exclusivamente os blocos Gherkin completos da Confirmation, e somente quando `Confirmation: Completa`.
- Com `Confirmation: Ausente` ou `Confirmation: Parcial`, indique fora do conteúdo copiável que `Acceptance Criteria` deve permanecer vazio; mantenha regras, lacunas e bloqueadores em `Description`, dentro da Conversation.
- Produzir conteúdo para os campos não autoriza criar ou alterar work items no Azure Boards.

## Contrato da entrega

Entregue blocos separados e prontos para copiar:

1. **Azure Boards — Description**
2. **Azure Boards — Acceptance Criteria** contendo somente blocos Gherkin da Confirmation quando ela estiver `Completa`; com `Ausente` ou `Parcial`, renderize exatamente `**Ação no Azure Boards:** deixe o campo sem conteúdo.` Não abra bloco de código nem use placeholder.
3. **Estado 3C e prontidão** — fora dos campos quando for informação operacional, salvo se o usuário pedir seu registro em `Description`

## Sinais de alerta

- Card transformado em especificação extensa.
- “Conversation” composta apenas por inferências da LLM.
- “O Product Owner não participou” convertido em “o Product Owner deve decidir”, sem autoridade informada.
- Proposta, hipótese ou pergunta pendente dentro de `Acceptance Criteria`.
- Gherkin criado para aparentar completude sem decisão de negócio.
- História marcada pronta porque os campos estão preenchidos.

Base conceitual: [Ron Jeffries — Card, Conversation, Confirmation](https://ronjeffries.com/xprog/articles/expcardconversationconfirmation/).
