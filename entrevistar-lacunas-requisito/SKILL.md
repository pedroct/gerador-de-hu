---
name: entrevistar-lacunas-requisito
description: Use quando uma spec possui a seção aberta "Lacunas e perguntas abertas" e essas lacunas precisam ser fechadas por entrevista em rodadas, registrando adiamentos explícitos em vez de deixar decisões silenciosas. Aceita um escopo de audiência para separar o refinamento de negócio do técnico.
license: See NOTICE.md — adapts the round/frontier interview mechanism from mattpocock/skills (grilling), MIT licensed.
---

# Entrevistar lacunas de requisito

## Objetivo

Fechar, por entrevista com o usuário, a seção `## Lacunas e perguntas abertas` de uma spec já escrita —
tipicamente produzida por `redigir-spec-demanda-azure-boards` ou `redigir-spec-pedido-negocio` —
perguntando em rodadas até não sobrar nada em aberto ou até o usuário adiar explicitamente um item. O
mecanismo de rodada/fronteira usado aqui é adaptado, com atribuição MIT completa em
[NOTICE.md](NOTICE.md), da skill `grilling` do repositório
[`mattpocock/skills`](https://github.com/mattpocock/skills/tree/main/skills/productivity/grilling)
— o conteúdo abaixo foi reescrito para um escopo mais estreito, não traduzido literalmente.

## Escopo

Trabalhe só com o texto já escrito na spec fornecida. Não investigue código-fonte — essa investigação já
aconteceu antes, em `redigir-spec-pedido-negocio` — e não desenhe planos, features ou
arquitetura em aberto; isso continua sendo papel de `superpowers:brainstorming` neste repositório.

## Fluxo

1. **Leia a spec** e mapeie cada item de `## Lacunas e perguntas abertas` como um nó independente. Uma
   lacuna pode vir rotulada no formato `- **N3 · Negócio** — <pergunta>`, onde a letra do ID e o rótulo
   indicam a audiência. **Spec sem rótulos de audiência é o caso normal de specs antigas: pergunte
   todas as lacunas, exatamente como antes.** O escopo é um filtro opcional, nunca um requisito de
   formato.
2. **Calcule a fronteira**: os itens que já podem ser perguntados agora, sem depender da resposta de
   outro item ainda em aberto na mesma lista. Se o usuário informou um escopo (`negócio` ou `técnico`),
   ele **compõe com a fronteira** em vez de substituí-la: uma lacuna `Técnico` que depende de uma
   `Negócio` ainda aberta fica fora da fronteira mesmo na rodada técnica. Relate o que ficou bloqueado
   em vez de forçar uma resposta prematura. Na rodada de escopo `negócio`, o material de leitura do
   usuário é `negocio.md`; as decisões, porém, são sempre gravadas em `spec.md`. **Lacuna sem rótulo
   numa spec que tem outras rotuladas entra em toda rodada** e é relatada ao usuário como rótulo
   faltante; ela nunca é pulada por não casar com o escopo, sob pena de a decisão sumir nas duas
   rodadas.
3. **Pergunte a fronteira inteira em uma única rodada**, no formato:

   ```text
   ❓ **P1** - **<título da pergunta>**: <corpo da pergunta, pode trazer alternativas>

   ➡️ <resposta recomendada>

   ---

   ❓ **P2** - **<título da pergunta>**: <corpo da pergunta>

   ➡️ <resposta recomendada>
   ```

4. **Espere as respostas do usuário** antes de seguir. Cada resposta:
   - vira uma decisão registrada na seção apropriada da spec (`Comportamento esperado`,
     `Classificação`, etc.), com a lacuna correspondente removida de `## Lacunas e perguntas abertas`;
     ou
   - se o usuário adiar explicitamente, permanece registrada em `## Lacunas e perguntas abertas` como
     decisão consciente de adiamento — nunca apagada como se tivesse sido respondida; ou
   - se a resposta criar uma decisão que ainda não existia, **registrar uma lacuna nova** em
     `## Lacunas e perguntas abertas`, com ID e audiência próprios, citando a lacuna que a originou.
     Decidir *"a diligência deve expirar sozinha"* cria *"como a rotina de expiração é disparada"*, que
     é da outra rodada. Sem isso, decisões de negócio gerariam trabalho técnico invisível, descoberto
     só na implementação.
5. **Recalcule a fronteira** com o que foi decidido nesta rodada e repita a partir do passo 3.
6. **Pare** quando a fronteira ficar vazia — nada mais dependia de decisão do usuário — ou quando o
   usuário disser explicitamente para parar. Ao encerrar uma rodada de escopo `negócio`, **avise o
   usuário de que `negocio.md` ficou desatualizado**: as decisões foram para `spec.md`, e a projeção
   precisa ser regerada a partir dela antes da próxima rodada. Esta skill não regenera `negocio.md`
   nem chama quem o gera; o aviso é a entrega.

## Boundaries

- Skill-folha: nunca invoque nenhuma outra skill deste repositório.
- Não investigue código-fonte, não execute scripts, testes, builds, servidores, migrações nem a
  aplicação; trabalhe só com o texto da spec fornecida.
- Nunca preencha uma lacuna por plausibilidade; toda decisão vem do usuário, registrada com a resposta
  efetivamente dada — que pode divergir da resposta recomendada.
- Adiamento explícito do usuário é uma decisão válida e deve ser registrada como tal na spec, nunca
  tratado como falha da entrevista nem como lacuna esquecida.
- Não desenhe planos, features ou arquitetura em aberto; isso continua sendo papel de
  `superpowers:brainstorming`.
- Não reclassifique a audiência de uma lacuna existente para encaixá-la na rodada atual. Se o rótulo
  estiver errado, diga isso ao usuário e siga adiante sem perguntá-la.
