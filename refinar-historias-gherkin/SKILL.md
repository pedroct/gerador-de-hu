---
name: refinar-historias-gherkin
description: Use quando histórias, critérios de aceitação, regras de negócio, exemplos BDD ou cenários Gherkin precisam ser refinados, revisados ou divididos antes do desenvolvimento.
---

# Refinar histórias com Gherkin

## Objetivo

Transformar requisitos ainda imprecisos em entendimento compartilhado e exemplos verificáveis. Gherkin ilustra regras de negócio; não substitui descoberta, decisões do produto nem perguntas em aberto.

## Entrada e limite da skill

Consuma a história ou Card, os fatos e as decisões registradas na Conversation, incluindo as regras decididas. Aponte lacunas sem chamar outra skill. Se o ator, o valor ou uma regra necessária estiver ausente, reporte a lacuna.

Evidência Brownfield pode ser recebida como contexto rotulado do estado atual. Ela pode revelar lacunas ou divergências a discutir, mas não transforma código em confirmação. Escreva Gherkin somente com comportamento desejado confirmado pela Conversation; caminho, teste, símbolo e comportamento existente não criam regra nem completam decisão pendente.

Esta é uma skill-folha. Retorne regras confirmadas, exemplos e estado da Confirmation (`Ausente`, `Parcial` ou `Completa`). Não emita prontidão geral. Sob a 3C, aceite como confirmadas somente decisões da Conversation.

## Fluxo de refinamento

1. **Preserve a evidência.** Separe fatos confirmados, dúvidas e hipóteses. Nunca converta uma solução plausível em regra confirmada. Se não puder perguntar, mantenha a lacuna explícita.
2. **Extraia regras e exemplos.** Nomeie cada regra de negócio e cubra-a com exemplos concretos. Inclua fluxo principal, alternativas, limites e falhas somente quando sustentados pelo requisito ou identificados como hipóteses a validar. Divida a Confirmation quando houver regras que não possam ser entendidas e testadas juntas.
3. **Escreva ou revise Gherkin.** Antes disso, leia [references/gherkin-practices.md](references/gherkin-practices.md). Use a linguagem do domínio, não detalhes de tela, API, banco de dados, classes ou automação, salvo quando a interface técnica for parte explícita do comportamento contratado.
4. **Avalie a Confirmation.** Rastreie cada exemplo até uma regra, liste decisões pendentes e classifique o estado como `Ausente`, `Parcial` ou `Completa`.

Se os exemplos ou o requisito associado incluírem mensagens, rótulos ou CTAs exibidos ao usuário,
indique `revisar-textos-requisitos` como revisão manual opcional. Copy não deve ser criada para
preencher uma lacuna de regra, e essa indicação não é uma chamada automática nem altera o estado da
Confirmation.

No Azure Boards, regras confirmadas e exemplos pertencem a `Acceptance Criteria`; hipóteses, perguntas e histórico permanecem em `Description`. Se nenhuma regra puder formar exemplo legítimo, mantenha `Acceptance Criteria` vazio.

Não inclua evidência de implementação nos artefatos desta skill. O chamador a mantém em `Implementation Evidence` ou em síntese rotulada na Description/Conversation, nunca no Gherkin nem em `Acceptance Criteria`.

## Contrato da entrega

Salvo se o usuário pedir outro formato, produza nesta ordem:

1. **Regras confirmadas** — sem misturar suposições.
2. **Exemplos de aceitação** — um bloco Gherkin completo, válido e legível, contendo apenas comportamentos confirmados. Cada `Regra` contém ao menos um cenário; cada cenário contém passos. Se não houver comportamento suficiente para formar um exemplo, declare isso em dúvidas, fora do bloco.
3. **Dúvidas e hipóteses** — incluindo impacto de cada lacuna.
4. **Estado da Confirmation** — `Ausente`, `Parcial` ou `Completa`, com justificativa objetiva.

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
- Confirmation declarada completa apesar de decisões que alteram comportamento observável.
