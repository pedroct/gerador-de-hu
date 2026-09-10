---
name: refining-user-stories-with-3w
description: Use when a user story or product demand has a vague actor, solution-led goal, missing benefit, circular rationale, or explicitly requests Who/What/Why or the 3W technique.
---

# Refining User Stories With 3W

## Objetivo

Use 3W para descobrir intenção, não apenas preencher `Como / quero / para`. Uma história só fica coerente quando identifica **quem** vive o problema, **o que** essa pessoa precisa alcançar e **por que** isso tem valor. O molde não substitui regras, exemplos nem conversas.

## Fluxo

1. **Preserve a evidência.** Separe informações confirmadas, hipóteses e dúvidas. Não invente persona, motivação, comportamento ou métrica para completar um W.
2. **Who — quem?** Identifique o ator ou beneficiário cujo comportamento, necessidade ou resultado orienta a história. Registre contexto que altere a necessidade. Se atores buscam resultados diferentes, proponha histórias separadas. Um papel genérico é suficiente apenas quando distingui-lo não mudaria a história.
3. **What — o quê?** Expresse a capacidade ou resultado pretendido, em linguagem do domínio e independente de implementação. Preserve canais, telas, APIs e componentes como restrições ou hipóteses separadas. Verifique se soluções alternativas ainda poderiam atender ao mesmo `What`.
4. **Why — por quê?** Expresse a mudança útil para o ator ou negócio: problema evitado, decisão habilitada ou resultado alcançado. O `Why` precisa explicar o valor do `What`, não repeti-lo com palavras como “para conseguir”, “para facilitar” ou “para ficar informado”. Registre evidência ou medida somente se fornecida.
5. **Aplique o gate 3W.** Classifique cada W como `Confirmado`, `Fraco` ou `Pendente`. `Who` genérico quando perfis podem divergir, `What` que apenas nomeia a solução e `Why` circular não passam no gate. Não os reutilize como se estivessem resolvidos.
6. **Declare o estado 3W.** Use `Completo` somente quando os três Ws passam no gate sem fatos inventados; caso contrário, use `Incompleto` e apresente as perguntas de maior impacto. Estado 3W não equivale, sozinho, à prontidão para desenvolvimento.

## Contrato da entrega

Salvo formato solicitado pelo usuário, entregue:

1. **Mapa 3W** — tabela com `W`, status, formulação, evidência e lacunas.
2. **História proposta** — use `Como [Who], quero [What], para [Why]` somente se os três Ws estiverem confirmados. Caso contrário, entregue **Rascunho incompleto** e escreva `[a definir]` em cada cláusula fraca ou pendente.
3. **Possíveis divisões** — somente quando houver atores, capacidades ou valores independentes.
4. **Perguntas priorizadas** — decisão necessária e impacto da resposta.
5. **Estado 3W** — `Completo` ou `Incompleto`, com justificativa objetiva. Se o pedido também avaliar regras e critérios, apresente separadamente a prontidão geral definida pela skill Gherkin.

Quando estiver sob refining-user-stories-with-3c, entregue o mapa, a história ou rascunho e o estado 3W como insumos do Card; devolva então o controle à 3C para a Conversation. Para Azure Boards, esses elementos pertencem a `Description`, nunca a `Acceptance Criteria`.

Fora do fluxo 3C, quando o pedido também incluir regras ou critérios de aceitação, conclua primeiro a análise 3W. Só passe adiante regras confirmadas que tenham evento e resultado observável suficientes para formar um exemplo significativo. Se não houver nenhuma, declare que critérios não podem ser escritos sem fabricar comportamento. Havendo regras elegíveis, **REQUIRED SUB-SKILL:** use refining-user-stories-with-gherkin sem reiniciar nem contradizer a análise.

## Referência rápida

| W | Deve responder | Sinal de fraqueza |
|---|---|---|
| Who | Quem tem a necessidade ou recebe o valor? | “usuário”, “área” ou “sistema” sem contexto relevante |
| What | Que capacidade ou resultado é desejado? | nome de tela, canal, API, componente ou tarefa técnica |
| Why | Que benefício ou problema justifica isso? | paráfrase do `What`, slogan ou vantagem não confirmada |

## Exemplo

Entrada: “Como usuário, quero notificações para ficar informado.”

- **Who — Fraco:** identificar quem precisa agir com a informação.
- **What — Fraco:** descobrir qual mudança exige atenção; eventos e canais continuam pendentes.
- **Why — Fraco:** esclarecer qual decisão, ação ou risco depende da informação.

Rascunho incompleto: `Como [perfil e contexto a definir], quero [mudança sobre a qual precisa ser avisado], para [decisão, ação ou risco a definir].`

Não há regra com evento e resultado confirmados; portanto, ainda não há Gherkin legítimo. “Push”, “e-mail” ou “engajamento” também não viram requisitos sem confirmação.

Base conceitual: [Atlassian — User stories](https://www.atlassian.com/agile/project-management/user-stories), que descreve histórias como persona, necessidade e propósito e recomenda manter o objetivo livre de implementação.
