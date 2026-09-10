---
name: refining-user-stories-with-gherkin
description: Use when refining, reviewing, or splitting user stories, acceptance criteria, business rules, BDD examples, or Gherkin scenarios before development.
---

# Refining User Stories With Gherkin

## Objetivo

Transformar requisitos ainda imprecisos em entendimento compartilhado e exemplos verificáveis. Gherkin ilustra regras de negócio; não substitui descoberta, decisões do produto nem perguntas em aberto.

## Fluxo de refinamento

1. **Preserve a evidência.** Separe fatos confirmados, dúvidas e hipóteses. Nunca converta uma solução plausível em regra confirmada. Se não puder perguntar, mantenha a lacuna explícita e considere a história não pronta quando ela impedir implementação ou teste.
2. **Formule a história.** **REQUIRED SUB-SKILL:** use refining-user-stories-with-3w para estabelecer e validar ator, capacidade e benefício. Retorne então a este fluxo para extrair regras e exemplos. Se o gate 3W não passar, não promova cláusulas fracas a fatos; trabalhe somente com regras confirmadas que ainda possam formar exemplos significativos. Divida a história quando houver resultados independentes, fluxos com valor próprio ou regras que não possam ser entendidas e testadas juntas.
3. **Extraia regras e exemplos.** Nomeie cada regra de negócio e cubra-a com exemplos concretos. Inclua fluxo principal, alternativas, limites e falhas somente quando sustentados pelo requisito ou identificados como hipóteses a validar.
4. **Escreva ou revise Gherkin.** Antes disso, leia [references/gherkin-practices.md](references/gherkin-practices.md). Use a linguagem do domínio, não detalhes de tela, API, banco de dados, classes ou automação, salvo quando a interface técnica for parte explícita do comportamento contratado.
5. **Avalie a prontidão.** Rastreie cada exemplo até uma regra, liste decisões pendentes e dê um veredito binário: `Pronta` ou `Não pronta`. Se uma condição pendente alterar implementação ou teste, o veredito é `Não pronta`; nunca use “pronta com ressalvas” ou “pronta condicionada”.

Quando estiver sob refining-user-stories-with-3c, trate como confirmadas somente as decisões registradas pela Conversation. Devolva regras e exemplos completos como Confirmation. No Azure Boards, esse conteúdo pertence a `Acceptance Criteria`; hipóteses, perguntas e histórico permanecem em `Description`. Se nenhuma regra puder formar exemplo legítimo, mantenha `Acceptance Criteria` vazio.

## Contrato da entrega

Salvo se o usuário pedir outro formato, produza nesta ordem:

1. **História refinada** — ator, capacidade e benefício.
2. **Regras confirmadas** — sem misturar suposições.
3. **Exemplos de aceitação** — um bloco Gherkin completo, válido e legível, contendo apenas comportamentos confirmados. Cada `Regra` contém ao menos um cenário; cada cenário contém passos. Se não houver comportamento suficiente para formar um exemplo, declare isso em dúvidas, fora do bloco.
4. **Dúvidas e hipóteses** — incluindo impacto de cada lacuna.
5. **Prontidão** — veredito e bloqueadores.

## Critérios de qualidade

- Cada cenário ilustra um comportamento ou regra reconhecível.
- O evento e o resultado distinguem comportamento aceitável de inaceitável; um `Então` que apenas renomeia o `Quando` ou a capacidade desejada não constitui critério.
- `Dado` estabelece estado conhecido; `Quando` descreve o evento; `Então` descreve resultado observável por pessoa ou sistema externo.
- Prefira 3–5 passos por exemplo. Comprima detalhes incidentais em linguagem de domínio; não esconda regras relevantes.
- Use valores e resultados concretos. Termos como “adequado”, “rápido”, “válido” ou “correto” exigem definição verificável.
- Não invente limites, estados, mensagens, prazos, tentativas, prioridades, regras de recorrência ou tratamento de duplicidade.
- Um cenário não prova completude. Verifique cobertura por regra e explicite o que continua desconhecido.

## Sinais de alerta

- Critérios que verificam chamadas de API, tabelas, filas ou registros internos.
- Interações de interface em `Dado` ou resultados técnicos em `Então`.
- `Contexto` usado para esconder configuração longa ou regras diferentes.
- `Esquema do Cenário` usado em comportamentos diferentes apenas para reduzir texto.
- Blocos Gherkin parciais ou comentários usados no lugar de exemplos.
- História declarada pronta apesar de decisões que alteram comportamento observável.
