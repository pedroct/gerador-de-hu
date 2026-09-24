# Design: convenção de nomes para a spec e seus documentos companheiros

## Contexto

`redigir-spec-demanda-azure-boards` produz até quatro documentos a partir de uma única Demanda de
Negócio: a Spec-base e, condicionalmente, a spec de débitos técnicos, o briefing de telas UX-UI e o
parecer de revisão de textos. Hoje nenhuma dessas skills prescreve onde salvar nem como nomear o
arquivo. Os `SKILL.md` dizem apenas "salve o documento separado".

Duas consequências disso são visíveis no repositório:

1. **Não existe contrato de localização, só contrato de título.**
   `gerar-backlog-azure-boards` localiza o briefing de telas pelo cabeçalho do documento —
   `gerar-backlog-azure-boards/SKILL.md:21` cita literalmente o documento companheiro
   `Spec: Telas UX-UI — <contexto>`. O caminho do arquivo nunca entra na conversa.
2. **`docs/specs/` é convenção de fato, não documentada.** O caminho só aparece nos fixtures
   `publicar-backlog-azure-boards/tests/fixtures/valid-backlog.md` e
   `publicar-backlog-demanda-azure-boards/tests/fixtures/valid-backlog.md`, como valor de exemplo do
   campo `Spec de origem`. Nenhum `SKILL.md` o menciona.

Na prática, quando duas Demandas convivem no mesmo diretório, os quatro documentos de uma se
misturam aos quatro da outra, e o único jeito de separá-las é abrir cada arquivo e ler o título.

Este design introduz uma convenção de nomes ancorada no ID da Demanda de Negócio do Azure Boards.

## Objetivos

1. Agrupar fisicamente os documentos de uma mesma Demanda, de modo que o agrupamento seja visível
   sem abrir nenhum arquivo.
2. Tornar o ID da Demanda legível no sistema de arquivos, como rótulo.
3. Dar às três skills especializadas um destino determinístico para suas saídas quando elas forem
   chamadas pela orquestradora.
4. Documentar `docs/specs/` como raiz padrão, promovendo a convenção de fato a convenção escrita.
5. Preservar integralmente o funcionamento das specs já existentes, escritas antes desta convenção.

## Fora de escopo

- **`redigir-spec-pedido-negocio`.** Ela roda quando ainda não existe Demanda no Azure Boards —
  é exatamente o cenário dela (`README.md:351`). A convenção não a alcança e ela continua salvando
  como hoje. Esta é uma decisão deliberada, registrada aqui para não ser lida como esquecimento numa
  revisão futura.
- **As chamadas avulsas das skills especializadas.** `especificar-debitos-tecnicos` é invocada de
  quatro lugares, e em três deles não há Demanda: `refinar-historias-3c/SKILL.md:17`,
  `redigir-spec-pedido-negocio/SKILL.md:34` e o roteador de `orquestrar-skills-de-requisito`, cujo
  `scripts/roteamento.py:79` classifica o caso como "observação técnica interna, sem demanda de
  negócio". Nesses três, nada muda.
- **Migração de specs existentes.** Nenhum arquivo já escrito precisa ser renomeado ou movido.
- **Os dois publicadores de backlog.** Eles consomem o backlog Markdown, nunca a spec.
- **Verificar, por teste automatizado, que o agente salvou no caminho certo.** Ver
  [Limites da verificação](#limites-da-verificação).

## Contrato da pasta

Cada Demanda de Negócio ganha um diretório próprio:

```
docs/specs/DN-14125-emissao-de-convites/
├── spec.md              ← Spec-base, sempre presente
├── negocio.md           ← projeção para o refinamento de negócio, condicional
├── debitos-tecnicos.md  ← saída de especificar-debitos-tecnicos, condicional
├── telas-ux-ui.md       ← saída de especificar-telas-ux-ui, condicional
└── revisao-textos.md    ← saída de revisar-textos-requisitos, condicional
```

### Nome do diretório

`DN-<id>-<slug>`, onde:

- `DN` é literal, abreviação de Demanda de Negócio.
- `<id>` é o ID numérico do work item no Azure Boards, sem zeros à esquerda.
- `<slug>` deriva do `System.Title` da Demanda, em kebab-case, sem acentos, truncado em 60
  caracteres. O slug é conforto de leitura: pode ser reescrito a qualquer momento sem quebrar nada,
  porque nada o consome.

A ordenação alfabética de um conjunto de diretórios assim não é numérica — `DN-14125` aparece antes
de `DN-9999`. Zero-padding não resolve de forma durável, já que os IDs crescem sem teto conhecido.
Aceitamos a limitação.

### Nomes internos

O vocabulário é fechado e tem exatamente cinco valores: `spec.md`, `negocio.md`,
`debitos-tecnicos.md`, `telas-ux-ui.md` e `revisao-textos.md`. Não levam prefixo `spec-` porque o
diretório já estabelece o escopo; `DN-14125-emissao-de-convites/telas-ux-ui.md` se lê inteiro, e
`.../spec-telas-ux-ui.md` apenas repetiria.

`negocio.md` não nasce deste design. Ele é definido em
[`2026-09-24-separar-refinamento-negocio-tecnico-design.md`](2026-09-24-separar-refinamento-negocio-tecnico-design.md)
e entra aqui apenas para ocupar seu lugar no vocabulário fechado. As duas mudanças são
independentes: esta pode ser implementada sozinha, e nesse caso a pasta simplesmente não terá esse
arquivo.

Ser um conjunto fechado é o que importa: permite que a orquestradora e `gerar-backlog-azure-boards`
localizem um companheiro por construção, em vez de procurá-lo.

### Raiz

`docs/specs/` passa a ser o padrão documentado, e o usuário pode indicar outra raiz na invocação. A
skill sempre informa o caminho final que usou.

## Propriedade da pasta

**A pasta pertence à orquestradora, não às skills especializadas.**

`redigir-spec-demanda-azure-boards` cria o diretório no passo 6, junto com a Spec-base, e repassa o
caminho a cada especializada nos passos 7 a 9.

As três especializadas passam a aceitar um **diretório de destino como insumo opcional**:

- Recebeu diretório: salva ali, com o nome do vocabulário fechado.
- Não recebeu: salva como hoje.

Essa assimetria é o ponto central do design. Ela mantém as três skills ignorantes do que é uma
Demanda de Negócio, o que preserva a estrutura acíclica descrita em `README.md:120` — elas continuam
sendo folhas, sem conhecimento de Azure Boards. E resolve o caso avulso sem regra especial: ele
simplesmente não muda de comportamento.

`revisar-textos-requisitos` hoje não prescreve título de documento nenhum — seu
`SKILL.md:50` define apenas o corpo do parecer. Ela ganha `# Revisão de textos — <contexto>`, para
ficar simétrica às outras duas saídas companheiras.

## Consumo pelo gerador de backlog

`gerar-backlog-azure-boards` ganha um atalho, não uma substituição:

- Recebeu o diretório: lê `spec.md` e procura os irmãos pelo vocabulário fechado.
- Não recebeu: mantém o comportamento atual, localizando os companheiros pelo título.

**A busca por título permanece como fallback permanente, não como etapa de transição.** É ela que
mantém funcionando toda spec escrita antes desta convenção, e também as specs vindas de
`redigir-spec-pedido-negocio`, que estão fora do escopo desta mudança. O passo 2 do fluxo continua
tratando os companheiros como input opcional por arquivo, nunca como invocação.

O campo `Spec de origem` dos metadados do backlog passa a registrar o caminho completo até
`spec.md`. O campo sempre aceitou "documento, versão ou localização"
(`gerar-backlog-azure-boards/references/backlog-markdown-contract.md:79`), então nenhum fixture
existente se torna inválido.

## O nome é rótulo, nunca fonte

`gerar-backlog-azure-boards/references/backlog-markdown-contract.md:169` já determina que o ID da
Demanda seja copiado da seção `## Fonte da Demanda` da spec, e proíbe inferi-lo de qualquer outra
fonte. Essa regra não muda, mas passa a ter um risco concreto que antes não existia: depois desta
convenção, há um `DN-14125` a um `basename` de distância, e ele parece uma resposta.

Não é. Um diretório renomeado à mão, copiado de outra Demanda ou criado por engano produziria um
backlog vinculado à Demanda errada — e o vínculo errado só apareceria depois da publicação, quando os
Épicos já estivessem pendurados no work item incorreto.

O contrato passa a citar o nome do diretório nominalmente entre as fontes proibidas. O ID no caminho
existe para quem lê um `ls`; a verdade está dentro de `spec.md`.

## Alcance da mudança

### Arquivos alterados

| Arquivo | Mudança |
|---|---|
| `redigir-spec-demanda-azure-boards/SKILL.md` | passo 6 cria o diretório; passos 7 a 9 repassam o caminho |
| `especificar-debitos-tecnicos/SKILL.md` | aceita diretório opcional; salva como `debitos-tecnicos.md` |
| `especificar-telas-ux-ui/SKILL.md` | idem no passo 16; salva como `telas-ux-ui.md` |
| `revisar-textos-requisitos/SKILL.md` | ganha título de documento; aceita diretório; salva como `revisao-textos.md` |
| `gerar-backlog-azure-boards/SKILL.md` | passo 2 ganha o atalho por diretório, preservando a busca por título |
| `gerar-backlog-azure-boards/references/backlog-markdown-contract.md` | a proibição de inferir o ID passa a citar o nome do diretório |
| `README.md` | documenta a convenção e a raiz `docs/specs/` |

### Testes acompanhados

Cada skill afetada tem um `tests/test_skill_integration.py` que afirma sobre o texto do respectivo
`SKILL.md`. As asserções acompanham as alterações acima, cobrindo:

- que cada especializada declara o nome de arquivo do vocabulário fechado;
- que cada especializada declara o comportamento de fallback quando não recebe diretório;
- que `gerar-backlog-azure-boards` declara a busca por título como fallback permanente;
- que o contrato de backlog proíbe o nome do diretório como fonte do ID.

### Intocados

`redigir-spec-pedido-negocio`, `refinar-historias-3c`, `orquestrar-skills-de-requisito`,
`entrevistar-lacunas-requisito`, `refinar-historias-3w`, `refinar-historias-gherkin` e os dois
publicadores de backlog. Os fixtures `docs/specs/spec-exemplo.md` continuam válidos.

## Limites da verificação

Os testes deste projeto verificam o **texto** dos `SKILL.md`, não o comportamento do agente. Nenhum
teste automatizado provará que o agente de fato gravou
`docs/specs/DN-14125-emissao-de-convites/telas-ux-ui.md`.

Isso é uma característica do projeto inteiro, não uma dívida introduzida aqui. Mas delimita o que
esta mudança garante: que a instrução está escrita e é inequívoca — não que o comportamento foi
observado. A validação de comportamento é manual, rodando a orquestradora contra uma Demanda real e
conferindo a árvore de arquivos resultante.

## Decisões registradas

| Decisão | Alternativa descartada | Motivo |
|---|---|---|
| Diretório por Demanda | Prefixo `DN-<id>-` em arquivos soltos | O prefixo exigiria repetir o slug em quatro arquivos escritos por quatro skills independentes; slugs divergentes quebrariam o agrupamento visual, que é o objetivo inteiro |
| Slug só no diretório | Slug em cada arquivo interno | O diretório já identifica a Demanda; repetir seria ruído |
| Diretório como insumo opcional das especializadas | Especializadas conhecerem a Demanda | Manteria as folhas acopladas ao Azure Boards e quebraria a estrutura acíclica do `README.md:120` |
| Busca por título como fallback permanente | Migração para busca só por caminho | Toda spec existente e toda spec de `redigir-spec-pedido-negocio` deixariam de ser encontradas |
| `docs/specs/` como raiz padrão | Deixar a raiz indefinida, como hoje | A convenção de fato já existe nos fixtures; escrevê-la custa nada e remove uma decisão por execução |
