---
name: interviewing-request-gaps
description: Use when a spec has an open "Lacunas e perguntas abertas" (gaps/open questions) section and those gaps need to be closed by interviewing the user round by round, asking only what is currently decidable and recording explicit deferrals as decisions instead of leaving silent gaps.
license: See NOTICE.md — adapts the round/frontier interview mechanism from mattpocock/skills (grilling), MIT licensed.
---

# Interviewing Request Gaps

## Objetivo

Fechar, por entrevista com o usuário, a seção `## Lacunas e perguntas abertas` de uma spec já escrita —
tipicamente produzida por `drafting-a-spec-from-business-request` — perguntando em rodadas até não
sobrar nada em aberto ou até o usuário adiar explicitamente um item. O mecanismo de rodada/fronteira
usado aqui é adaptado, com atribuição MIT completa em [NOTICE.md](NOTICE.md), da skill `grilling` do
repositório [`mattpocock/skills`](https://github.com/mattpocock/skills/tree/main/skills/productivity/grilling)
— o conteúdo abaixo foi reescrito para um escopo mais estreito, não traduzido literalmente.

## Escopo

Trabalhe só com o texto já escrito na spec fornecida. Não investigue código-fonte — essa investigação já
aconteceu antes, em `drafting-a-spec-from-business-request` — e não desenhe planos, features ou
arquitetura em aberto; isso continua sendo papel de `superpowers:brainstorming` neste repositório.

## Fluxo

1. **Leia a spec** e mapeie cada item de `## Lacunas e perguntas abertas` como um nó independente.
2. **Calcule a fronteira**: os itens que já podem ser perguntados agora, sem depender da resposta de
   outro item ainda em aberto na mesma lista.
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
     decisão consciente de adiamento — nunca apagada como se tivesse sido respondida.
5. **Recalcule a fronteira** com o que foi decidido nesta rodada e repita a partir do passo 3.
6. **Pare** quando a fronteira ficar vazia — nada mais dependia de decisão do usuário — ou quando o
   usuário disser explicitamente para parar.

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
