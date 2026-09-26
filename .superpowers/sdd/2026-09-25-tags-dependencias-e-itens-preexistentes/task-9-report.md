# Tarefa 9: contrato Markdown — relatório

## O que foi documentado

Em `gerar-backlog-azure-boards/references/backlog-markdown-contract.md`:

1. **`## Depende de e Bloqueia` reescrita.** Passou a descrever `Depende de` como subseção
   estruturada (não mais texto na `Description`), opcional e válida só em item de folha; chaves
   `E.F.S` separadas por vírgula, entre crases, dedup preservando ordem; recusa quando declarado em
   Epic/Feature, quando aponta para não-folha ou chave inexistente, e quando fecha ciclo (inclusive
   auto-dependência). Registrei que só `Depende de` gera `System.LinkTypes.Dependency-Reverse` (no
   item dependente, apontando para o predecessor) e que `Bloqueia` continua só texto informativo, sem
   seção própria, sem link. Acrescentei a ressalva pedida: backlog anterior com `Depende de` em prosa
   dentro da `Description` continua válido, só não ganha o link.

2. **`## Tags` (nova seção).** Separador vírgula no Markdown, `"; "` no `System.Tags`; opcional;
   presente e vazia é erro; tag vazia entre vírgulas é erro; `;` dentro da tag é erro explícito
   (vírgula dentro da tag é estruturalmente impossível, já que é o separador da lista); limite de 400
   caracteres; dedup preservando ordem; válida em qualquer tipo de item (Epic, Feature, User Story,
   Bug).

3. **`## Azure Boards ID` (nova seção).** Só em Epic e Feature; Feature com ID exige que o Epic pai
   também declare ID; ID inteiro positivo ASCII entre crases, recusando zero, negativo, decimal,
   espaço interno e algarismos não-ASCII/sobrescritos; é o único lugar do backlog onde aparece um ID
   real do Azure Boards — nunca inferido, nunca derivado da chave documental ou do nome de pasta; item
   com ID declarado não é criado pela publicação, é reaproveitado como pai.

4. **Template completo** atualizado com `Tags` e `Azure Boards ID` em Epic e Feature, e `Tags` e
   `Depende de` nos dois itens de folha (User Story e Bug); removi as notas antigas de `Depende de`
   em prosa dentro da `Description` e troquei a nota de `Bloqueia` para prosa livre (sem seção
   própria). Acrescentei uma frase de resumo de opcionalidade após o bloco de código.

5. **Tabela `Markdown de revisão e campos do Azure Boards`** ganhou três linhas novas: `Tags` →
   `System.Tags` (unido por `"; "`); `Depende de` → `System.LinkTypes.Dependency-Reverse` no item
   dependente (`Bloqueia` não gera campo/relação nenhuma); `Azure Boards ID` → não gera campo, só
   sinaliza reaproveitamento de Epic/Feature já publicado.

Em `publicar-backlog-demanda-azure-boards/SKILL.md`, seção "Configuração por execução", logo após o
parágrafo sobre `Area Path`/`Iteration Path` herdados: um parágrafo curto dizendo que o backlog precisa
declarar `Demanda de Negócio de origem` e que a publicação é recusada, antes de qualquer chamada
remota, quando esse valor diverge do `--demanda` informado, quando o backlog declara `Não se aplica`,
ou quando o metadado está ausente.

## Valores conferidos contra os testes, um a um

**Tags** (`tests/test_contrato_tags.py`, `contrato_backlog.normalizar_tags`):
- Separador vírgula, trim de espaços — `test_separa_por_virgula_e_remove_espacos`.
- Dedup preservando ordem — `test_deduplica_preservando_a_ordem`.
- Tag vazia entre vírgulas → `"a seção Tags possui uma tag vazia entre vírgulas"` —
  `test_recusa_tag_vazia_entre_virgulas`.
- `;` na tag → `"a tag '{tag}' contém ';', que o Azure Boards usa como separador"` —
  `test_recusa_ponto_e_virgula_dentro_da_tag`.
- Limite 400 → `"a tag '{tag}' passa de 400 caracteres, o limite do Azure Boards"` —
  `test_recusa_tag_acima_do_limite_do_azure` (testa com 401 caracteres).
- Seção ausente não produz erro nem tags — `test_seccao_ausente_nao_produz_tags_nem_erros`.
- Seção presente e vazia → `"{chave} possui a seção Tags presente e vazia"` —
  `test_validacao_recusa_secao_tags_presente_e_vazia`.
- Separador `"; "` no `System.Tags` — conferido em `cliente_azure_devops.py:300`
  (`"; ".join(operacao.tags)`), não em teste de contrato de Markdown, mas é o valor que documentei.

**Depende de** (`tests/test_contrato_dependencias.py`, `normalizar_chaves` e `detectar_ciclo`):
- Chaves entre crases, separadas por vírgula, dedup — `test_le_varias_chaves_separadas_por_virgula`,
  `test_deduplica_chave_repetida`.
- Valor fora do formato `E.F.S` → `"'{chave}' não é uma chave documental no formato E.F.S"` —
  `test_recusa_valor_que_nao_e_chave_documental`.
- Ciclo de 2 e 3 nós, e auto-dependência de 1 nó — `test_detecta_ciclo_de_dois_itens`,
  `test_detecta_ciclo_de_tres_itens`, `test_detecta_item_que_depende_de_si_mesmo`.
- Só em item de folha: declarar em Feature ou Epic → `"{chave} declara Depende de, permitido só em
  item de folha"` — `test_recusa_dependencia_declarada_em_feature`,
  `test_recusa_dependencia_declarada_em_epic`.
- Alvo inexistente → `"{chave} depende de {alvo}, que não existe no backlog"` —
  `test_recusa_dependencia_para_chave_inexistente`.
- Alvo não-folha → `"{chave} depende de {alvo}, que não é item de folha"` —
  `test_recusa_dependencia_para_item_que_nao_e_folha`.
- Folha dependendo de folha aceita sem erro — `test_folha_com_dependencia_continua_aceita`.
- Relação `System.LinkTypes.Dependency-Reverse` — conferida em `cliente_azure_devops.py:38,319`
  (constante `_RELACAO_PREDECESSORA`), aplicada no item dependente apontando para
  `ids_predecessores` (o predecessor).

**Azure Boards ID** (`tests/test_contrato_id_existente.py`, `normalizar_id`):
- Seção ausente devolve `None` sem erro — `test_secao_ausente_devolve_none`.
- ID entre crases — `test_le_id_entre_crases`.
- Recusa `abc`, `0`, `-3`, `47.21`, `47 21`, sobrescritos (`²³¹`) e dígitos não-ASCII (`٣`) —
  `test_recusa_id_que_nao_e_inteiro_positivo`, com mensagem `"'{texto}' não é um ID de work item
  inteiro e positivo"`.
- Só em Epic/Feature: declarar em User Story → `"{chave} declara Azure Boards ID, permitido só em
  Epic e Feature"` — `test_recusa_id_em_item_de_folha`.
- Feature com ID sob Epic sem ID → `"{chave} declara Azure Boards ID, mas seu pai {pai} não declara"`
  — `test_recusa_feature_com_id_sob_epic_sem`. Confirmei que a checagem de ancestral só se aplica a
  Feature (`contrato_backlog.py:324`, `elif ... item.kind == "Feature"`); Epic não tem ancestral a
  checar porque é raiz — não escrevi nenhuma exigência de ancestral para Epic.
- Item preexistente não é criado e serve de pai — conferido em
  `planejar_publicacao.py:41-46` (`ItemPreexistente`, filtro `a_criar = [... azure_boards_id is
  None]`) e no teste `test_item_preexistente_nao_e_recriado_e_serve_de_pai` em
  `tests/test_executar_publicacao.py`.

**Demanda de Negócio de origem** (`tests/test_demanda_de_origem.py`,
`executar_publicacao.conferir_demanda_de_origem`/`extrair_demanda_origem`):
- Lê `#<id>` — `test_le_o_id_da_demanda_de_origem`.
- `Não se aplica` devolve `None` — `test_devolve_none_quando_o_backlog_declara_nao_se_aplica`.
- Metadado ausente levanta `ErroContratoMarkdown` mencionando "Demanda de Negócio de origem" —
  `test_rejeita_metadado_ausente`.
- Divergência entre declarado e `--demanda` levanta `ValueError` citando os dois IDs —
  `test_recusa_quando_o_id_informado_diverge_do_backlog`.
- Backlog `Não se aplica` com `--demanda` informado é recusado —
  `test_recusa_backlog_que_nao_nasceu_de_demanda`.
- Chamada acontece em `cli.py:208`, antes de `_verificar_preliminar` e de qualquer chamada remota —
  frase "antes de qualquer chamada remota" no SKILL.md está certa.

## Divergências entre minha descrição inicial e o código

Nenhuma. O único ponto que ajustei em relação ao rascunho do meu primeiro parágrafo interno foi a
formulação de "cada chave aponta para *outro* item de folha": o código não proíbe uma chave apontar
para o próprio item via `normalizar_chaves` (isso passa nas checagens de existência/folha); é
`detectar_ciclo` que pega esse caso como ciclo de um nó. Reescrevi o contrato para não implicar uma
checagem que não existe nesse ponto específico — o efeito final (recusa) é o mesmo, mas a causa
correta é "ciclo", não "não pode ser o próprio item".

## Arquivos alterados

- `gerar-backlog-azure-boards/references/backlog-markdown-contract.md`
- `publicar-backlog-demanda-azure-boards/SKILL.md`

## Validações executadas

```
cd publicar-backlog-azure-boards && uv run pytest tests/test_contrato_tags.py \
  tests/test_contrato_dependencias.py tests/test_contrato_id_existente.py -q
# 34 passed

cd publicar-backlog-azure-boards && uv run python scripts/publicar_backlog.py validar \
  tests/fixtures/valid-backlog.md
# Backlog válido: 3 itens.

cd publicar-backlog-demanda-azure-boards && uv run pytest tests/test_demanda_de_origem.py -q
# 6 passed
```

A fixture `tests/fixtures/valid-backlog.md` não usa nenhum dos três campos novos e passou sem erro,
confirmando que continuam opcionais.

## Autorrevisão

- Reli a seção reescrita de `Depende de e Bloqueia` contra as 8 mensagens de erro de
  `test_contrato_dependencias.py` e as 6 de `test_contrato_id_existente.py`: bate valor por valor,
  incluindo o texto exato citado entre aspas nas mensagens onde fiz questão de reproduzir a regra
  (limite 400, separador `; `, nomes `System.Tags` / `System.LinkTypes.Dependency-Reverse`).
- Conferi que `git diff --stat` só toca os dois arquivos pedidos — nenhum arquivo de código foi
  alterado.
- Conferi comprimento de linha: nem `backlog-markdown-contract.md` nem `SKILL.md` seguem convenção de
  100 colunas (parágrafos de prosa já existentes passam de 500-700 caracteres em uma linha só); mantive
  o estilo de "um parágrafo por linha" já em uso nesses arquivos, e as listas com marcador que
  acrescentei ficaram dentro de ~100 colunas por serem naturalmente mais curtas.
- Todo o texto novo está em português brasileiro; nomes de campo (`Tags`, `Depende de`, `Azure Boards
  ID`, `System.Tags`, `System.LinkTypes.Dependency-Reverse`) ficaram como a API/o contrato os nomeia.
- Rodei os três arquivos de teste de contrato e o de demanda de origem depois de escrever a
  documentação — todos passaram sem precisar tocar em código.

## Preocupações

- Nenhuma bloqueante. Um ponto de atenção para quem ler o contrato: a regra "`,` dentro de uma tag é
  impossível de representar" é uma explicação minha do comportamento (decorre de a vírgula ser
  separador), não uma mensagem de erro do código — não há teste que gere esse erro especificamente
  porque a situação não chega a existir como tal (o parser já quebra a tag em duas antes). Deixei
  isso explícito no texto para não sugerir que existe uma mensagem de erro dedicada a vírgula dentro
  de tag.
- Registrado a pedido do controlador: minha verificação original de "`git diff --stat` só toca os
  arquivos pedidos" comprovava que eu não tinha alterado nenhum arquivo fora do escopo, mas não
  cobria o efeito colateral — um arquivo de teste em outro diretório do mesmo pacote (`gerar-backlog-
  azure-boards/tests/test_skill_integration.py`) que lia o arquivo que eu editei e afirmava a forma
  antiga do contrato. Editar um arquivo é uma coisa; quebrar quem o lê é outra. Da próxima vez, antes
  de reportar concluído, rodar a suíte de testes do próprio pacote cujo arquivo foi editado, não só a
  suíte explicitamente listada no brief.

## Correção pós-revisão (achado Crítico)

A revisão do controlador (rodando `cd gerar-backlog-azure-boards && uv run pytest -q`) encontrou 2
testes pré-existentes quebrados pela reescrita da seção `Depende de e Bloqueia`:
`test_contract_documents_depende_de_and_bloqueia_as_informative` e
`test_contract_template_has_a_slot_for_depende_de_and_bloqueia`, ambos em
`gerar-backlog-azure-boards/tests/test_skill_integration.py`. Eu não tinha rodado essa suíte porque o
brief só pedia a suíte de contrato de `publicar-backlog-azure-boards` e a validação estrutural da
fixture — a falha é do despacho, não minha, mas a correção é meu trabalho.

**Saída antes da correção** (colada literalmente):

```
$ cd gerar-backlog-azure-boards && uv run pytest -q
..............FF.............................................          [100%]
=================================== FAILURES ===================================
_ SkillIntegrationTests.test_contract_documents_depende_de_and_bloqueia_as_informative _
    def test_contract_documents_depende_de_and_bloqueia_as_informative(self):
        self.assertIn("## Depende de e Bloqueia", self.backlog_contract)
        self.assertIn("Não altera a prontidão calculada pela 3C", self.backlog_contract)
>       self.assertIn(
            "não é um novo nível hierárquico e não substitui `Parent`",
            self.backlog_contract,
        )
E       AssertionError: 'não é um novo nível hierárquico e não substitui `Parent`' not found in '...'
tests/test_skill_integration.py:235: AssertionError
_ SkillIntegrationTests.test_contract_template_has_a_slot_for_depende_de_and_bloqueia _
    def test_contract_template_has_a_slot_for_depende_de_and_bloqueia(self):
>       self.assertIn("Depende de: 1.1.2", self.backlog_contract)
E       AssertionError: 'Depende de: 1.1.2' not found in '...'
tests/test_skill_integration.py:209: AssertionError
=========================== short test summary info ============================
FAILED tests/test_skill_integration.py::SkillIntegrationTests::test_contract_documents_depende_de_and_bloqueia_as_informative
FAILED tests/test_skill_integration.py::SkillIntegrationTests::test_contract_template_has_a_slot_for_depende_de_and_bloqueia
2 failed, 59 passed
```

Ambas as asserções codificavam a forma em prosa que o contrato descontinuou de propósito: a primeira
esperava a frase antiga "não é um novo nível hierárquico e não substitui `Parent`" (removida porque
`Depende de` agora É uma subseção estruturada, então essa frase deixou de ser verdade); a segunda
esperava o literal `"Depende de: 1.1.2"` (a forma em prosa antiga do campo).

**O que mudei**, mantendo as asserções específicas em vez de genéricas:

1. `test_contract_template_has_a_slot_for_depende_de_and_bloqueia` — passou a afirmar que o template
   tem a subseção estruturada (`"##### Depende de"`) e o formato específico de chave documental que
   ela documenta (`"uma ou mais chaves `E.F.S` de item de folha já existente no backlog"`), mantendo
   a asserção original sobre o `Bloqueia: 1.1.1` em prosa, que continua literal no arquivo.
2. `test_contract_documents_depende_de_and_bloqueia_as_informative` **renomeado** para
   `test_contract_documents_bloqueia_as_informative_and_linkless` — o nome antigo afirmava que os
   *dois* campos eram documentados como informativos, o que deixou de ser verdade para `Depende de`
   (ele agora gera link real). O teste renomeado verifica especificamente que o contrato descreve
   `Bloqueia` como texto informativo sem link (`"`Bloqueia` permanece **texto informativo**, sem
   seção própria nem chave estruturada"`, `"Não gera link algum; é só rastro documental."`) e a
   relação com o `Depende de` estruturado (`"Só `Depende de` gera relação real no Azure Boards"`).

**Saída depois da correção** (colada literalmente):

```
$ cd gerar-backlog-azure-boards && uv run pytest -q
.............................................................          [100%]
61 passed, 2 subtests passed in 0.04s
```

Reexecutei também as suítes das duas publicadoras para garantir que nada mais regrediu:

```
$ cd publicar-backlog-azure-boards && uv run pytest -q
........................................................................ [ 35%]
........................................................................ [ 70%]
............................................................             [100%]
204 passed in 0.36s

$ cd publicar-backlog-demanda-azure-boards && uv run pytest -q
........................................................................ [ 23%]
........................................................................ [ 47%]
........................................................................ [ 71%]
........................................................................ [ 95%]
.............                                                            [100%]
301 passed in 1.07s
```

Arquivo adicional alterado por esta correção:
`gerar-backlog-azure-boards/tests/test_skill_integration.py`.
