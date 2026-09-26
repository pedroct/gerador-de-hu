# Tarefa 10: skills de débitos, telas e geração de backlog — relatório

## Correção pós-revisão nº 2: violação de invariante de isolamento em pacote não tocado

A revisão rodou a suíte **raiz** do repositório (`uv run pytest -q` a partir da raiz do worktree, não
por pacote) e encontrou uma falha que as três suítes por pacote não detectam, porque o teste que
quebrou não mora em nenhum dos três arquivos que esta tarefa editou:

```
FAILED redigir-spec-pedido-negocio/tests/test_skill_integration.py::DraftingSkillIsolationTests::test_existing_skills_do_not_reference_drafting_skill
1 failed, 351 passed, 109 subtests passed
```

**Causa:** a seção nova `## Specs de entrada reconhecidas`, em `gerar-backlog-azure-boards/SKILL.md`,
citava `redigir-spec-pedido-negocio` como exemplo de skill de redação de spec comum. O pacote
`redigir-spec-pedido-negocio` tem um teste de isolamento deliberado
(`test_existing_skills_do_not_reference_drafting_skill`) que afirma que 3W, 3C, Gherkin e
`gerar-backlog-azure-boards` **nunca** referenciam essa skill por nome — é uma invariante de
arquitetura (a skill geradora de backlog não pode se acoplar a uma skill específica de redação), não
um teste frágil.

**Correção:** removi o nome `redigir-spec-pedido-negocio` da frase. Verifiquei que a invariante vale
só para essa skill — `redigir-spec-demanda-azure-boards` já é citada no próprio
`backlog-markdown-contract.md:232` e não tem essa restrição —, então mantive esse segundo exemplo e
troquei o primeiro por uma descrição de categoria em vez de nome literal:

- Antes: `` Uma spec de produto ou software comum, do fluxo usual (`redigir-spec-pedido-negocio`, `redigir-spec-demanda-azure-boards` ou equivalente). ``
- Depois: `` Uma spec de produto ou software do fluxo usual de requisitos (por exemplo `redigir-spec-demanda-azure-boards`, ou qualquer skill de redação equivalente). ``

Conferi que nenhuma outra menção a `redigir-spec-pedido-negocio` foi introduzida em
`gerar-backlog-azure-boards/` por esta tarefa (`grep -rn "redigir-spec-pedido-negocio"
gerar-backlog-azure-boards/` devolveu vazio depois da correção).

### Saída de `uv run pytest -q` **da raiz do worktree** — antes e depois

Antes (confirmando a falha apontada pela revisão):

```
FAILED redigir-spec-pedido-negocio/tests/test_skill_integration.py::DraftingSkillIsolationTests::test_existing_skills_do_not_reference_drafting_skill
1 failed, 351 passed, 109 subtests passed in 0.35s
```

Depois da correção:

```
...................................................................... [ 19%]
............................................................................................. [ 46%]
........................................................................ [ 66%]
........................................................................ [ 87%]
.............................................                                            [100%]
352 passed, 109 subtests passed in 0.32s
```

Reconferi também as três suítes por pacote, para garantir que os testes acrescentados nas duas
rodadas anteriores (incluindo o dedicado ao achado da conversão de `Faixa`) continuam passando:

```
cd gerar-backlog-azure-boards && uv run pytest -q
...................................................................    [100%]
67 passed, 2 subtests passed in 0.03s

cd especificar-debitos-tecnicos && uv run pytest -q
..................... [ 55%]
.................                                                        [100%]
38 passed, 51 subtests passed in 0.02s

cd especificar-telas-ux-ui && uv run pytest -q
..........................                                               [100%]
26 passed in 0.01s
```

### Lição registrada, como pedido pelo coordenador

Rodar a suíte dos pacotes que a tarefa edita **não é suficiente** para mudança de documentação. Esta
é a segunda tarefa seguida a quebrar teste fora dos pacotes editados: a Tarefa 9 quebrou o pacote
**dono** do arquivo editado (a mesma classe de risco que o brief desta tarefa já citava e que eu
verifiquei explicitamente nos três pacotes que toquei); a minha quebrou um **terceiro pacote**,
ligado ao texto novo só por uma invariante de isolamento que nada no arquivo editado menciona ou
sugere. Nenhuma leitura cuidadosa do `SKILL.md` que editei apontaria essa dependência — só a suíte
raiz do repositório a expõe, porque só ela varre todos os testes que fazem asserção sobre o conteúdo
de `gerar-backlog-azure-boards/SKILL.md`, vindos de pacotes que eu não tinha motivo para abrir.
**Daqui em diante, mudança de documentação roda a suíte raiz do repositório antes de declarar a tarefa
concluída** — os testes por pacote continuam úteis para iteração rápida durante a edição, mas não
substituem a rodada final na raiz.

---

## Correção pós-revisão nº 1: regra de conversão de `Faixa` para tag

A revisão apontou um achado **Importante** em `gerar-backlog-azure-boards/SKILL.md:47`: a regra
original ("copia a `Faixa` declarada no DT de origem, convertida para minúsculas e hífen") descrevia
uma transformação sobre o **texto de exibição** (`Restrição`, `Candidato`, `A confirmar`), mas os três
exemplos citados (`dt-restricao`, `dt-candidato`, `dt-a-confirmar`) só batem com essa regra para dois
dos três casos. Aplicar "minúsculas e hífen" a `Restrição` produz `dt-restrição` (cedilha e til), não
`dt-restricao` — o modo de falha silencioso que o brief descreve como risco central: a query por
`dt-restricao` no Azure Boards voltaria vazia, e nenhum teste acusaria, porque os outros dois valores
não têm acento e mascaram o problema.

**Correção aplicada** em `gerar-backlog-azure-boards/SKILL.md`: a regra agora parte explicitamente do
**retorno ASCII de `priorizacao.py::faixa()`** (`restricao`, `a_confirmar`, `candidato`), trocando `_`
por `-`, e diz explicitamente que a conversão **nunca** parte do texto de exibição da coluna `Faixa`
— citando o próprio contraexemplo (`Restrição` → `dt-restrição`, errado) para deixar o motivo
registrado, não só a regra corrigida. Acrescentei a tabela de mapeamento fixa exibição → retorno de
`faixa()` → tag, pedida como exemplo lado a lado pelo achado da revisão:

| Faixa (texto de exibição no DT) | Retorno de `faixa()` | Tag |
|---|---|---|
| Restrição | `restricao` | `dt-restricao` |
| Candidato | `candidato` | `dt-candidato` |
| A confirmar | `a_confirmar` | `dt-a-confirmar` |

### Asserção de teste ajustada por causa da correção

`test_emite_vocabulario_de_tags_por_origem_do_item` continha `self.assertIn("`dt-restricao`,
`dt-candidato` ou `dt-a-confirmar`", self.backlog)` — essa string contígua deixou de existir porque
os três valores passaram a viver em linhas separadas da tabela nova. Troquei por três `assertIn`
específicos, um por linha da tabela (`| Restrição | `restricao` | `dt-restricao` |` etc.), mantendo a
asserção tão específica quanto a anterior.

Acrescentei também um teste novo, dedicado ao achado da revisão —
`test_tag_de_faixa_parte_do_retorno_ascii_de_faixa_nao_do_texto_de_exibicao` —, que verifica: (1) a
frase "retorno ASCII de" está presente; (2) a frase que proíbe explicitamente derivar do texto de
exibição por minúsculas está presente; (3) `dt-restrição` (com cedilha) não aparece como entrada da
tabela de mapeamento (só pode aparecer dentro da prosa que explica o erro evitado). Na primeira
tentativa esse teste falhou porque o `assertNotIn` original checava a substring inteira `dt-restrição`
— que legitimamente aparece uma vez, dentro da própria explicação do contraexemplo. Corrigi o teste
para checar a ausência da entrada de tabela (`| `dt-restrição` |`) em vez da substring solta, e
afirmar positivamente que a frase do contraexemplo está presente.

### Saída de `uv run pytest -q` depois da correção

```
cd gerar-backlog-azure-boards && uv run pytest -q
...................................................................    [100%]
67 passed, 2 subtests passed in 0.03s

cd especificar-debitos-tecnicos && uv run pytest -q
..................... [ 55%]
.................                                                        [100%]
38 passed, 51 subtests passed in 0.02s

cd especificar-telas-ux-ui && uv run pytest -q
..........................                                               [100%]
26 passed in 0.01s
```

Nenhuma regressão nas outras duas suítes.

### Grep de grafia repetido depois da correção

```
grep -n "debito-tecnico\|design-ux-ui\|plataforma-\|dn-<id>\|dt-restricao\|dt-candidato\|dt-a-confirmar" \
  especificar-debitos-tecnicos/SKILL.md especificar-telas-ux-ui/SKILL.md gerar-backlog-azure-boards/SKILL.md \
  gerar-backlog-azure-boards/references/backlog-markdown-contract.md
```

```
gerar-backlog-azure-boards/SKILL.md:32: ...a tag `debito-tecnico` já dá a visão de débito...
gerar-backlog-azure-boards/SKILL.md:47:- **`debito-tecnico`** e **`dt-<faixa>`** ... nunca do texto de exibição `Faixa` do DT (`Restrição`, `Candidato`, `A confirmar`) passado por minúsculas: `Restrição` tem cedilha e til, e "minúsculas e hífen" sobre ele produziria `dt-restrição`, não `dt-restricao`. ...
gerar-backlog-azure-boards/SKILL.md:51:  | Restrição | `restricao` | `dt-restricao` |
gerar-backlog-azure-boards/SKILL.md:52:  | Candidato | `candidato` | `dt-candidato` |
gerar-backlog-azure-boards/SKILL.md:53:  | A confirmar | `a_confirmar` | `dt-a-confirmar` |
gerar-backlog-azure-boards/SKILL.md:54:- **`design-ux-ui`** e **`plataforma-web`** ou **`plataforma-mobile`** ...
gerar-backlog-azure-boards/SKILL.md:55:- **`dn-<id>`** ...
gerar-backlog-azure-boards/SKILL.md:57: ...`debito-tecnico`, `dt-<faixa>` **e** `dn-<id>` juntas.
gerar-backlog-azure-boards/references/backlog-markdown-contract.md:86:`debito-tecnico, dt-restricao`; ...
gerar-backlog-azure-boards/references/backlog-markdown-contract.md:135:[Se aplicável: ... `debito-tecnico, dt-restricao`]
especificar-telas-ux-ui/SKILL.md:242:para decidir a tag `plataforma-web`/`plataforma-mobile` de um item de design — só desta subseção.
```

Ainda sem divergência de grafia entre os pontos onde a mesma tag aparece mais de uma vez — a única
diferença em relação à conferência anterior é que a regra que produz `dt-restricao` agora está correta
por construção (parte do ASCII), não só coincidentemente certa nos exemplos citados.

## Achados Menores registrados pela revisão (não corrigidos, ficam para a triagem final)

- A célula-exemplo da coluna `Faixa` no `Resumo priorizado` de `especificar-debitos-tecnicos/SKILL.md`
  usa `\|` como separador enquanto a célula vizinha (`Tipo sugerido`) usa `/`.
- As adições em `especificar-debitos-tecnicos/SKILL.md` não ganharam teste novo, ao contrário das
  outras duas skills desta tarefa.

---


## O que foi documentado

### `especificar-debitos-tecnicos/SKILL.md`

- `Faixa` virou campo oficial: coluna nova no cabeçalho do `Resumo priorizado` e linha
  `- Faixa: <Restrição | Candidato | A confirmar>` na seção `### Priorização` do template de cada DT.
  Os três valores reproduzem a grafia já usada na tabela de `scripts/priorizacao.py::faixa()` que a
  própria skill já documentava na seção "Priorização assistida" (Restrição / A confirmar / Candidato,
  derivados dos retornos `restricao` / `a_confirmar` / `candidato` da função).
- Nova seção `## Fonte da Demanda` no template (logo após `## Contexto e origem`, antes do `Resumo
  priorizado`), com instrução de copiar a seção homônima da origem quando existir, `Não se aplica`
  caso contrário, e proibição explícita de derivar o ID do nome da pasta (`DN-14125-<slug>/` citado
  como exemplo do risco). Bullet espelhado em `## Limites`.
- Nota na seção "Priorização assistida" e bullet em `## Limites`: a tag `dt-<faixa>` publicada é
  fotografia da geração; uma reavaliação que mude a `Faixa` no documento não atualiza sozinha o work
  item já criado.
- Bullet novo em `## Limites`: mesmo quando esta spec declarar `## Fonte da Demanda`, a próxima etapa
  indicada é `publicar-backlog-azure-boards` (solta), nunca `publicar-backlog-demanda-azure-boards` —
  esta herdaria o `Iteration Path` da Demanda e o débito nasceria na sprint em que não será pago.

### `especificar-telas-ux-ui/SKILL.md`

- Nova subseção `### Plataforma` no template do item `TL-xx`, logo após o heading do item e antes de
  `### Por que esta tela existe`, com valor único `Web` ou `Mobile`.
- Parágrafo logo após o template explicando que essa subseção é o único campo estruturado de
  plataforma — cabeçalho do documento e título em prosa continuam existindo para quem lê, mas
  `gerar-backlog-azure-boards` nunca deve inferir a tag `plataforma-web`/`plataforma-mobile` por
  parsing de título ou cabeçalho.
- Testes novos em `tests/test_skill_integration.py`: `### Plataforma` acrescentada à lista de seções
  obrigatórias do template (`test_item_template_has_design_sections`) e um teste dedicado
  (`test_item_template_declares_platform_as_structured_field`) fixando a frase sobre não depender de
  parsing de título.

### `gerar-backlog-azure-boards/SKILL.md`

- Nova seção `## Specs de entrada reconhecidas` (após `## Resultado`, antes de `## Detecção do modo`):
  reconhece `Spec: Débitos técnicos — <contexto>` como spec de entrada válida quando é o documento
  passado diretamente à execução — preservando, na mesma seção, a regra intocada de que um
  `debitos-tecnicos.md` companheiro dentro da pasta de outra Demanda continua contexto rotulado.
- Passo 4 do Workflow ganhou a regra de hierarquia por capacidade: num backlog de débitos, Epic e
  Feature nomeiam a capacidade de produto afetada, nunca o débito ou sua categoria (decisão de
  2026-09-12, já registrada na memória do usuário).
- Passo 7 ganhou a regra dos critérios do DT: os bullets de `### Critérios de aceite` do DT viram
  contexto rotulado de entrada para a Conversation da 3C, nunca cópia direta para `Acceptance
  Criteria`; sem Gherkin derivado da Confirmation, `Acceptance Criteria` fica em branco (mesma regra
  geral do contrato para Confirmation `Ausente`/`Parcial`).
- Novo passo 13: mesmo com `Demanda de Negócio de origem` declarada, um backlog nascido de débitos
  indica `publicar-backlog-azure-boards` (solta) como próxima etapa, nunca a publicadora vinculada à
  Demanda — mesmo raciocínio de sprint que na skill de débitos.
- Nova seção `## Tags emitidas`, o único lugar do repositório que declara o vocabulário reservado de
  tags: `debito-tecnico` + `dt-<faixa>` (`dt-restricao`/`dt-candidato`/`dt-a-confirmar`) em item de DT;
  `design-ux-ui` + `plataforma-web`/`plataforma-mobile` em item de design; `dn-<id>` em todo item de
  folha nascido de uma Demanda. Epic e Feature nunca recebem tag — declarado nesta seção e reforçado
  em `## Boundaries`.
- Bullet de `## Boundaries` sobre `Depende de`/`Bloqueia` **reescrito** (ver seção de asserções
  alteradas abaixo): a versão antiga descrevia os dois campos como "informativo", o que ficou incorreto
  depois que a Tarefa 9 tornou `Depende de` gerador de link real (`System.LinkTypes.Dependency-
  Reverse`). A nova redação distingue os dois: `Depende de` é subseção estruturada que gera relação
  real na publicação; `Bloqueia` continua texto informativo em prosa, sem seção nem link.
- Bullet novo de `## Boundaries` reforçando que tags são string opaca para o publicador e que Epic/
  Feature nunca recebem tag.

## Asserção de teste alterada, e por quê

`gerar-backlog-azure-boards/tests/test_skill_integration.py`, método
`test_backlog_boundaries_mark_dependency_field_as_informative` → renomeado para
`test_backlog_boundaries_distinguish_dependency_link_from_informative_bloqueia`.

- **Texto antigo asserido:** `"O campo `Depende de`/`Bloqueia`, quando presente, é informativo"`.
- **Por que quebrou:** a Tarefa 9 reescreveu o contrato para que `Depende de` gere
  `System.LinkTypes.Dependency-Reverse` de verdade na publicação — só `Bloqueia` ficou puramente
  informativo. A frase antiga no `SKILL.md` já estava desatualizada em relação ao próprio contrato que
  ele cita (`references/backlog-markdown-contract.md#depende-de-e-bloqueia`); mantê-la geraria uma
  contradição documental permanente, não só uma falha de teste.
- **Nova asserção**, mantida específica (dois `assertIn` distintos, cada um citando o texto exato):
  - `"gera, na publicação, a relação real `System.LinkTypes.Dependency-Reverse`"` (cobre `Depende de`).
  - `` "`Bloqueia`, ao contrário, permanece texto informativo em prosa" `` (cobre `Bloqueia`).

Nenhuma outra asserção pré-existente, nas três suítes, precisou de ajuste — todas as demais passaram
sem alteração porque o conteúdo novo foi **acrescentado**, nunca substituiu texto que outro teste já
citava literalmente.

Testes novos que também travam o conteúdo desta tarefa (não substituem nada, só adicionam cobertura):
- `test_reconhece_spec_de_debitos_tecnicos_como_entrada_valida`
- `test_emite_vocabulario_de_tags_por_origem_do_item`
- `test_epico_e_feature_de_debito_nomeiam_capacidade_nao_o_debito`
- `test_criterios_do_dt_viram_contexto_da_conversation_nao_acceptance_criteria`
- `test_backlog_de_debito_indica_publicadora_solta_mesmo_com_demanda`
- (em `especificar-telas-ux-ui`) `test_item_template_declares_platform_as_structured_field`

## Saída das três suítes

```
cd especificar-debitos-tecnicos && uv run pytest -q
..................... [ 55%]
.................                                                        [100%]
38 passed, 51 subtests passed in 0.02s

cd especificar-telas-ux-ui && uv run pytest -q
..........................                                               [100%]
26 passed in 0.01s

cd gerar-backlog-azure-boards && uv run pytest -q
..................................................................     [100%]
66 passed, 2 subtests passed in 0.03s
```

Rodadas repetidas depois de cada bloco de edição (não só ao final) — nenhuma quebra durante o
processo, além da mudança de asserção documentada acima, que fiz de propósito antes de rodar de novo.

## Saída do grep de conferência de grafia

```
grep -n "debito-tecnico\|design-ux-ui\|plataforma-\|dn-<id>\|dt-restricao\|dt-candidato\|dt-a-confirmar" \
  especificar-debitos-tecnicos/SKILL.md especificar-telas-ux-ui/SKILL.md gerar-backlog-azure-boards/SKILL.md \
  gerar-backlog-azure-boards/references/backlog-markdown-contract.md
```

```
especificar-telas-ux-ui/SKILL.md:242:para decidir a tag `plataforma-web`/`plataforma-mobile` de um item de design — só desta subseção.
gerar-backlog-azure-boards/SKILL.md:32: ...a tag `debito-tecnico` já dá a visão de débito...
gerar-backlog-azure-boards/SKILL.md:47:- **`debito-tecnico`** e **`dt-<faixa>`** ... `dt-restricao`, `dt-candidato` ou `dt-a-confirmar` ...
gerar-backlog-azure-boards/SKILL.md:48:- **`design-ux-ui`** e **`plataforma-web`** ou **`plataforma-mobile`** ...
gerar-backlog-azure-boards/SKILL.md:49:- **`dn-<id>`** — em todo item de folha nascido de uma spec com `## Fonte da Demanda`...
gerar-backlog-azure-boards/SKILL.md:51:Um item de folha pode acumular mais de uma origem — ... `debito-tecnico`, `dt-<faixa>` **e** `dn-<id>` juntas.
gerar-backlog-azure-boards/references/backlog-markdown-contract.md:86:`debito-tecnico, dt-restricao`; espaços ao redor de cada tag são ignorados.
gerar-backlog-azure-boards/references/backlog-markdown-contract.md:135:[Se aplicável: lista separada por vírgula, por exemplo `debito-tecnico, dt-restricao`]
```

Leitura da saída: `debito-tecnico` e `dt-restricao` batem, grafia idêntica, entre o contrato (Tarefa 9,
onde já existiam como exemplo) e `gerar-backlog-azure-boards` (onde viraram regra de emissão). As
tags novas desta tarefa (`design-ux-ui`, `plataforma-web`, `plataforma-mobile`, `dn-<id>`,
`dt-candidato`, `dt-a-confirmar`) aparecem só em `gerar-backlog-azure-boards/SKILL.md`, que é o único
lugar do repositório autorizado a conhecer o vocabulário reservado (arquitetura descrita no brief: o
publicador trata tag como string opaca; as skills de origem — débitos e telas — não precisam declarar
o nome da tag, só o campo estruturado do qual ela deriva, `Faixa` e `### Plataforma`). Não há
divergência de grafia entre os pontos onde a mesma tag aparece mais de uma vez.

## Arquivos alterados

- `especificar-debitos-tecnicos/SKILL.md`
- `especificar-telas-ux-ui/SKILL.md`
- `especificar-telas-ux-ui/tests/test_skill_integration.py`
- `gerar-backlog-azure-boards/SKILL.md`
- `gerar-backlog-azure-boards/tests/test_skill_integration.py`

## Achados da autorrevisão

- Ao reler o `## Boundaries` de `gerar-backlog-azure-boards/SKILL.md` antes de escrever, encontrei uma
  inconsistência real deixada pela Tarefa 9: o bullet de `Depende de`/`Bloqueia` ainda descrevia os
  dois campos como "informativo", contradizendo o próprio contrato que a mesma skill cita
  (`Depende de` gera `System.LinkTypes.Dependency-Reverse`, não é meramente informativo). Corrigi e
  documentei a mudança de asserção acima — não fazia parte do escopo literal do brief, mas deixaria o
  `SKILL.md` contradizendo seu próprio contrato se eu não corrigisse.
- Conferi que a nova seção `## Specs de entrada reconhecidas` não altera nem duplica a frase testada
  literalmente por `test_companheiros_da_pasta_nao_viram_item_de_backlog` — copiei a frase exata do
  passo 2 para dentro da nova seção, sem reescrevê-la.
- Verifiquei o caminho relativo `../especificar-debitos-tecnicos/scripts/priorizacao.py` citado em
  `## Tags emitidas` a partir de `gerar-backlog-azure-boards/`: resolve para o arquivo real.
  `priorizacao.py::faixa()` foi lido antes de escrever qualquer coisa; os três retornos da função
  (`restricao`, `a_confirmar`, `candidato`) mapeiam para `dt-restricao`, `dt-a-confirmar`,
  `dt-candidato` por substituição mecânica de `_` por `-` — mesma grafia que o contrato já fixava
  para o primeiro caso (`dt-restricao`) desde a Tarefa 9.
- Nenhuma das três skills foi reescrita; todo conteúdo foi acrescentado nos pontos indicados pelo
  brief, seguindo a estrutura (headings, numeração de passo, estilo de lista) já existente em cada
  arquivo.
- Comprimento de linha: nenhum dos três `SKILL.md` seguia disciplina estrita de 100 colunas antes desta
  tarefa (`gerar-backlog-azure-boards/SKILL.md` já tinha parágrafos de passo com mais de 1000
  caracteres em linha única; `especificar-telas-ux-ui/SKILL.md` tinha linhas de até 579). As linhas que
  acrescentei ficaram no mesmo padrão de cada arquivo — só em `especificar-debitos-tecnicos/SKILL.md`,
  que já usava quebra por volta de ~100 colunas, mantive esse mesmo padrão (linhas nas minhas adições
  entre 101 e 106 caracteres, mesma faixa das linhas pré-existentes).

## Preocupações

- Nenhuma pendência bloqueante. O ponto que mais vale acompanhar: a correção do bullet `Depende de`/
  `Bloqueia` em `## Boundaries` não estava no escopo literal do brief da Tarefa 10 — decidi corrigi-la
  porque a frase antiga contradizia o contrato da própria Tarefa 9, e deixá-la incorreta pareceu pior
  do que ampliar levemente o escopo. Vale uma segunda leitura do controlador focada só nessa mudança,
  caso prefira reverter e tratar como item separado.
