# Design: skill de entrevista para fechar lacunas de uma spec

## Contexto

A skill `drafting-a-spec-from-business-request` (adicionada nesta mesma sessão) produz uma spec a
partir de um pedido informal de negócio, separando o que foi afirmado pelo pedido, evidenciado pelo
código e o que permanece como lacuna. Por desenho, ela nunca preenche lacuna por plausibilidade — só
documenta.

Isso é correto, mas deixa uma etapa manual: alguém precisa revisar a seção `## Lacunas e perguntas
abertas` e decidir, uma a uma, o que fazer com cada item. O usuário pediu uma skill que fizesse essa
etapa por entrevista — perguntando até não sobrar nada em aberto — e apontou a skill `grilling`, do
repositório [`mattpocock/skills`](https://github.com/mattpocock/skills) (MIT, Copyright (c) 2026 Matt
Pocock), como referência de qualidade para esse tipo de interação.

`grilling` original é genérica ("sharpen a plan or design"): mapeia decisões como uma árvore, calcula a
"fronteira" (perguntas já respondíveis, sem depender de outra ainda em aberto), pergunta a fronteira
inteira numa rodada com resposta recomendada, espera, recalcula e repete até a fronteira esvaziar. Ela
também delega a si mesma a busca de fatos, reservando ao usuário só decisões genuínas — princípio que,
no nosso caso, já é coberto por `drafting-a-spec-from-business-request` (a separação afirmado /
evidenciado / lacuna acontece antes, na investigação de código).

Este design cobre uma skill nova, `interviewing-request-gaps`, que adapta o mecanismo de rodada/fronteira
de `grilling` — traduzido e reescrito, não copiado literalmente — para um escopo mais estreito e
específico deste repositório: fechar a seção de lacunas de uma spec já escrita, não desenhar planos em
aberto (esse continua sendo o papel de `superpowers:brainstorming`, usado para desenhar as skills deste
próprio repositório).

## Objetivos

1. Criar a skill `interviewing-request-gaps`.
2. Entrevistar o usuário em rodadas até a seção de lacunas de uma spec ficar vazia ou até o usuário
   adiar explicitamente um item (o que também é uma decisão registrada, não uma lacuna esquecida).
3. Nunca inventar resposta por plausibilidade; toda decisão vem do usuário.
4. Referenciar essa skill de forma condicional em `drafting-a-spec-from-business-request`, sem quebrar
   o design de "predecessora isolada que nunca chama nada" já testado — quem instalar só a skill de
   drafting continua funcionando.
5. Dar a atribuição MIT correta ao trabalho original de Matt Pocock que inspirou o mecanismo.

## Fora de escopo

- Investigar código-fonte; a skill trabalha só com o que já está escrito na spec.
- Desenhar planos, features ou arquitetura em aberto — isso continua sendo papel de
  `superpowers:brainstorming` neste repositório.
- Buscar fatos automaticamente (diferente da `grilling` original) — não se aplica aqui porque a
  investigação de código já aconteceu antes, em `drafting-a-spec-from-business-request`.
- Tornar-se `REQUIRED SUB-SKILL` de `drafting-a-spec-from-business-request` — a referência é condicional
  ("se estiver instalada"), nunca obrigatória.
- Copiar o texto de `grilling` literalmente; o conteúdo é reescrito em português, adaptado ao escopo
  mais estreito.

## Fluxo

1. **Ler a spec** e mapear cada item de `## Lacunas e perguntas abertas` como um nó independente.
2. **Calcular a fronteira**: os itens que já podem ser perguntados agora, sem depender da resposta de
   outro item ainda em aberto na mesma lista.
3. **Perguntar a fronteira inteira em uma rodada**, no formato:

   ```text
   ❓ **P1** - **<título da pergunta>**: <corpo da pergunta, pode trazer alternativas>

   ➡️ <resposta recomendada>

   ---

   ❓ **P2** - **<título da pergunta>**: <corpo da pergunta>

   ➡️ <resposta recomendada>
   ```
4. **Esperar as respostas do usuário** antes de seguir. Cada resposta:
   - vira uma decisão registrada na seção apropriada da spec (`Comportamento esperado`,
     `Classificação`, etc.), com a lacuna correspondente removida; ou
   - se o usuário adiar explicitamente, permanece registrada como decisão consciente de adiamento, não
     como lacuna silenciosa.
5. **Recalcular a fronteira** com o que foi decidido nesta rodada e repetir a partir do passo 3.
6. **Parar** quando a fronteira ficar vazia (nada mais dependia de decisão do usuário) ou quando o
   usuário disser explicitamente para parar.

## Boundaries

- Skill-folha: nunca chama nenhuma outra skill.
- Não investiga código-fonte, não executa nada; trabalha só com o texto da spec fornecida.
- Nunca preenche lacuna por plausibilidade; toda decisão é do usuário, registrada com a resposta
  efetivamente dada (que pode divergir da recomendada).
- Adiamento explícito do usuário é uma decisão válida e deve ser registrada como tal, não tratado como
  falha da entrevista.

## Wiring com `drafting-a-spec-from-business-request`

Referência condicional, adicionada ao passo final do Fluxo dessa skill (já existente, não recriado
aqui): "se a skill `interviewing-request-gaps` estiver instalada, use-a para fechar o máximo possível
das lacunas antes de salvar o arquivo; caso não esteja, salve com as lacunas documentadas normalmente."
Sem `REQUIRED SUB-SKILL`, sem verbo de invocação que o teste de isolamento já existente rejeitaria — a
frase precisa ser condicional e verificável por um novo teste, não pelos testes de isolamento atuais
(que continuam proibindo invocação incondicional das quatro skills originais; esta quinta referência é
deliberadamente diferente e ganha sua própria asserção).

## Atribuição MIT

`interviewing-request-gaps` adapta o mecanismo de rodada/fronteira publicado em
`mattpocock/skills` (`skills/productivity/grilling`), licenciado MIT:

```
MIT License
Copyright (c) 2026 Matt Pocock
```

A skill inclui um `NOTICE.md` próprio com o texto integral da licença e a atribuição, apontando a
origem (`https://github.com/mattpocock/skills/tree/main/skills/productivity/grilling`) e deixando claro
que o conteúdo em português foi adaptado, não traduzido literalmente.

## Arquitetura de skills

```text
drafting-a-spec-from-business-request   (inalterada em sua essência; ganha 1 referência condicional)
        |
        | (arquivo de spec com lacunas)
        v
interviewing-request-gaps               (nova, folha, referenciada condicionalmente)
        |
        | (spec com lacunas fechadas, uso manual pelo usuário)
        v
generating-azure-boards-backlog-from-spec   (inalterada)
```

Nenhuma das quatro skills originais é tocada. `interviewing-request-gaps` não é chamada por, nem chama,
nenhuma delas.

## Arquivos previstos

```text
interviewing-request-gaps/
├── SKILL.md
├── agents/openai.yaml
└── NOTICE.md
```

Também modificados:
- `drafting-a-spec-from-business-request/SKILL.md`: uma frase condicional a mais no Fluxo.
- `drafting-a-spec-from-business-request/tests/test_skill_integration.py`: uma asserção nova para essa
  frase condicional.

## Estratégia de testes

1. Teste estático próprio de `interviewing-request-gaps`, no mesmo padrão das outras cinco skills:
   confirma que é skill-folha (não invoca nenhuma outra skill do repositório, incluindo as quatro
   originais e `drafting-a-spec-from-business-request`), e que o conteúdo cobre fronteira, rodada,
   resposta recomendada e o tratamento de adiamento explícito como decisão válida.
2. Teste estendido em `drafting-a-spec-from-business-request/tests/test_skill_integration.py`:
   confirma a frase condicional exata sobre `interviewing-request-gaps` e que ela não aparece como
   `REQUIRED SUB-SKILL`.
3. `quick_validate.py` sobre o novo diretório.
4. `uv run pytest -v` completo, sem regressão nas seis skills.

## Critérios de conclusão

- `interviewing-request-gaps` existe, com `SKILL.md`, `agents/openai.yaml` e `NOTICE.md` com a
  atribuição MIT completa.
- Nenhuma das quatro skills originais é alterada; `drafting-a-spec-from-business-request` só ganha a
  referência condicional descrita.
- O teste de isolamento de `interviewing-request-gaps` passa, confirmando que ela não chama nenhuma
  outra skill.
- O teste estendido de `drafting-a-spec-from-business-request` confirma a referência condicional, sem
  `REQUIRED SUB-SKILL`.
- `quick_validate.py` passa para o novo diretório.
- `uv run pytest -v` passa por completo, sem regressão.
