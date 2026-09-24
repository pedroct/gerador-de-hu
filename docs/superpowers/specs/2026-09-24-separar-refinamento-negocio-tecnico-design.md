# Design: separar o refinamento de negócio do refinamento técnico

## Contexto

`redigir-spec-demanda-azure-boards` produz uma spec única, destinada a um leitor que não existe:
alguém que é simultaneamente Product Owner e desenvolvedor. Na prática o refinamento acontece em duas
reuniões, com pessoas diferentes, e o artefato não acompanha essa divisão.

O sintoma foi observado ao validar uma spec real, gerada para a Demanda "APERFEIÇOAR PRAZOS E STATUS
DE DILIGÊNCIAS E CONVITES" (240 linhas, 19 lacunas). A área de negócio não conseguiu validá-la, e
acionar `entrevistar-lacunas-requisito` sobre a seção `## Lacunas e perguntas abertas` piorou o
quadro: a entrevista perguntou tudo, inclusive decisões de persistência e migração de dados, numa
reunião de negócio.

### O diagnóstico não é "a spec é técnica demais"

Classificando as 19 lacunas daquela spec pelo critério da seção
[Critério de audiência](#critério-de-audiência), **6 são técnicas e 13 são decisões de negócio**.
A reunião não falhou porque as perguntas eram técnicas. Falhou porque **as perguntas de negócio foram
redigidas em vocabulário de código**.

Exemplo literal da spec:

> Há duas âncoras de prazo em uso simultâneo e elas não coincidem: a data exibida ao usuário parte da
> criação da diligência (`MinhaDiligenciaDTO.java:76-78`), enquanto a expiração efetiva parte da data
> do convite do executor (`DiligenciaService.java:269-270`).

A decisão por trás é inteiramente do PO — *a data que o usuário vê deve ser a mesma que faz a
diligência expirar?* — mas para chegar até ela é preciso ler Java.

O mesmo vale para o corpo do documento: `## Comportamento esperado`, a seção mais próxima do negócio,
abre com um parágrafo legível e no bullet seguinte apresenta oito citações `caminho:linha`.

A consequência para o desenho é direta: **rotular as lacunas por audiência não basta**. Filtrar sem
reescrever entregaria ao PO uma lista que continua dizendo `MinhaDiligenciaDTO.java:76-78`. Separar e
traduzir são duas mudanças.

## Objetivos

1. Permitir que a área de negócio valide o requisito e decida sobre ele sem ler código.
2. Classificar cada lacuna por audiência, com critério checável e reprodutível entre execuções.
3. Formular cada lacuna de negócio na linguagem de quem vai respondê-la.
4. Manter `spec.md` como fonte única, para que nenhuma decisão se perca e o backlog continue nascendo
   de um só documento.
5. Dar a cada uma das duas reuniões um ponto de partida e um comando próprios.
6. Preservar o funcionamento das specs já existentes, escritas sem rótulos de audiência.

## Fora de escopo

- **`redigir-spec-pedido-negocio`.** Ela sofre do mesmo problema, mas a dor relatada está no fluxo da
  Demanda, e incluí-la dobraria o alcance da mudança. Decisão deliberada, registrada para não ser
  lida como esquecimento numa revisão futura.
- **Reescrever specs já geradas.** A spec de diligências pode ser reclassificada manualmente depois,
  numa Demanda real; não faz parte desta mudança.
- **Uma terceira audiência de UX.** Perguntas de detalhe visual (cor exata, ícone) já têm casa em
  `telas-ux-ui.md` e devem ser roteadas para lá, mas não ganham rótulo próprio.
- **Automatizar a convocação das reuniões** ou qualquer integração com agenda.

## Dependência

Este design pressupõe a convenção de pastas de
[`2026-09-24-convencao-nomes-spec-demanda-design.md`](2026-09-24-convencao-nomes-spec-demanda-design.md).
O documento `negocio.md` definido aqui integra o vocabulário fechado daquela pasta, e aquela spec foi
atualizada para incluí-lo.

## Fonte única e visão derivada

`spec.md` permanece dona de **todas** as lacunas. `negocio.md` é uma **projeção** dela, não um
documento paralelo — é essa assimetria que impede os dois de divergirem em silêncio.

Cada lacuna em `spec.md` passa a ter quatro partes:

```markdown
- **N3 · Negócio** — Hoje a data que o usuário vê na tela não é a mesma que faz a
  diligência expirar; a data anunciada pode passar sem nada acontecer. As duas devem
  virar uma só?
  <!-- evidência: MinhaDiligenciaDTO.java:76-78 vs DiligenciaService.java:269-270 -->
```

- **ID** (`N3`, `T2`) — vincula os dois documentos e ancora o registro da decisão.
- **Audiência** — `Negócio` ou `Técnico`.
- **Pergunta** — na linguagem da audiência. Em lacuna de negócio, sem uma linha de código.
- **Evidência** — `caminho:linha`, que permanece em `spec.md` e nunca entra em `negocio.md`.

### Conteúdo de `negocio.md`

1. O que a Demanda pediu, em linguagem de negócio.
2. Como o sistema se comporta hoje, **como fato observado**, sem citação de código.
3. O que muda.
4. As lacunas `Negócio`, só a pergunta.
5. Uma linha de fechamento informando quantas decisões técnicas ficaram para o outro turno.

O item 2 é o que preserva o valor da investigação de código para o negócio. O que o PO precisa saber
de `## Comportamento atual` é o fato — *"hoje o prazo conta 4 dias a partir do convite do executor,
não 7 da abertura"* — não a citação que o sustenta. O fato é de negócio mesmo tendo sido descoberto
no código.

O item 5 existe para que o PO saiba que nada foi descartado, sem ser convidado a opinar.

## Critério de audiência

**Discriminador:** a decisão muda o que o usuário percebe? → `Negócio`. Muda apenas como o sistema
guarda ou calcula, com o mesmo resultado percebido? → `Técnico`.

O critério foi testado contra as 19 lacunas da spec de diligências:

| Lacuna | Audiência | Por quê |
|---|---|---|
| Expiração por rotina ou só quando alguém acessa | `Negócio` | a diligência expirar ou não é percebido |
| Renovação por diligência ou por executor | `Negócio` | muda quem consegue renovar |
| "7 dias corridos" conta hora a hora ou vira à meia-noite | `Negócio` | muda a data em que o usuário perde o prazo |
| Quem vê o novo rótulo | `Negócio` | — |
| `PENDENTE` vira enum persistido ou é rótulo de exibição | `Técnico` | o usuário lê "pendente" nos dois casos |
| Onde persistir prazo vigente e consumo da renovação | `Técnico` | invisível |
| Data recalculada e persistida ou derivada na leitura | `Técnico` | invisível |
| Convites históricos gravados como `VENCIDO` | `Técnico` | migração |

O vocabulário engana nas duas direções, e é por isso que o critério olha a consequência, não as
palavras. "Expiração por agendador" soa técnico e é de negócio. "Enum ou rótulo" soa de negócio — o
nome já foi decidido; o que resta é onde guardá-lo — e é técnico.

### Uma lacuna, uma decisão, uma audiência

Uma lacuna que funde duas perguntas não classifica, e vai inteira para a reunião errada. Exemplo real
da spec de diligências:

> O destaque laranja é exigido para o fundo do texto do status. Qual o valor exato da cor, e ele vale
> para portal e mobile?

São duas: *vale para os dois canais?* é de negócio; *qual o valor exato?* é detalhe visual e pertence
a `telas-ux-ui.md`. Lacunas fundidas devem ser divididas em lacunas ligadas (`N7` origina `T4`).

## Regra de tradução

Para toda lacuna classificada como `Negócio`:

1. É proibido citar arquivo, classe, método, campo, enum, número de linha ou variável **na pergunta**.
2. O estado atual é afirmado como fato observado, nunca como citação: *"hoje o prazo conta 4 dias a
   partir do convite do executor"*, e não *"`DiligenciaService.java:269-270` usa `plusDays`"*.
3. A pergunta termina em uma escolha concreta, com alternativas. Não em *"como deve ser?"*.
4. A evidência `caminho:linha` continua em `spec.md`, ligada pelo ID.

### Verificação automática

Diferente do restante deste repositório, esta regra não fica apenas como instrução textual. Um script
varre as lacunas marcadas `Negócio` e falha ao encontrar, dentro do corpo da pergunta, padrões de
código: `.java:`, `.ts:`, `.dart:`, `.html:`, `Classe.metodo()` ou `:\d+(-\d+)?`.

É a única parte deste design coberta por verificação executável — e é exatamente a que falhou na
reunião que originou a mudança. O precedente de script dentro de skill já existe em
`especificar-debitos-tecnicos/scripts/priorizar.py`.

## Momento de cada rodada

**A orquestradora nunca entrevista.** `redigir-spec-demanda-azure-boards/SKILL.md:64` já proíbe
encadear entrevista, geração ou publicação, e a proibição permanece. Ela gera, classifica e encerra
com um handoff explícito, informando quantas lacunas de cada audiência existem e qual rodada executar
primeiro.

Encadear automaticamente seria pior: a spec costuma ser gerada ao vivo, numa sala com PO, área de
negócio e desenvolvedor. Disparar sozinha uma entrevista de 13 perguntas nesse momento tira do
usuário o controle de quando a sala está pronta.

### Ordem entre as rodadas

Negócio primeiro, por dependência e não por preferência. Lacunas técnicas frequentemente descendem de
decisões de negócio: *"onde persistir o prazo vigente e o consumo da renovação"* só é respondível
depois de *"a renovação é por diligência ou por executor"*. Perguntar ao desenvolvedor antes é pedir
que ele projete para duas regras possíveis.

A máquina para isso já existe. `entrevistar-lacunas-requisito/SKILL.md:27` calcula uma **fronteira** —
os itens perguntáveis agora, sem depender de outro ainda aberto. O escopo de audiência **compõe** com
a fronteira em vez de substituí-la: uma lacuna `Técnico` que depende de uma `Negócio` aberta fica fora
da fronteira mesmo na rodada técnica. Rodar o escopo técnico cedo demais pergunta apenas o que for
genuinamente independente e relata o que está bloqueado, em vez de forçar respostas prematuras.

### Decisão de negócio que cria lacuna técnica

Uma resposta do PO pode originar uma lacuna que não existia. Decidir *"a diligência deve expirar
sozinha, mesmo sem ninguém acessá-la"* cria *"como a rotina de expiração é disparada"*, que é do outro
turno.

Hoje o passo 4 de `entrevistar-lacunas-requisito` conhece dois desfechos: registrar a decisão e
remover a lacuna, ou registrar adiamento explícito. Ele passa a conhecer um terceiro: **registrar uma
lacuna nova**, com ID e audiência, derivada da resposta. Sem isso, decisões de negócio gerariam
trabalho técnico invisível, descoberto apenas na implementação.

### Ciclo completo

| Turno | Quem participa | Comando | Lê | Grava |
|---|---|---|---|---|
| 1 — geração | usuário | `redigir-spec-demanda-azure-boards <id>` | a Demanda | `spec.md`, `negocio.md`, companheiros |
| 2 — refinamento de negócio | PO e área de negócio | `entrevistar-lacunas-requisito`, escopo `negócio` | `negocio.md` | decisões em `spec.md`; pode criar lacunas `T*` |
| 3 — refinamento técnico | desenvolvedor | `entrevistar-lacunas-requisito`, escopo `técnico` | `spec.md` | decisões em `spec.md` |
| 4 — backlog | usuário | `gerar-backlog-azure-boards` | `spec.md` e companheiros | backlog Markdown |

Os turnos 2 e 3 são sessões independentes, em dias distintos, e podem repetir; cada rodada recalcula a
fronteira. Lacunas adiadas não bloqueiam o turno 4: o backlog sai com as Histórias afetadas marcadas
`Não pronta`, como já ocorre hoje.

## Compatibilidade

`entrevistar-lacunas-requisito` precisa degradar bem. Diante de uma spec **sem** rótulos de audiência
— toda spec já escrita, e todas as produzidas por `redigir-spec-pedido-negocio` — ela se comporta como
hoje e pergunta tudo. **O escopo é um filtro opcional, nunca um requisito de formato.** Sem essa
regra, as specs atuais do usuário parariam de funcionar com a entrevista.

O mesmo princípio de fallback permanente adotado na convenção de pastas.

## Alcance da mudança

### Arquivos alterados

| Arquivo | Mudança |
|---|---|
| `redigir-spec-demanda-azure-boards/SKILL.md` | template de lacuna com ID, audiência e evidência; passo 10 gera `negocio.md`; handoff final com a contagem por audiência |
| `entrevistar-lacunas-requisito/SKILL.md` | escopo de audiência compondo com a fronteira; passo 4 ganha o desfecho "criar lacuna nova"; `description` atualizada |
| `gerar-backlog-azure-boards/SKILL.md` | passo 11 sugere a rodada com o escopo correspondente, em vez da chamada genérica |
| `redigir-spec-demanda-azure-boards/scripts/` | novo verificador de linguagem das lacunas `Negócio`, com testes |
| `README.md` | documenta as duas rodadas e o novo documento |
| `2026-09-24-convencao-nomes-spec-demanda-design.md` | `negocio.md` incorporado ao vocabulário fechado |

A `description` de `entrevistar-lacunas-requisito` afirma hoje que a spec é *"tipicamente produzida
por `redigir-spec-pedido-negocio`"*, desatualizada desde a criação da orquestradora da Demanda.

### Testes acompanhados

Os `tests/test_skill_integration.py` das skills afetadas afirmam sobre o texto dos `SKILL.md` e
acompanham as alterações. O verificador de linguagem ganha testes próprios, com casos positivos e
negativos por padrão de código detectado.

### Intocados

`redigir-spec-pedido-negocio`, `refinar-historias-3c`, `refinar-historias-3w`,
`refinar-historias-gherkin`, `orquestrar-skills-de-requisito`, `especificar-debitos-tecnicos`,
`especificar-telas-ux-ui`, `revisar-textos-requisitos` e os dois publicadores de backlog.

## Limites da verificação

Salvo o verificador de linguagem, os testes continuam afirmando sobre o **texto** dos `SKILL.md`, não
sobre o comportamento do agente. Nenhum teste prova que a classificação de audiência foi feita
corretamente numa spec real — esse julgamento é do modelo, e a validação é rodar contra uma Demanda
verdadeira e conferir se a reunião de negócio consegue decidir sem abrir código.

O verificador cobre o sintoma mais objetivo e mais frequente: vazamento de vocabulário técnico para
dentro de uma pergunta de negócio.

## Decisões registradas

| Decisão | Alternativa descartada | Motivo |
|---|---|---|
| `negocio.md` derivado de `spec.md` | Duas specs irmãs em pé de igualdade | Duas fontes divergem em silêncio e quebram a origem única do backlog |
| Separar **e** traduzir | Apenas rotular as lacunas por audiência | Filtrar sem traduzir entrega ao PO uma lista que ainda cita `caminho:linha` |
| Critério por consequência percebida | Critério pelo vocabulário da pergunta | O vocabulário engana nas duas direções, como mostram "expiração por agendador" e "enum ou rótulo" |
| Escopo compõe com a fronteira | Escopo substitui a fronteira | Perder a fronteira permitiria perguntar ao dev algo que depende de decisão de negócio ainda aberta |
| Handoff explícito, sem encadeamento | Orquestradora chama a entrevista de negócio | A spec nasce ao vivo, numa sala com várias pessoas; quem decide o momento é o usuário |
| Escopo como filtro opcional | Escopo exigindo rótulos | Toda spec existente deixaria de funcionar com a entrevista |
