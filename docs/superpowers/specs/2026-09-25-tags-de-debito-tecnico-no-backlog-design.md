# Design: tags no backlog e o caminho do débito técnico até o Azure Boards

## Contexto

O documento `debitos-tecnicos.md` já prioriza cada débito e recomenda `Bug` ou `User Story` por item.
A pergunta que originou este design foi outra: se `User Story` é o tipo de uma funcionalidade nova,
não seria melhor criar um work item type personalizado `Débito Técnico` no Azure Boards?

A resposta foi não, e o motivo não é custo.

### Por que não um tipo personalizado

`User Story` não é "o tipo da funcionalidade nova". É o tipo de folha da categoria Requirement — a
unidade que entra no backlog, recebe Story Points, aparece no board, conta na velocity e fecha no
burndown. A narrativa "Como… quero… para…" é convenção de escrita, não restrição do tipo. O processo
Scrum chama a mesma coisa de `Product Backlog Item`, e o publicador já trata os dois como
intercambiáveis via `AZURE_DEVOPS_TIPO_USER_STORY`.

Um tipo personalizado exige processo herdado, aplicado ao projeto inteiro, e leva a uma escolha
binária em que os dois lados são ruins:

1. O tipo entra no nível de backlog Requirements: comporta-se exatamente como a User Story, com
   outro nome. Pagou-se uma customização de processo para renomear um tipo.
2. O tipo fica fora dos níveis de backlog: some do backlog, do board, da velocity e do burndown. É o
   destino do `Issue` no processo Agile. Para débito técnico esse é o pior resultado possível —
   débito que não compete por sprint não é pago.

### Por que não uma Area Path dedicada

Pelo mesmo motivo, em outro eixo. Area Path roteia trabalho para um time e carrega permissão. Uma
Area de débito não vinculada a time some do backlog de todos; vinculada ao time de sustentação, é
`Sustentacao` com outro nome e uma escolha a mais para errar em cada publicação.

Há ainda uma restrição dura: `publicar-backlog-demanda-azure-boards` herda `Area Path` da Demanda. Uma
Area dedicada só funcionaria no fluxo solto, e o mesmo débito cairia em áreas diferentes conforme a
publicadora — pior que não ter.

Se um dia for preciso reservar capacidade para débito, a ferramenta é política de sprint medida pela
tag, não Area, que reserva time e não esforço.

### O problema real

O que falta não é um tipo: é o débito publicado perder a identidade. Depois de criado o work item,
ninguém consegue perguntar "quanto de débito temos", "quanto pagamos neste trimestre" ou "quais são
Restrição". Isso é trabalho de discriminador, e o discriminador barato e filtrável do Azure Boards
é a tag.

Com a tag, a visão de débito existe independentemente da hierarquia. É isso que permite pendurar o
débito na capacidade afetada e ter as duas visões — hierarquia por capacidade e filtro por tag — em
vez de escolher uma.

## Objetivos

- O backlog Markdown passa a declarar tags por item, e as publicadoras as enviam em `System.Tags`.
- Um débito publicado carrega `debito-tecnico`, sua faixa de priorização e, quando houver, a Demanda
  que o revelou — tudo filtrável por query e por Analytics, sem customizar o processo.
- O documento de débitos vira spec de entrada legítima do `gerar-backlog-azure-boards`, produzindo um
  backlog próprio.
- Nenhum backlog já publicado deixa de retomar por causa desta mudança.

## Fora de escopo

- **Tipo de work item personalizado e Area Path dedicada.** Recusados acima, com motivo.
- **Flag de execução `--tags` no publicador.** Aplicaria a mesma tag a todos os itens da rodada, o que
  torna a faixa por item impossível, e deixaria a tag fora do artefato revisado por humano — o mesmo
  backlog publicado duas vezes com flags diferentes daria resultados diferentes sem deixar rastro.
  Tag de campanha (`q4-2026`) não é necessidade declarada.
- **Gherkin para débitos.** A skill de débitos continua produzindo critérios em bullets; ver
  "Critérios de aceite" abaixo.
- **Consulta anti-duplicidade de Epic/Feature via MCP.** Continua adiada desde 2026-09-12. Ver
  "Riscos conhecidos".
- **Checagem cruzada entre o `demanda_id` do publicador e o backlog.** Lacuna real encontrada durante
  o desenho, mas independente deste trabalho. Ver "Riscos conhecidos".

## O campo `Tags` no contrato do backlog

Genérico no contrato, com vocabulário reservado na skill de débitos. Assim, marcar `risco-lgpd` ou
`sustentacao` amanhã não exige mexer no contrato de novo.

### Formato

Uma subseção no mesmo nível das demais seções do item:

```markdown
##### Tags
debito-tecnico, dt-restricao, dn-14125
```

### Regras

- **Opcional.** Item sem a subseção é válido — é o caso de todo backlog existente.
- **Presente e vazia é erro.** Diferente de `Acceptance Criteria`, que fica legitimamente em branco
  com Confirmation `Ausente` ou `Parcial`, uma seção `Tags` vazia só ocorre quando algo se perdeu no
  caminho.
- **Separador é vírgula**, com trim em cada valor.
- **`,` e `;` são proibidos dentro de uma tag.** `System.Tags` usa `;` como separador canônico; uma
  tag com separador embutido viraria duas tags silenciosamente no Azure Boards.
- **Repetição deduplica preservando a ordem**, sem erro. A mesma tag escrita duas vezes não é
  ambiguidade.
- **Vale em qualquer item** — Epic, Feature ou folha. O contrato não restringe; quem restringe é a
  política de emissão.

### Os dois parsers mudam no mesmo commit

`interpretar_markdown._nome_secao` e `contrato_backlog._section_heading` discordam por construção
diante de uma seção desconhecida: o primeiro levanta `heading fora do contrato`, o segundo devolve
`None` e a linha acaba anexada como conteúdo da seção anterior. Já existe um comentário no código
pedindo que os dois concordem.

Se `Tags` entrar em apenas um dos conjuntos, um backlog com tags é aceito por um caminho e explode no
outro. `Tags` entra em `_SECOES` e em `SECTION_NAMES` na mesma mudança.

## Vocabulário reservado do débito técnico

Definido pela skill `especificar-debitos-tecnicos`, não pelo contrato. Para o publicador, tag é
string opaca.

| Tag | Quando |
|---|---|
| `debito-tecnico` | todo item de folha originado de um DT |
| `dt-restricao` / `dt-candidato` / `dt-a-confirmar` | exatamente uma, espelhando `faixa()` |
| `dn-<id>` | quando a spec de débitos registrar Demanda de origem |

A faixa precisa virar campo oficial antes de virar tag. Hoje `faixa()` só aparece no stdout do
`priorizar.py`, e o template do `Resumo priorizado` não tem a coluna — documentos gerados já a
trazem, mas por iniciativa da rodada, não por contrato. Uma tag não pode depender de um dado que o
template não garante.

**Só em item de folha.** Epic e Feature são contêineres de capacidade compartilhados com o trabalho
funcional; marcá-los de débito mentiria sobre a capacidade inteira.

**A tag de faixa é um snapshot da geração.** Uma reavaliação que mova o DT-03 de `a-confirmar` para
`restricao` não atualiza o work item já publicado. A skill precisa dizer isso, senão alguém lê a tag
como verdade corrente seis meses depois.

## Hierarquia do backlog de débitos

O débito entra como backlog próprio: `debitos-tecnicos.md` é a spec de entrada do
`gerar-backlog-azure-boards`, e não um companheiro-contexto. Isso mantém coerente a regra atual de que
o documento de débitos encontrado numa pasta de Demanda é contexto rotulado — companheiro de uma
Demanda é contexto, spec de entrada é origem — e deixa a revisão do débito acontecer no ritmo dela.

**Epic e Feature nomeiam a capacidade afetada**, como manda a decisão de 2026-09-12: contêineres
duráveis de capacidade, nunca do problema. Um Epic "Débito técnico" com Features por categoria seria
contêiner do problema, e esconderia o débito de quem olha a capacidade. Como a tag já garante a visão
de débito, pendurar na capacidade dá as duas visões em vez de trocar uma pela outra.

## Vínculo com a Demanda

Rastreável no documento, solto na publicação.

A spec de débitos ganha `## Fonte da Demanda`, copiada da spec de origem — **nunca do nome da pasta**,
replicando a proibição que o contrato do backlog já carrega: um diretório `DN-14125-<slug>/` parece uma
resposta e não é. O `#id` chega ao backlog como rastreabilidade e vira a tag `dn-<id>`.

A publicação usa a publicadora solta, com Area e Iteration escolhidas por execução. O motivo é o
`Iteration Path`: `publicar-backlog-demanda-azure-boards` o herda da Demanda, ou seja, o débito
nasceria alocado na sprint da Demanda — exatamente a sprint em que ele não será pago — e alguém teria
que remanejar item por item depois.

`Area Path` permanece `CESOP-DILIGENCIA\Sustentacao`, escolhido por execução como hoje.

## Critérios de aceite do débito

Os `Critérios de aceite` da spec de débitos são bullets; `Acceptance Criteria` do backlog só aceita
blocos cercados `gherkin`, e o contrato é taxativo: "nenhum outro conteúdo".

**Os bullets vão para a Conversation e `Acceptance Criteria` fica em branco**, que é o que o contrato
manda quando a Confirmation não está completa. Quem quiser critério publicável roda
`refinar-historias-gherkin` sobre o item depois.

A consequência é visível e aceita: **um débito publicado chega ao Azure Boards sem critério de aceite
preenchido.** A alternativa — fazer a skill de débitos produzir Gherkin — é mais trabalho e está fora
do que se pediu.

## Compatibilidade

Um campo novo no item muda o hash do plano, e manifesto com hash divergente recusa retomar. Uma
publicação interrompida no meio exigiria reconciliação manual item a item.

**A chave `tags` só entra no dict serializado por `_calcular_hash` quando a tupla não é vazia.**
Backlog sem tags produz exatamente o hash de hoje, e toda publicação parcial em andamento retoma
normalmente. A assimetria precisa de comentário no código explicando o porquê — sem ele, alguém a
"limpa" numa refatoração futura e quebra a retomada sem perceber.

## Alcance da mudança

Tudo em `src/` sai em dobro: `publicar-backlog-azure-boards` e `publicar-backlog-demanda-azure-boards`
são gêmeos.

### Publicadoras (× 2)

| Arquivo | Mudança |
|---|---|
| `contrato_backlog.py` | `Tags` em `SECTION_NAMES`; parsing com trim, dedup e as recusas de formato |
| `interpretar_markdown.py` | `Tags` em `_SECOES`; `_converter_item` preenche o campo novo |
| `modelos.py` | `ItemBacklog` e `OperacaoCriacao` ganham `tags: tuple[str, ...] = ()` — tupla porque os dataclasses são `frozen` |
| `planejar_publicacao.py` | `_criar_operacao` propaga; `_calcular_hash` inclui `"tags"` só quando não vazia, com comentário |
| `cliente_azure_devops.py` | `op: add` em `/fields/System.Tags`, valores unidos por `"; "`, apenas quando há tags |

### Skills

| Arquivo | Mudança |
|---|---|
| `gerar-backlog-azure-boards/references/backlog-markdown-contract.md` | seção `Tags`: formato, regras, posição no template, mapeamento para `System.Tags` |
| `gerar-backlog-azure-boards/SKILL.md` | reconhece `Spec: Débitos técnicos` como spec de entrada; emite as tags nos itens de folha; Epic/Feature por capacidade e sem tags |
| `especificar-debitos-tecnicos/SKILL.md` | `Faixa` como campo oficial; `## Fonte da Demanda`; nota do snapshot |

### Testes

- Parsing: tags ausentes, uma tag, várias, espaços em volta, repetidas, seção vazia, tag vazia entre
  vírgulas, `;` embutido.
- Concordância entre os dois parsers diante de `Tags`.
- Hash: backlog sem tags mantém o hash anterior (é o teste que protege a retomada); backlog com tags
  muda o hash.
- Payload: `System.Tags` ausente sem tags, presente e unido por `"; "` com tags.
- Validação estrutural agregando os erros novos junto dos existentes.

## Riscos conhecidos

**Recriação de Epic/Feature já publicados.** A publicadora só pendura um item em outro criado na
mesma execução; não existe caminho para pendurar em Epic já existente no Boards. Uma rodada de débito
pode recriar a capacidade. Não é problema novo que o débito introduza — é o mesmo da segunda Demanda
sobre uma capacidade já publicada — e a consulta anti-duplicidade via MCP segue adiada desde
2026-09-12. Fica registrado, não resolvido aqui.

**`demanda_id` sem checagem cruzada.** `publicar-backlog-demanda-azure-boards` toma o ID de
`AZURE_DEVOPS_DEMANDA` ou de pergunta interativa e não confere contra o `Demanda de Negócio de origem`
escrito no backlog: grep por esse rótulo no pacote inteiro devolve zero ocorrências. Os Épicos
penduram na Demanda digitada, certa ou errada, em silêncio. Encontrado durante este desenho, fora do
escopo deste trabalho, merece correção própria.

## Decisões registradas

| Decisão | Alternativa recusada | Motivo |
|---|---|---|
| Tag em vez de work item type personalizado | `Débito Técnico` como tipo | ou vira User Story renomeada, ou some do backlog |
| Tag em vez de Area Path dedicada | Area de débito | Area roteia time, não classifica; e a publicadora de Demanda herda a Area |
| `Tags` genérico no contrato | campo fechado `Débito técnico:` | qualquer marcação futura sem novo campo no contrato |
| Tags declaradas no Markdown | `--tags` por execução | a faixa é por item, e a tag precisa estar no artefato revisado |
| `tags` fora do hash quando vazia | incluir sempre | preserva a retomada de manifestos existentes |
| Backlog de débitos próprio | débitos no backlog da Demanda | evita reverter a regra atual e misturar duas priorizações num documento |
| Epic/Feature por capacidade | Epic "Débito técnico" por categoria | decisão de 2026-09-12; a tag já dá a visão de débito |
| Publicação solta, com Demanda rastreável | pendurar na Demanda | a publicadora de Demanda herdaria a sprint da Demanda para o débito |
| `Acceptance Criteria` em branco no débito | Gherkin na skill de débitos | fora do escopo pedido; `refinar-historias-gherkin` cobre depois |
