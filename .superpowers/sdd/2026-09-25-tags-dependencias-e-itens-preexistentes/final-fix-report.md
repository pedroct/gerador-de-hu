# Relatório da onda única de correção — revisão final

Branch: `tags-dependencias-itens-preexistentes`
Worktree: `/Volumes/DOCK/Projetos/pessoal/gerador-hu/.worktrees/tags-dependencias-itens-preexistentes`
Base desta onda: `09f2137`
Status: **DONE** — os sete itens da lista foram aplicados.

## Resumo de teste

Suíte raiz **antes** desta onda (`uv run pytest -q` na raiz do worktree):

```
...................................................................... [ 19%]
............................................................................................. [ 46%]
........................................................................ [ 66%]
........................................................................ [ 87%]
.............................................                                            [100%]
352 passed, 109 subtests passed in 0.35s
```

Suíte raiz **depois**:

```
...................................................................... [ 18%]
............................................................. [ 35%]
................................ [ 43%]
........................................................................ [ 63%]
........................................................................ [ 82%]
.................................................................                        [100%]
372 passed, 109 subtests passed in 0.35s
```

Suítes dos dois pacotes publicadores (não estão em `testpaths` da raiz):

```
$ cd publicar-backlog-azure-boards && uv run pytest -q
........................................................................ [ 34%]
........................................................................ [ 68%]
.................................................................        [100%]
209 passed in 0.35s
```

```
$ cd publicar-backlog-demanda-azure-boards && uv run pytest -q
........................................................................ [ 47%]
........................................................................ [ 70%]
........................................................................ [ 94%]
..................                                                       [100%]
306 passed in 1.08s
```

Portões estáticos na raiz:

```
$ uv run ruff check .
All checks passed!
$ uv run ruff format --check .
105 files already formatted
$ uv run mypy
Success: no issues found in 15 source files
```

`HASH_ANTES_DOS_CAMPOS_NOVOS` **não foi tocado** em nenhum dos dois pacotes (confirmado por
`git diff main...HEAD` — o literal só aparece como adição do branch, nunca desta onda) e o guarda
continua verde:

```
$ cd publicar-backlog-azure-boards && uv run pytest -q tests/test_planejar_publicacao.py -k "nao_muda" -v
tests/test_planejar_publicacao.py ..                                     [100%]
======================= 2 passed, 18 deselected in 0.06s =======================
```

## Commits desta onda

| Commit | Itens |
|---|---|
| `2bac182` `fix: porta Tags, Depende de e Azure Boards ID para o gate canonico` | 1, 2, 3 (código) |
| `16b30b9` `test: torna viva a asserção de predecessor no teste ponta a ponta` | 4 |
| `551c596` `docs: guardas da skill de debitos e correcoes de comentario e contrato` | 3 (contrato), 5, 6, 7 |

---

## Item 1 — CRÍTICO: o validador canônico recusava os campos novos

### O que fiz

Em vez de portar as regras à mão para `gerar-backlog-azure-boards/scripts/validate_backlog.py`,
reescrevi o arquivo como **espelho mecânico** do corpo de `contrato_backlog.py` mais o CLI próprio:

- cabeçalho: docstring explicando que esta é a cópia canônica, `from __future__`, imports
  (`argparse`, `re`, `sys`, `Sequence`, `dataclass`/`field`, `Path`);
- `# --- início do trecho espelhado de contrato_backlog.py ---` … 383 linhas copiadas verbatim do
  corpo de `contrato_backlog.py` (tudo a partir de `ITEM_RE = re.compile(`) … `# --- fim ... ---`;
- `main()` com `--update`, as três saídas (`0`/`1`/`2`) e a mensagem
  `A estrutura do backlog é válida`, inalteradas.

Assim entram não só os três nomes em `SECTION_NAMES`, mas `normalizar_tags`, `normalizar_chaves`,
`normalizar_id`, `detectar_ciclo`, as regras dentro de `_validate_item` (ciclo, chave inexistente,
`Depende de` fora de folha e apontando para não-folha, `Azure Boards ID` em folha, ancestral não
declarado) e também a normalização de `Implementation Evidence <sufixo>` em `_section_heading`, que
esta cópia **também** não tinha (divergência anterior a este branch — ver "Achados" abaixo).

### Evidência: antes × depois, lado a lado

Comparação do módulo em `09f2137` (ANTES) com o atual (AGORA) sobre os mesmos documentos usados nos
casos novos de teste:

```
--- Tags na folha
  ANTES: ['1.1.1 esperava o pai 1.1.0, recebeu 1.1.0`\n##### Tags\ndebito-tecnico, dt-restricao']
  AGORA: []
--- Tags com ';' embutido
  ANTES: ['1.1.1 esperava o pai 1.1.0, recebeu 1.1.0`\n##### Tags\ndebito-tecnico; dt-restricao']
  AGORA: ["1.1.1: a tag 'debito-tecnico; dt-restricao' contém ';', que o Azure Boards usa como separador"]
--- Depende de entre folhas irmas
  ANTES: ['1.1.1 esperava o pai 1.1.0, recebeu 1.1.0`\n##### Depende de\n`1.1.2']
  AGORA: []
--- Depende de para chave inexistente
  ANTES: ['1.1.1 esperava o pai 1.1.0, recebeu 1.1.0`\n##### Depende de\n`9.9.9']
  AGORA: ['1.1.1 depende de 9.9.9, que não existe no backlog']
--- Depende de para nao-folha
  ANTES: ['1.1.1 esperava o pai 1.1.0, recebeu 1.1.0`\n##### Depende de\n`1.1.0']
  AGORA: ['1.1.1 depende de 1.1.0, que não é item de folha']
--- ciclo 1.1.1 <-> 1.1.2
  ANTES: ['1.1.1 esperava o pai 1.1.0, recebeu 1.1.0`\n##### Depende de\n`1.1.2', '1.1.2 esperava o pai 1.1.0, recebeu 1.1.0`\n##### Depende de\n`1.1.1']
  AGORA: ['ciclo de dependência entre 1.1.1 → 1.1.2']
--- Azure Boards ID em Epic e Feature
  ANTES: ['1.1.0 esperava o pai 1.0.0, recebeu 1.0.0`\n#### Azure Boards ID\n`4722']
  AGORA: []
--- Azure Boards ID em folha
  ANTES: ['1.1.1 esperava o pai 1.1.0, recebeu 1.1.0`\n##### Azure Boards ID\n`4723']
  AGORA: ['1.1.1 declara Azure Boards ID, permitido só em Epic e Feature']
--- Feature com ID sob Epic sem ID
  ANTES: ['1.1.0 esperava o pai 1.0.0, recebeu 1.0.0`\n#### Azure Boards ID\n`4722']
  AGORA: ['1.1.0 declara Azure Boards ID, mas seu pai 1.0.0 não declara']
```

O `esperava o pai … recebeu 1.1.0`\n##### Tags\n…` é literalmente a armadilha descrita no briefing: o
gate acusava uma **violação de hierarquia inexistente**, e a leitura natural de "corrija violações
estruturais" é apagar a seção nova.

### Segundo modo de falha, mais silencioso (achado durante a verificação)

O gate antigo **nem sempre recusava**. Quando a seção nova não vem logo depois de `Parent`, o
conteúdo era engolido pela seção anterior sem erro algum. Medido sobre a fixture do publicador (que
tem `Título curto` entre `Parent` e `Depende de`), com o módulo de `09f2137`:

```
erros ANTES na fixture com Depende de: []
secoes lidas ANTES em 1.1.1: ['Acceptance Criteria', 'Description', 'Parent', 'Título curto']
Titulo curto ANTES: 'Reabertura no prazo\n\n##### Depende de\n`1.1.2`'
```

Ou seja: `Depende de` desaparecia dentro de `Título curto` e o gate dizia "estrutura válida". Isso
reforça a decisão de não parar no `SECTION_NAMES`: aceitar sem validar era exatamente o que acontecia
em metade dos casos.

Depois da correção, o gate aceita as três fixtures, inclusive as duas que agora carregam
`Depende de`:

```
$ cd gerar-backlog-azure-boards
$ uv run python scripts/validate_backlog.py tests/fixtures/valid-backlog.md
A estrutura do backlog é válida
rc=0
$ uv run python scripts/validate_backlog.py ../publicar-backlog-azure-boards/tests/fixtures/valid-backlog.md
A estrutura do backlog é válida
rc=0
$ uv run python scripts/validate_backlog.py ../publicar-backlog-demanda-azure-boards/tests/fixtures/valid-backlog.md
A estrutura do backlog é válida
rc=0
```

### Testes acrescentados a `gerar-backlog-azure-boards/tests/test_validate_backlog.py`

Quatro ajudantes de montagem (`_com_tags`, `_com_depende_de`, `_com_id_no_epic`,
`_com_id_na_feature`) e catorze casos — ao menos um feliz e uma recusa por campo:

- Tags: aceita na folha; recusa `;` embutido; recusa seção presente e vazia.
- Depende de: aceita entre folhas irmãs; recusa chave inexistente, alvo não-folha, declaração fora de
  folha, seção vazia e ciclo.
- Azure Boards ID: aceita em Epic + Feature; recusa em folha, Feature sem ID no Epic pai, valor não
  inteiro positivo (`0`) e seção vazia.

```
$ uv run pytest -q gerar-backlog-azure-boards/tests/test_validate_backlog.py
..............................................                         [100%]
46 passed, 2 subtests passed in 0.02s
```

(eram 32 casos + 2 subtests antes)

### Decisão sobre o teste comparando as três cópias

**Fiz** — e barato, porque a reescrita mecânica criou uma fronteira exata para comparar.
`tests/test_sincronia_do_contrato.py` (raiz, fora de qualquer skill, portanto sem acoplar skill
irmã no pacote instalável) faz duas afirmações:

1. o validador canônico delimita o trecho espelhado (os dois marcadores existem);
2. o trecho entre os marcadores é **byte a byte** igual ao corpo de `contrato_backlog.py` a partir de
   `ITEM_RE = re.compile(`.

Por que assim e não de outra forma:

- **Comparar só os três `SECTION_NAMES`** teria passado por acaso se alguém acrescentasse o nome sem
  a validação — que é precisamente o modo de falha que o briefing manda evitar.
- **Byte a byte das três cópias inteiras** não é possível: os arquivos têm docstring, imports e (no
  validador) um CLI diferentes por construção. A comparação da região compartilhada é o máximo que
  se pode exigir sem inventar uma quarta cópia.
- A terceira aresta (solta ↔ Demanda) já é medida por
  `publicar-backlog-demanda-azure-boards/tests/test_sincronia_com_origem.py`; juntas, as duas fecham
  o triângulo. O novo teste não a duplica.

```
$ uv run pytest -q tests/test_sincronia_do_contrato.py
..                                                                       [100%]
2 passed in 0.01s
```

---

## Item 2 — `_SECOES` amarrado a `SECTION_NAMES`

`interpretar_markdown._SECOES` deixou de repetir os oito nomes como literais e passou a ser
`SECTION_NAMES` (com comentário explicando o modo de falha assimétrico dos dois parsers). Aproveitei
para trocar os literais restantes pelas constantes importadas do mesmo módulo: `TAGS`, `DEPENDE_DE`,
`AZURE_BOARDS_ID` e `IMPLEMENTATION_EVIDENCE` — isso fecha o Menor que estava diferido.

Testes novos em `test_interpretar_markdown.py` (nos dois pacotes):

- `test_le_depende_de_declarado_no_item` — lê `Depende de` de Markdown real por `interpretar_backlog`
  e afirma `("1.1.2",)` no dependente e `()` no predecessor;
- `test_le_azure_boards_id_declarado_no_item` — `4721` no Epic, `None` na Feature;
- `test_as_secoes_reconhecidas_sao_as_do_contrato` — `_SECOES == SECTION_NAMES`.

Antes, `Depende de` e `Azure Boards ID` só apareciam como Markdown em testes que importam de
`contrato_backlog`; nenhum teste os lia pelo caminho de `interpretar_backlog`.

---

## Item 3 — "presente e vazia é erro" para os três campos

`contrato_backlog._validate_item` ganhou as duas checagens que faltavam, com a mesma redação já usada
para `Tags` e a mesma de `interpretar_markdown` (as mensagens são idênticas nos dois caminhos).
Medição depois da correção, reproduzindo a tabela do briefing:

```
Tags vazia               validate_backlog -> ['1.1.1 possui a seção Tags presente e vazia']
Depende de vazia         validate_backlog -> ['1.1.1 possui a seção Depende de presente e vazia']
Azure Boards ID vazia    validate_backlog -> ['1.0.0 possui a seção Azure Boards ID presente e vazia']
```

Testes: `test_recusa_secao_depende_de_presente_e_vazia` em `test_contrato_dependencias.py` e
`test_recusa_secao_azure_boards_id_presente_e_vazia` em `test_contrato_id_existente.py`, nos dois
pacotes; mais os dois casos equivalentes no gate canônico (item 1).

Documentação: a regra entrou nas seções `Depende de e Bloqueia` e `Azure Boards ID` de
`backlog-markdown-contract.md`, com a mesma forma do bullet que a seção `Tags` já tinha.

---

## Item 4 — asserção morta em `test_integracao_final.py`

A fixture `valid-backlog.md` dos **dois** pacotes ganhou:

- `##### Depende de` / `` `1.1.2` `` em `1.1.1`, entre `Título curto` e `Description` (posição do
  template do contrato);
- um segundo item de folha `1.1.2 [User Story] Desenhar a tela de reabertura` (o item de design), com
  `Parent`, `Título curto`, `Description` com Card/Conversation e `Origem na spec`, e
  `Acceptance Criteria` em bloco gherkin.

Isso torna a asserção viva e, de quebra, faz a fixture atravessar `_SECOES` com a seção nova **e**
exercitar a ordenação topológica: o predecessor `1.1.2` é criado antes do dependente `1.1.1`, apesar
da chave maior.

### Prova de que a asserção ficou viva (mutação)

Troquei `ids_predecessores = tuple(...)` por `()` em `executar_publicacao.py`:

```
tests/test_integracao_final.py:181: AssertionError
=========================== short test summary info ============================
FAILED tests/test_integracao_final.py::test_publicacao_pela_cli_aceita_confirmacao_apos_nova_tentativa
FAILED tests/test_integracao_final.py::test_publicacao_pela_cli_cria_itens_em_ordem_e_grava_manifesto_no_caminho_informado
FAILED tests/test_integracao_final.py::test_publicadora_solta_publica_backlog_com_demanda_de_origem_declarada
3 failed, 2 passed in 0.28s
```

A mutação foi revertida (`git checkout --`) e a suíte voltou verde antes do commit.

### Regressões encontradas e resolvidas (a fixture é usada por outros testes)

Seis testes falharam pela fixture maior; nenhum era falha real, todos eram contagem ou ordem:

- `test_configuracao_projeto::test_entry_point_instalado_chama_cli_real` — `3 itens.` → `4 itens.`
  (nos dois pacotes).
- `test_interpretar_markdown::test_interpreta_epic_feature_e_historia` — lista esperada ganhou
  `("1.1.2", "User Story")`.
- `test_integracao_final` — `chaves_criadas` passou a `["1.0.0", "1.1.0", "1.1.2", "1.1.1"]` (3
  ocorrências na solta, 2 na de Demanda).
- `test_skill_integration::test_validar_apenas_...` — quatro `POST validateOnly` em vez de três.
- `test_integracao_final` (Demanda) — `sorted(manifesto.itens)` ganhou `"1.1.2"`.
- `test_integracao_final` — `list(ler_manifesto(...).itens) == cliente.chaves_criadas` deixou de
  valer: o manifesto é gravado com `sort_keys=True`, então a ordem das chaves nele é **lexicográfica**
  e não topológica. Virou comparação de conjuntos, com comentário explicando por quê; a ordem de
  criação continua afirmada na linha acima.

Além disso, dois testes liam `interpretar_backlog(...)[-1]` da fixture
(`test_evidencia_de_implementacao_nao_faz_parte_da_descricao` e
`test_card_e_conversation_sao_normalizados_para_heading_proeminente`). Com duas folhas, `[-1]`
passaria a apontar para `1.1.2` e o primeiro viraria asserção vazia (só `1.1.1` tem
`Implementation Evidence`). Os dois passaram a buscar `1.1.1` pela chave, via um ajudante
`_historia_da_fixture()`. **Estes dois não falharam** — passariam vazios, que é pior; achei durante a
inspeção.

---

## Item 5 — assimetria de guarda na skill de débitos

Quatro guardas em `especificar-debitos-tecnicos/tests/test_skill_integration.py`, uma por adição,
seguindo o padrão das outras duas skills (um `assertIn` por teste, docstring dizendo o que quebra se
o texto sair):

- `test_resumo_priorizado_declara_a_coluna_faixa` → `"| Prioridade | Faixa |"` (contrato estrutural
  do qual `gerar-backlog-azure-boards` depende para emitir `dt-<faixa>`);
- `test_declara_a_secao_fonte_da_demanda` → `"## Fonte da Demanda"`;
- `test_registra_que_a_faixa_e_fotografia_da_geracao` →
  `"fotografia da geração, não obrigação recalculável"`;
- `test_indica_a_publicadora_solta_para_o_backlog_de_debitos` →
  `"(a publicadora solta) como próxima etapa manual"`.

```
$ uv run pytest -q especificar-debitos-tecnicos/tests/test_skill_integration.py
..........                                                               [100%]
10 passed in 0.01s
```

(eram 6)

---

## Item 6 — quatro (na prática cinco) correções pequenas

1. **Contrato** — `backlog-markdown-contract.md`, seção `Azure Boards ID`: bullet dizendo que as
   `Tags` de um item reaproveitado **não são publicadas**, que o work item existente permanece com as
   tags que já tinha, e que as tags declaradas **ainda entram no hash do plano** — então mudá-las
   invalida a retomada de uma publicação parcial sem mudar nada no board. Verifiquei os dois lados no
   código antes de escrever: `criar_plano` passa `itens_ordenados` (que inclui os pré-existentes) a
   `_calcular_hash`, e `a_criar` filtra `azure_boards_id is None`, então nenhuma `OperacaoCriacao` —
   e portanto nenhum `System.Tags` — é gerada para eles.
2. **`publicar-backlog-demanda-azure-boards/cli.py`** — o comentário dizia "antes de qualquer chamada
   remota", falso porque `ler_demanda` já fez um GET. Agora diz "antes de qualquer escrita e antes de
   pedir autorização", e explicita que não é "antes de qualquer chamada remota", nomeando o GET.
3. **`cliente_azure_devops.validar_operacao`** (ambos) — três linhas na docstring explicando que o
   `validateOnly` não exercita `System.LinkTypes.Dependency-Reverse`, porque na primeira rodada o
   predecessor ainda não tem ID e a relação nem entra no payload validado; erro de link só aparece na
   criação real.
4. **`executar_publicacao.extrair_demanda_origem`** (Demanda) — a docstring dizia que lê da seção de
   Metadados; o regex é `re.MULTILINE` sobre o documento inteiro e casa a primeira linha
   `- Demanda de Negócio de origem: ...` onde quer que esteja. A docstring agora descreve isso e diz
   que funciona porque os Metadados vêm primeiro, sem afirmar que a seção é verificada.
5. **`executar_publicacao.py`** (ambos) — comentário de cinco linhas antes do laço de predecessores
   explicando que as duas checagens são puras, que qualquer uma interrompe antes de qualquer escrita,
   que a ordem só decide qual mensagem o usuário vê, e que um teste depende dela — é o tipo de
   reordenação que parece inofensiva.

---

## Item 7 — a spec omitia um arquivo

Linha acrescentada à tabela "Alcance da mudança → Skills" de
`docs/superpowers/specs/2026-09-25-tags-de-debito-tecnico-no-backlog-design.md`, logo após a do
contrato de referência:

```
| `gerar-backlog-azure-boards/scripts/validate_backlog.py` | as três seções em `SECTION_NAMES` e as validações correspondentes. É a **terceira cópia** da lógica de contrato e a única que o passo 10 do `SKILL.md` manda rodar: sem ela, o mesmo arquivo manda emitir os campos e, dez linhas abaixo, rodar o gate que os recusa |
```

---

## Achados e observações — nada que eu tenha julgado errado na lista

Nenhum item da lista me pareceu errado ao olhar o código. Três observações que não mudam o que fiz,
mas que registro para a decisão do controlador:

1. **O gate antigo tinha dois modos de falha, não um.** O briefing descreve a recusa; medi também o
   modo silencioso (seção engolida pela anterior, "estrutura válida"). O modo que aparece depende de
   qual seção vem imediatamente antes da nova. Isso só fortalece a conclusão: acrescentar nomes sem
   validação deixaria o modo silencioso intacto para os três campos.

2. **Espelhei a normalização de `Implementation Evidence` de passagem.** `validate_backlog.py` também
   não tinha o tratamento de `Implementation Evidence <sufixo>` de `_section_heading` — divergência
   **anterior** a este branch, sem relação com os três campos novos. Como decidi fazer do arquivo um
   espelho mecânico (a única forma de garantir que ele não volte a ficar atrás), o tratamento entrou
   junto. Efeito prático: o gate canônico passa a terminar a `Description` no fim da Conversation, em
   vez de anexar o texto de evidência nela — o mesmo que os dois publicadores já faziam. Nenhum teste
   existente mudou de resultado. Se preferir isolar essa mudança num commit próprio, é fácil, mas
   desfazê-la reabriria a divergência que o novo teste de sincronia existe para fechar.

3. **`converter_para_html.py` e `validacao_estrutural.py` foram reescritos pelo espelhamento** (mesmo
   conteúdo: a substituição mecânica é idempotente para eles). Só `contrato_backlog.py` e
   `interpretar_markdown.py` mudaram de fato; `git diff` confirma.

## Preocupações

- **A fixture ponta a ponta ficou mais rica, e mais testes dependem da sua forma.** Seis asserções
  de contagem/ordem tiveram de acompanhar. Quem mexer nela de novo vai pagar o mesmo pedágio. A
  alternativa (montar o backlog com dependência em `tmp_path`, como o teste da Demanda declarada já
  faz) deixaria as outras asserções em paz, mas não faria a fixture atravessar `_SECOES` — segui a
  instrução do briefing e registro o custo.
- **`tests/test_sincronia_do_contrato.py` depende de dois marcadores de comentário.** É a mesma
  fragilidade de qualquer delimitador textual: apagar o marcador faz o primeiro teste falhar (por
  isso ele existe separado), não passar em silêncio.
- **Nada verifica que `_SECOES`/`SECTION_NAMES` e o vocabulário emitido pelas skills concordam.** As
  skills decidem as tags, o publicador as trata como string opaca — correto por desenho. Mas se
  `gerar-backlog-azure-boards` passar a emitir uma **seção** nova, nada avisa. Fora do escopo desta
  onda; anoto como candidato a débito.

## Arquivos alterados nesta onda

```
 docs/superpowers/specs/2026-09-25-tags-de-debito-tecnico-no-backlog-design.md |   1 +
 especificar-debitos-tecnicos/tests/test_skill_integration.py                  |  21 +++
 gerar-backlog-azure-boards/references/backlog-markdown-contract.md            |   7 +
 gerar-backlog-azure-boards/scripts/validate_backlog.py                        | 189 ++++++++++-
 gerar-backlog-azure-boards/tests/test_validate_backlog.py                     | 127 ++++++++
 publicar-backlog-azure-boards/src/.../cliente_azure_devops.py                 |   7 +-
 publicar-backlog-azure-boards/src/.../contrato_backlog.py                     |   4 +
 publicar-backlog-azure-boards/src/.../executar_publicacao.py                  |   5 +
 publicar-backlog-azure-boards/src/.../interpretar_markdown.py                 |  44 +--
 publicar-backlog-azure-boards/tests/fixtures/valid-backlog.md                 |  31 ++
 publicar-backlog-azure-boards/tests/test_configuracao_projeto.py              |   2 +-
 publicar-backlog-azure-boards/tests/test_contrato_dependencias.py             |   8 +
 publicar-backlog-azure-boards/tests/test_contrato_id_existente.py             |  11 ++
 publicar-backlog-azure-boards/tests/test_integracao_final.py                  |  10 +-
 publicar-backlog-azure-boards/tests/test_interpretar_markdown.py              |  88 ++++-
 publicar-backlog-azure-boards/tests/test_skill_integration.py                 |   1 +
 publicar-backlog-demanda-azure-boards/src/.../cli.py                          |   6 +-
 publicar-backlog-demanda-azure-boards/src/.../cliente_azure_devops.py         |   4 +
 publicar-backlog-demanda-azure-boards/src/.../contrato_backlog.py             |   4 +
 publicar-backlog-demanda-azure-boards/src/.../executar_publicacao.py          |  12 +-
 publicar-backlog-demanda-azure-boards/src/.../interpretar_markdown.py         |  44 +--
 publicar-backlog-demanda-azure-boards/tests/fixtures/valid-backlog.md         |  31 ++
 publicar-backlog-demanda-azure-boards/tests/test_configuracao_projeto.py      |   2 +-
 publicar-backlog-demanda-azure-boards/tests/test_contrato_dependencias.py     |   8 +
 publicar-backlog-demanda-azure-boards/tests/test_contrato_id_existente.py     |  11 ++
 publicar-backlog-demanda-azure-boards/tests/test_integracao_final.py          |  10 +-
 publicar-backlog-demanda-azure-boards/tests/test_interpretar_markdown.py      |  88 ++++-
 publicar-backlog-demanda-azure-boards/tests/test_skill_integration.py         |   1 +
 tests/test_sincronia_do_contrato.py                                           |  56 +++
 29 files changed, 770 insertions(+), 63 deletions(-)
```

Os dois módulos espelhados foram gerados por substituição mecânica de `publicar_backlog_azure_boards`
→ `publicar_backlog_demanda_azure_boards`, nunca editados à mão, e
`test_sincronia_com_origem.py` confirma os quatro arquivos byte a byte (parte dos 306 testes verdes
do pacote de Demanda).
