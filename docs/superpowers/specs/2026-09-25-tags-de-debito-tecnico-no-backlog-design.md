# Design: tags no backlog como discriminador de origem dos work items

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

### O mesmo sintoma em outro lugar

O débito não é o único item que chega ao Boards sem identidade. `especificar-telas-ux-ui` produz um
item de design por par (requisito, plataforma), e `gerar-backlog` o cria como `User Story` irmã do
item funcional. No documento ele é distinguível: nasce de um `TL-xx` e declara `Bloqueia`. **No Azure
Boards é uma User Story igual a qualquer outra.**

A faceta plataforma tem valor próprio, porque a skill é taxativa em nunca agrupar web e mobile no
mesmo item de design: quem trabalha com tela precisa perguntar "o que está pendente de design em web".

E o item de design carrega um segundo problema, que a tag não resolve: **o bloqueio que ele representa
também é invisível no Boards.** `Depende de` / `Bloqueia` é texto na `Description`, não relação. Por
isso este design trata as duas coisas — a tag marca natureza, o link Predecessor/Sucessor cria a
relação — e não usa uma para fingir a outra.

Já a spec de negócio é o caso em que o mesmo raciocínio leva a uma conclusão diferente — ver
"Classificação do pedido não vira tag", em Fora de escopo.

## Objetivos

- O backlog Markdown passa a declarar tags por item, e as publicadoras as enviam em `System.Tags`.
- Um débito publicado carrega `debito-tecnico`, sua faixa de priorização e, quando houver, a Demanda
  que o revelou — tudo filtrável por query e por Analytics, sem customizar o processo.
- Um item de design carrega `design-ux-ui` e a plataforma.
- `Depende de` deixa de ser texto solto na `Description` e vira dependência estruturada, publicada
  como link Predecessor/Sucessor no Azure Boards.
- Um Epic ou Feature de capacidade já publicado deixa de ser recriado: o backlog declara o ID
  existente e o publicador pendura os filhos nele.
- A publicadora de Demanda recusa publicar quando o `demanda_id` informado diverge do que o backlog
  declara, antes de qualquer escrita.
- `dn-<id>` deixa de ser exclusivo do débito e marca todo item nascido de uma Demanda, de modo que "o
  que a DN-14125 gerou de trabalho" seja uma query em vez de uma navegação pela árvore.
- O documento de débitos vira spec de entrada legítima do `gerar-backlog-azure-boards`, produzindo um
  backlog próprio.
- Nenhum backlog já publicado deixa de retomar por causa desta mudança.

## Fora de escopo

- **Tipo de work item personalizado e Area Path dedicada.** Recusados acima, com motivo.
- **Flag de execução `--tags` no publicador.** Aplicaria a mesma tag a todos os itens da rodada, o que
  torna a faixa por item impossível, e deixaria a tag fora do artefato revisado por humano — o mesmo
  backlog publicado duas vezes com flags diferentes daria resultados diferentes sem deixar rastro.
  Tag de campanha (`q4-2026`) não é necessidade declarada.
- **Classificação do pedido não vira tag.** `Defeito | Melhoria | Outro` é metadado único da spec de
  negócio, e o contrato insiste que a decisão entre Bug e User Story é por item, nunca herdada dessa
  classificação — uma mesma spec origina os dois. Carimbar `defeito` em todos os itens de uma spec
  `Defeito` reintroduziria a herança cega como metadado publicado, e a tag discordaria do tipo em
  todo item que corretamente virou User Story. O tipo do work item já responde isso, item a item e com
  mais precisão. O que generaliza da spec de negócio é `dn-<id>`, não a classificação.
- **Tag por spec de origem** (ex.: `spec-emissao-convites`). Rastreabilidade mais fina que `dn-<id>`
  quando uma Demanda gera várias specs, mas o vocabulário cresceria a cada spec e sujaria o
  autocompletar de tags do projeto.
- **Tag `depende-de-design`.** Considerada e descartada. A justificativa dela era ser o único sinal
  visível de bloqueio; com o link Predecessor publicado, o sinal existe, é preciso — aponta *qual*
  item bloqueia, coisa que a tag não fazia — e não envelhece, porque fecha junto com o item de
  design. Uma tag que continuasse afirmando bloqueio depois do design entregue seria pior que nada.
- **Gherkin para débitos.** A skill de débitos continua produzindo critérios em bullets; ver
  "Critérios de aceite" abaixo.
- **Descoberta automática do Epic/Feature já publicado.** O publicador não consulta o Boards para
  achar a capacidade: ele obedece ao ID declarado no documento. Automatizar a descoberta — propor o ID
  durante a geração do backlog — é trabalho do `gerar-backlog`, e fica para depois. Ver "Item já
  publicado no Azure Boards".
- **Busca por título como anti-duplicidade.** Estruturalmente inviável: o título remoto é
  `{data_geracao} {chave} {titulo_curto}`, então a mesma capacidade publicada a partir de dois
  backlogs tem títulos diferentes por construção, e dois títulos curtos iguais podem ser capacidades
  distintas. Erraria nos dois sentidos.

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

## Vocabulário reservado

Definido pelas skills, não pelo contrato. Para o publicador, tag é string opaca.

| Tag | Emitida por | Quando |
|---|---|---|
| `debito-tecnico` | `especificar-debitos-tecnicos` | todo item de folha originado de um DT |
| `dt-restricao` / `dt-candidato` / `dt-a-confirmar` | `especificar-debitos-tecnicos` | exatamente uma, espelhando `faixa()` |
| `design-ux-ui` | `especificar-telas-ux-ui` | item de design originado de um TL |
| `plataforma-web` / `plataforma-mobile` | `especificar-telas-ux-ui` | exatamente uma, no item de design |
| `dn-<id>` | qualquer origem | todo item nascido de uma Demanda |

**Só em item de folha.** Epic e Feature são contêineres de capacidade compartilhados entre origens;
marcá-los de débito ou de design mentiria sobre a capacidade inteira. `dn-<id>` segue a mesma regra.

### Dois dados precisam virar campo antes de virar tag

Uma tag não pode depender de um dado que o template não garante.

- **`Faixa`**, na skill de débitos: hoje `faixa()` só aparece no stdout do `priorizar.py`, e o
  template do `Resumo priorizado` não tem a coluna. Documentos gerados já a trazem, mas por
  iniciativa da rodada, não por contrato.
- **Plataforma por item**, na skill de telas: hoje ela está no cabeçalho do documento
  (`**Plataforma:** <Web | Mobile>`) e no título em prosa do `TL-xx` ("com a plataforma no nome").
  Derivar tag de título é frágil; o item precisa de um campo próprio.

### A faixa envelhece

`dt-<faixa>` é um snapshot do momento da geração e não se corrige sozinha depois de publicada: uma
reavaliação que mova o DT-03 de `a-confirmar` para `restricao` não atualiza o work item já criado. A
skill de débitos precisa dizer isso, senão alguém lê a tag como verdade corrente seis meses depois.

É o único caso no vocabulário. `debito-tecnico`, `design-ux-ui`, a plataforma e `dn-<id>` afirmam
origem, e origem não muda.

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

A tag em si não é exclusiva do débito: o backlog já registra `Demanda de Negócio de origem` em
qualquer modo, e é desse campo que `dn-<id>` sai, venha o item de uma spec de negócio, de telas ou de
débitos. O que esta seção acrescenta é o caminho que faltava — a spec de débitos não tinha de onde
tirar o `#id`.

A publicação **do backlog de débitos** usa a publicadora solta, com Area e Iteration escolhidas por
execução; o backlog funcional de uma Demanda segue publicando como hoje. O motivo é o
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

## Dependência estruturada e link Predecessor/Sucessor

Hoje `Depende de` / `Bloqueia` é texto informativo dentro da `Description`, e o contrato o declara
responsabilidade de "uma etapa de publicação futura". Esta é a etapa.

### O campo

`Depende de` vira subseção estruturada do item, como `Parent`: uma ou mais chaves documentais, sem o
que não há o que ordenar nem o que vincular. **Vale entre quaisquer dois itens de folha** — o fluxo de
telas é apenas o primeiro a usar. Mesmo princípio do campo `Tags`: o contrato define o mecanismo, a
skill define quando emitir.

`Bloqueia` permanece documental. É a inversa do mesmo link, e publicar os dois duplicaria a relação.

### O problema é ordem, não API

`_ORDEM_TIPOS` põe `User Story` e `Bug` ambos em 2 e desempata pela chave. O item funcional `1.1.1` e
o item de design `1.1.2` são irmãos sob a mesma Feature, então o funcional é criado **antes** do
design de que depende, e na hora de criá-lo o ID do design ainda não existe. `Parent` nunca teve esse
problema porque o pai sempre vem antes por tipo.

**A solução é ordenação topológica estável no planejador**, e não uma segunda passada de vinculação.
O predecessor passa a ser criado antes, e o link entra no payload de criação do dependente, exatamente
como `Parent` já entra. Nenhuma operação nova, nenhuma mudança na forma do manifesto.

A segunda passada foi recusada por desproporção: o publicador passaria a ter uma operação que não é
criação, e isso contamina manifesto, autorização, retomada e idempotência — todos construídos em cima
de "só criamos".

Entre rodadas o mecanismo já funciona: `executar_publicacao` mantém `registros`, lido do manifesto no
início, mapeando chave documental para ID criado. Um predecessor criado numa rodada anterior tem ID
disponível na seguinte, do mesmo modo que um pai tem.

### Compatibilidade da ordem

Uma ordenação topológica **estável** sobre um grafo sem arestas devolve a ordem de hoje, item por
item. Backlog sem `Depende de` produz a mesma sequência, logo o mesmo hash, logo a retomada
preservada — a mesma propriedade decidida para as tags, pelo mesmo motivo.

### Recusas do planejador

Com o mecanismo genérico, o ciclo deixa de ser impossível por construção — no par bipartido
design/funcional ele não podia existir; entre duas histórias funcionais, pode. O planejador recusa,
nomeando as chaves envolvidas:

- ciclo de dependência;
- `Depende de` apontando para chave inexistente;
- `Depende de` apontando para item que não é folha.

### Direção do link

No item dependente entra `System.LinkTypes.Dependency-Reverse` apontando para o predecessor — "o alvo
é meu predecessor", mesma convenção do `Hierarchy-Reverse` que o filho já usa para apontar o pai.

**Inverter a direção é o erro clássico aqui e passa despercebido em teste de caminho feliz**, porque a
relação aparece nos dois work items de qualquer forma — só que trocada. A implementação confirma os
nomes contra a API antes de fechar, e o teste afirma a direção, não apenas a existência do link.

## Item já publicado no Azure Boards

A hierarquia é por capacidade e a capacidade é durável, então a segunda rodada sobre o mesmo fluxo
encontra o Epic — e às vezes a Feature — já no Boards. Hoje o publicador os recriaria, porque só sabe
pendurar um item em outro criado por ele.

### O campo

Epic e Feature ganham uma subseção opcional com o ID do work item existente. Quando ela está presente,
**o publicador não cria o item**: ele apenas resolve os filhos para aquele ID.

Este é o único lugar do backlog em que um ID real do Azure Boards aparece, e a proibição geral do
contrato continua valendo em volta dele: o ID é **copiado do Boards**, nunca inferido, nunca derivado
da chave documental, nunca do nome da pasta.

Não vale em item de folha. O caso de uso é reaproveitar contêiner de capacidade; permitir numa
História abriria caminho para encobrir problema de manifesto declarando um ID à mão.

### Validações

- **Ancestral também declarado.** Uma Feature com ID existente exige que seu Epic também tenha ID
  declarado — não existe Feature publicada sob um Epic que ainda será criado.
- **O item existe e é do tipo esperado.** O publicador confere antes de pendurar qualquer filho, como
  `leitor_demanda` já faz com o work item da Demanda. Pendurar épicos sob um ID errado é caro de
  desfazer, e um ID digitado com um dígito a menos aponta para outro work item qualquer.

### Manifesto

A chave documental passa a poder mapear para um ID **não criado por esta ferramenta**. O registro
precisa ser distinguível: nunca contado como criação, nunca elegível para reconciliação, e nunca
apagado por uma retomada. Sem essa distinção, o manifesto passaria a afirmar que criamos algo que já
existia.

## Checagem cruzada do `demanda_id`

`publicar-backlog-demanda-azure-boards` toma o ID de `AZURE_DEVOPS_DEMANDA` ou de pergunta interativa
e nunca o confere contra o `Demanda de Negócio de origem` escrito no backlog. Os Épicos penduram na
Demanda digitada, certa ou errada, em silêncio.

`extrair_demanda_origem` lê o metadado como `extrair_data_geracao` já lê a data, e a publicadora de
Demanda **recusa antes de qualquer escrita**, nomeando os dois valores, quando:

- o ID informado diverge do declarado no backlog;
- o backlog declara `Não se aplica` — esse backlog não nasceu de uma Demanda, e não é essa a
  publicadora dele.

Sem flag de sobreposição. Uma flag para forçar existiria para ser usada sob pressão, e o erro que ela
habilitaria é exatamente o que a checagem existe para impedir. Republicar sob outra Demanda é uma
decisão que passa por corrigir o documento.

### A publicadora solta não herda essa recusa

Simetria seria um bug aqui. O backlog de débitos declara Demanda de origem **e** publica solto de
propósito, pelo `Iteration Path`. Se a publicadora solta passasse a recusar backlog com Demanda
declarada, o fluxo de débitos deixaria de funcionar no dia em que fosse implementado.

## Compatibilidade

Um campo novo no item muda o hash do plano, e manifesto com hash divergente recusa retomar. Uma
publicação interrompida no meio exigiria reconciliação manual item a item.

**As chaves `tags`, `depende_de` e o ID declarado só entram no dict serializado por `_calcular_hash`
quando não são vazios.** Backlog sem tags e sem dependências produz exatamente o hash de hoje, e toda publicação
parcial em andamento retoma normalmente. A assimetria precisa de comentário no código explicando o
porquê — sem ele, alguém a "limpa" numa refatoração futura e quebra a retomada sem perceber.

A ordenação topológica estável tem a mesma propriedade, pelo mesmo motivo, e o teste que a protege é
o mesmo: um backlog sem os campos novos precisa produzir o hash anterior, byte a byte.

## Alcance da mudança

Tudo em `src/` sai em dobro: `publicar-backlog-azure-boards` e `publicar-backlog-demanda-azure-boards`
são gêmeos.

### Publicadoras (× 2)

| Arquivo | Mudança |
|---|---|
| `contrato_backlog.py` | `Tags`, `Depende de` e o ID existente em `SECTION_NAMES`; parsing com trim, dedup e as recusas de formato; validação de ciclo, chave inexistente, dependência para não-folha, ID em item de folha e ID sem ancestral declarado |
| `interpretar_markdown.py` | as três seções em `_SECOES`; `_converter_item` preenche os campos novos; `extrair_demanda_origem` ao lado de `extrair_data_geracao` |
| `modelos.py` | `ItemBacklog` e `OperacaoCriacao` ganham `tags: tuple[str, ...] = ()`, `depende_de: tuple[str, ...] = ()` e o ID existente — tuplas porque os dataclasses são `frozen` |
| `planejar_publicacao.py` | ordenação topológica estável substituindo o `sorted` atual; `_criar_operacao` propaga; `_calcular_hash` inclui `"tags"` e `"depende_de"` só quando não vazias, com comentário |
| `executar_publicacao.py` | resolve os IDs dos predecessores em `registros`, como já faz com `chave_pai`; pré-registra os IDs declarados e pula a criação desses itens |
| `manifesto.py` | registro distinguível para item pré-existente: nunca contado como criação nem elegível para reconciliação |
| `cliente_azure_devops.py` | `op: add` em `/fields/System.Tags` unido por `"; "`; uma relação `System.LinkTypes.Dependency-Reverse` por predecessor, ambos apenas quando há conteúdo |

### Skills

| Arquivo | Mudança |
|---|---|
| `gerar-backlog-azure-boards/references/backlog-markdown-contract.md` | seção `Tags`: formato, regras, posição no template, mapeamento para `System.Tags`. `Depende de` promovido de texto na `Description` a subseção estruturada, com o mapeamento para o link e a nota de que `Bloqueia` permanece documental |
| `gerar-backlog-azure-boards/scripts/validate_backlog.py` | as três seções em `SECTION_NAMES` e as validações correspondentes. É a **terceira cópia** da lógica de contrato e a única que o passo 10 do `SKILL.md` manda rodar: sem ela, o mesmo arquivo manda emitir os campos e, dez linhas abaixo, rodar o gate que os recusa |
| `gerar-backlog-azure-boards/SKILL.md` | reconhece `Spec: Débitos técnicos` como spec de entrada; emite todo o vocabulário nos itens de folha, incluindo `dn-<id>` em qualquer origem; serializa `Depende de` como subseção estruturada em vez de texto na `Description`; Epic/Feature por capacidade e sem tags |
| `especificar-debitos-tecnicos/SKILL.md` | `Faixa` como campo oficial; `## Fonte da Demanda`; nota da tag que envelhece |
| `especificar-telas-ux-ui/SKILL.md` | plataforma como campo estruturado por `TL-xx`, não só no cabeçalho e no título em prosa |

### Testes

- Parsing: tags ausentes, uma tag, várias, espaços em volta, repetidas, seção vazia, tag vazia entre
  vírgulas, `;` embutido.
- Concordância entre os dois parsers diante de `Tags`.
- Hash: backlog sem tags mantém o hash anterior (é o teste que protege a retomada); backlog com tags
  muda o hash.
- Payload: `System.Tags` ausente sem tags, presente e unido por `"; "` com tags.
- Ordenação: sem dependências, a sequência é idêntica à atual; com dependências, o predecessor
  precede o dependente, inclusive quando a chave do predecessor é maior.
- Recusas do planejador: ciclo (inclusive de três itens), chave inexistente, dependência para
  não-folha — cada erro nomeando as chaves.
- Link: a relação é `Dependency-Reverse` **no item dependente apontando para o predecessor**. O teste
  afirma a direção, não só a existência — uma inversão passa num teste que só conte relações.
- Predecessor criado em rodada anterior: o ID vem de `registros` e o link se forma na retomada.
- ID declarado: o item não é criado, os filhos penduram nele, o manifesto o marca como pré-existente
  e uma retomada não o recria nem o conta como criação.
- Recusas do ID declarado: em item de folha, sem ancestral declarado, apontando para work item
  inexistente, apontando para work item de outro tipo.
- `demanda_id` divergente recusa antes de qualquer escrita, nomeando os dois valores; backlog com
  `Não se aplica` recusa a publicadora de Demanda.
- **A publicadora solta aceita backlog com Demanda declarada** — é o teste que impede alguém de
  "corrigir" a assimetria e quebrar o fluxo de débitos.
- Validação estrutural agregando os erros novos junto dos existentes.

O vocabulário é regra de skill, não de código: nenhum teste do publicador conhece `debito-tecnico` ou
`design-ux-ui`. As skills de débitos e de telas têm suítes próprias em `tests/`, e é lá que a emissão
correta do vocabulário se verifica.

## Riscos conhecidos

**Achar o ID continua manual.** O publicador deixa de recriar a capacidade, mas quem monta o backlog
ainda precisa localizar o Epic no Boards e copiar o ID. Enquanto houver poucas capacidades publicadas
isso é aceitável; com dezenas, vira fonte de erro por digitação — mitigada pela conferência de
existência e tipo, não eliminada. Propor o ID durante a geração do backlog é o próximo passo natural.

**Backlogs antigos com `Depende de` em prosa.** O campo nasceu como texto dentro da `Description` e
continua válido ali — a subseção estruturada é opcional, e um backlog anterior não passa a ser
inválido. Mas ele também não ganha link: só a subseção gera relação. Nenhuma migração automática é
tentada, porque adivinhar chaves em prosa para criar relação no Boards erraria em silêncio.

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
| `dn-<id>` em todo item de Demanda | `dn-<id>` só no débito | a rastreabilidade por query vale para qualquer origem, não só para débito |
| Classificação do pedido fora do vocabulário | tag `defeito` / `melhoria` / `outro` | herdaria no item o metadado único da spec, e discordaria do tipo do work item |
| `dn-<id>` em vez de tag por spec | `spec-<slug>` por origem | vocabulário aberto, crescendo a cada spec |
| Plataforma como campo do `TL-xx` | derivar a plataforma do título em prosa | tag não pode depender de parsing de título |
| Link Predecessor/Sucessor no escopo | adiar como etapa futura | a tag seria paliativo que envelhece; o link é preciso e fecha junto com o item |
| Ordenação topológica estável | segunda passada de vinculação | evita uma operação que não é criação, que contaminaria manifesto, autorização e retomada |
| `Depende de` genérico entre folhas | restrito ao par design/funcional | o contrato define o mecanismo, a skill define quando emitir — como no campo `Tags` |
| `Bloqueia` permanece documental | publicar os dois sentidos | é a inversa do mesmo link; duplicaria a relação |
| Sem tag `depende-de-design` | link e tag juntos | o link já dá o sinal, aponta qual item bloqueia e não envelhece |
| ID existente declarado no documento | consulta automática ao Boards | o publicador obedece ao documento revisado em vez de adivinhar; e a busca por título é inviável pelo prefixo de data e chave |
| ID existente só em Epic e Feature | permitir também em folha | o caso de uso é reaproveitar contêiner de capacidade; em folha serviria para encobrir problema de manifesto |
| `demanda_id` divergente recusa | avisar, ou flag para forçar | pendurar épicos na Demanda errada é caro de desfazer, e a flag existiria para ser usada sob pressão |
| Publicadora solta sem essa recusa | aplicar a checagem nas duas | o backlog de débitos declara Demanda e publica solto de propósito |
