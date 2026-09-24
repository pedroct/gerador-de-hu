---
name: refinar-historias-3w
description: Use quando uma história ou demanda de produto tem ator vago, objetivo orientado à solução, benefício ausente, justificativa circular ou solicita explicitamente Who, What, Why ou a técnica 3W.
---

# Refinar histórias com 3W

## Objetivo

Use 3W para descobrir intenção, não apenas preencher `Como / quero / para`. Uma história só fica coerente quando identifica **quem** vive o problema, **o que** essa pessoa precisa alcançar e **por que** isso tem valor. O molde não substitui regras, exemplos nem conversas.

## Fluxo

1. **Preserve a evidência.** Separe informações confirmadas, hipóteses e dúvidas. Evidência Brownfield de código pode contextualizar o estado atual, mas não infira Who, What, Why ou valor a partir dela. Não invente persona, motivação, comportamento ou métrica para completar um W.
2. **Who — quem?** Identifique o ator ou beneficiário cujo comportamento, necessidade ou resultado orienta a história. Registre contexto que altere a necessidade. Se atores buscam resultados diferentes, registre a possível divisão nas perguntas priorizadas. Um papel genérico é suficiente apenas quando distingui-lo não mudaria a história.
3. **What — o quê?** Expresse a capacidade ou resultado pretendido, em linguagem do domínio e independente de implementação. Preserve canais, telas, APIs e componentes como restrições ou hipóteses separadas. Verifique se soluções alternativas ainda poderiam atender ao mesmo `What`.
4. **Why — por quê?** Expresse a mudança útil para o ator ou negócio: problema evitado, decisão habilitada ou resultado alcançado. O `Why` precisa explicar o valor do `What`, não repeti-lo com palavras como “para conseguir”, “para facilitar” ou “para ficar informado”. Registre evidência ou medida somente se fornecida.
5. **Aplique o gate 3W.** Classifique cada W como `Confirmado`, `Fraco` ou `Pendente`. `Who` genérico quando perfis podem divergir, `What` que apenas nomeia a solução e `Why` circular não passam no gate. Não os reutilize como se estivessem resolvidos.
6. **Declare o estado 3W.** Use `Completo` somente quando os três Ws passam no gate sem fatos inventados; caso contrário, use `Incompleto` e apresente as perguntas de maior impacto. Estado 3W não equivale, sozinho, à prontidão para desenvolvimento.

Se, ao separar fatos, hipóteses e dúvidas, surgir um débito técnico explícito ou sustentado por
evidência, sinalize-o ao chamador como saída separada — incluindo categoria, evidência e impacto
observado. Não o transforme em requisito de negócio nem chame outra skill diretamente; a skill
orquestradora pode encaminhar esse sinal para `especificar-debitos-tecnicos`.

Se a história ou o requisito contiver texto que será exibido ao usuário, indique ao usuário a skill
`revisar-textos-requisitos` como revisão opcional de copy. Não a trate como requisito do 3W nem
como chamada automática.

## Contrato da entrega

Salvo formato solicitado pelo usuário, entregue:

1. **Mapa 3W** — tabela com `W`, status, formulação, evidência e lacunas.
2. **História proposta** — escreva `Como`, `quero` e `para` em três linhas separadas (quebra de linha explícita entre elas, não um único parágrafo), somente se os três Ws estiverem confirmados:

   ```text
   Como [Who],
   quero [What],
   para [Why].
   ```

   Caso contrário, entregue **Rascunho incompleto**, no mesmo formato de três linhas, e escreva `[a definir]` em cada cláusula fraca ou pendente.
3. **Perguntas priorizadas** — decisão necessária e impacto da resposta. Se houver atores, capacidades ou valores possivelmente independentes, registre aqui a hipótese de divisão a confirmar.
4. **Estado 3W** — `Completo` ou `Incompleto`, com justificativa objetiva.

Quando receber evidência Brownfield, cite-a apenas na coluna de evidência ou nas lacunas pertinentes, identificada como estado atual. Um caminho, símbolo, teste ou comportamento implementado não muda um W de `Fraco` ou `Pendente` para `Confirmado` sem fonte da spec ou decisão de negócio correspondente.

## Limite da skill

Esta é uma skill-folha. Entregue somente mapa 3W, história ou rascunho, perguntas e estado 3W. Não produza Conversation, Gherkin ou prontidão geral. Quando for invocada por outra skill, devolva esses artefatos ao chamador.

Para Azure Boards, o conteúdo 3W pertence a `Description`, nunca a `Acceptance Criteria`.

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

Rascunho incompleto:

```text
Como [perfil e contexto a definir],
quero [mudança sobre a qual precisa ser avisado],
para [decisão, ação ou risco a definir].
```

As lacunas impedem uma história completa. “Push”, “e-mail” ou “engajamento” também não viram requisitos sem confirmação.

## Julgamento assistido (opcional)

Para classificar muitas histórias de uma vez, ou para ter um sinal auditável ao lado do seu
julgamento, existe uma implementação do gate por modelo de decisão:

```bash
uv run python refinar-historias-3w/scripts/avaliar_gate_3w.py
```

Ela envia a história ao modelo Jev com os critérios desta skill e devolve `Confirmado`, `Fraco` ou
`Pendente` por W, cada um com distribuição de probabilidade e confiança. A regra do gate
— `Completo` só quando os três Ws passam — continua em código, não no modelo. Requer
`JEV_OPENROUTER_API` no `.env`.

Isto **não substitui** o fluxo acima: o script classifica, mas não separa fato de hipótese, não
formula as perguntas priorizadas e não escreve o mapa 3W. Use a confiança para saber onde olhar
primeiro, nunca como prontidão. Medição e limites em
[`references/spike-e-medicao.md`](references/spike-e-medicao.md).

Base conceitual: [Atlassian — User stories](https://www.atlassian.com/agile/project-management/user-stories), que descreve histórias como persona, necessidade e propósito e recomenda manter o objetivo livre de implementação.
