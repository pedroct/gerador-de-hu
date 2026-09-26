# Relatório — Tarefa 6: `Azure Boards ID` — leitura e recusas

## Correção pós-revisão: `normalizar_id` estourava `ValueError` cru em entrada Unicode

O revisor encontrou, e o coordenador confirmou contra o pacote instalado, que
`normalizar_id` usava só `texto.isdigit()` como guarda antes de chamar `int(texto)`.
`str.isdigit()` aceita caracteres da categoria Unicode "No" (número, não dígito decimal), como os
sobrescritos `²³¹`, para os quais `int()` estoura `ValueError` cru — violando a própria promessa da
docstring. Também aceita dígitos não-ASCII (ex.: `٣`, dígito árabe-índico), que `int()` converteria
silenciosamente para outro valor, arriscando pendurar filhos no work item errado.

Decisão do coordenador sobre a forma da correção: usar `texto.isascii() and texto.isdigit()`
(em vez de `isdecimal()`, sugestão original do revisor), por consistência com o guard-rail já
existente em `publicar-backlog-demanda-azure-boards/src/publicar_backlog_demanda_azure_boards/configuracao.py:165`
para o `demanda_id`, e por ser mais estrito (recusa também dígitos árabe-índicos, que `isdecimal()`
aceitaria).

### RED — teste novo falhando antes da correção

```
$ cd publicar-backlog-azure-boards && uv run pytest "tests/test_contrato_id_existente.py::test_recusa_id_que_nao_e_inteiro_positivo" -v
bruto = '`²³¹`'
    def normalizar_id(bruto: str) -> tuple[int | None, list[str]]:
        ...
        texto = bruto.strip().strip("`").strip()
        if not texto:
            return None, []
>       if not texto.isdigit() or int(texto) <= 0:
                                  ^^^^^^^^^^
E       ValueError: invalid literal for int() with base 10: '²³¹'
src/publicar_backlog_azure_boards/contrato_backlog.py:118: ValueError
_____________ test_recusa_id_que_nao_e_inteiro_positivo[`٣`] ______________
bruto = '`٣`'
    def test_recusa_id_que_nao_e_inteiro_positivo(bruto: str) -> None:
        valor, erros = normalizar_id(bruto)
>       assert valor is None
E       assert 3 is None
tests/test_contrato_id_existente.py:18: AssertionError
========================= 2 failed, 5 passed in 0.03s ==========================
```

### Correção

Em `normalizar_id`, em ambos os pacotes (`contrato_backlog.py` é espelhado por substituição
mecânica de nome de pacote):

```python
if not texto.isascii() or not texto.isdigit() or int(texto) <= 0:
```

A ordem importa: `isascii()` e `isdigit()` são checados com curto-circuito antes de `int(texto)`,
então `int()` só é chamado quando `texto` já é garantidamente ASCII e composto só de dígitos
decimais — nunca mais pode estourar `ValueError`. Docstring atualizada para explicar por que
`isdigit()` sozinho não bastava.

Testes: acrescentei `` `²³¹` `` e `` `٣` `` ao `parametrize` de
`test_recusa_id_que_nao_e_inteiro_positivo` nos dois pacotes.

### GREEN — depois da correção

```
$ cd publicar-backlog-azure-boards && uv run pytest tests/test_contrato_id_existente.py -v
collected 11 items
tests/test_contrato_id_existente.py::test_secao_ausente_devolve_none PASSED
tests/test_contrato_id_existente.py::test_le_id_entre_crases PASSED
tests/test_contrato_id_existente.py::test_recusa_id_que_nao_e_inteiro_positivo[`abc`] PASSED
tests/test_contrato_id_existente.py::test_recusa_id_que_nao_e_inteiro_positivo[`0`] PASSED
tests/test_contrato_id_existente.py::test_recusa_id_que_nao_e_inteiro_positivo[`-3`] PASSED
tests/test_contrato_id_existente.py::test_recusa_id_que_nao_e_inteiro_positivo[`47.21`] PASSED
tests/test_contrato_id_existente.py::test_recusa_id_que_nao_e_inteiro_positivo[`47 21`] PASSED
tests/test_contrato_id_existente.py::test_recusa_id_que_nao_e_inteiro_positivo[`\xb2\xb3\xb9`] PASSED
tests/test_contrato_id_existente.py::test_recusa_id_que_nao_e_inteiro_positivo[`٣`] PASSED
tests/test_contrato_id_existente.py::test_recusa_id_em_item_de_folha PASSED
tests/test_contrato_id_existente.py::test_recusa_feature_com_id_sob_epic_sem_id PASSED
============================== 11 passed in 0.02s ==============================
```

Suíte completa de cada pacote:

```
$ cd publicar-backlog-azure-boards && uv run pytest -q
........................................................................ [ 38%]
........................................................................ [ 77%]
..........................................                               [100%]
186 passed in 0.35s

$ cd publicar-backlog-demanda-azure-boards && uv run pytest -q
........................................................................ [ 25%]
........................................................................ [ 51%]
........................................................................ [ 77%]
..............................................................           [100%]
278 passed in 1.07s
```

`ruff check`, `ruff format --check` e `mypy src` passaram sem achados nos dois pacotes.

`test_sincronia_com_origem.py` (Demanda) — confirma que o mirror por substituição mecânica ficou
byte a byte igual à origem:

```
$ cd publicar-backlog-demanda-azure-boards && uv run pytest tests/test_sincronia_com_origem.py -v
tests/test_sincronia_com_origem.py::test_modulo_espelhado_e_identico_ao_da_origem[contrato_backlog.py] PASSED
tests/test_sincronia_com_origem.py::test_modulo_espelhado_e_identico_ao_da_origem[converter_para_html.py] PASSED
tests/test_sincronia_com_origem.py::test_modulo_espelhado_e_identico_ao_da_origem[interpretar_markdown.py] PASSED
tests/test_sincronia_com_origem.py::test_modulo_espelhado_e_identico_ao_da_origem[validacao_estrutural.py] PASSED
tests/test_sincronia_com_origem.py::test_modulos_espelhados_existem_no_pacote_local PASSED
============================== 5 passed in 0.01s ===============================
```

Invariante do hash — verificado explicitamente nos dois pacotes, literal não tocado:

```
$ uv run pytest -q tests/test_planejar_publicacao.py -k "nao_muda" -v
collected N items / M deselected / 2 selected
tests/test_planejar_publicacao.py ..                                     [100%]
2 passed
```

Largura de linha medida em caracteres via Python (`len()` sobre codepoints, não `awk` bruto —
lição já registrada na autorrevisão anterior): nenhuma linha alterada passou de 100 colunas em
nenhum dos dois pacotes.

Commit: `b7c7e94` — `fix: normalizar_id recusa entrada Unicode nao-ASCII em vez de estourar`.

### Achados Menores do revisor — deferidos, não corrigidos nesta rodada

Por instrução explícita do coordenador, ficam registrados para a triagem final do branch:
- `normalizar_id` é chamado duas vezes por item (uma em `validate_backlog` ao montar `com_id`,
  outra em `_validate_item`).
- Quando o `Parent` da Feature está ausente, a mensagem de ancestral sai com string vazia.
- Falta teste de integração passando ID malformado por `validate_backlog` para conferir o prefixo
  `"{item.key}: {erro}"`.

## O que foi implementado

Em ambos os pacotes (`publicar-backlog-azure-boards` e `publicar-backlog-demanda-azure-boards`):

### `contrato_backlog.py` (mirror byte a byte via substituição mecânica)
- Constantes `AZURE_BOARDS_ID = "Azure Boards ID"` e `CONTAINER_KINDS = ("Epic", "Feature")`.
- `AZURE_BOARDS_ID` acrescentado a `SECTION_NAMES` (por acréscimo, nada removido).
- `normalizar_id(bruto) -> tuple[int | None, list[str]]`: seção ausente/vazia devolve
  `(None, [])`; valor não inteiro-positivo devolve `(None, [erro])`; caso contrário devolve
  `(int, [])`.
- `_validate_item` ganhou o parâmetro `com_id: set[str]` (mesmo padrão de `keys`/`folhas`, calculado
  uma única vez em `validate_backlog`) e a validação:
  - recusa Azure Boards ID em item que não seja Epic ou Feature;
  - recusa Feature com ID cujo pai (Epic) não declara ID.
- `validate_backlog` calcula `com_id` antes do laço e passa para `_validate_item`.

### `interpretar_markdown.py` (mirror byte a byte via substituição mecânica)
- Import de `normalizar_id`.
- `"Azure Boards ID"` acrescentado a `_SECOES`.
- `_id_existente(item) -> int | None`: mesmo padrão de `_tags_do_item`/`_dependencias_do_item`
  para ler uma seção opcional e recusar presente-e-vazia, mas devolvendo o inteiro em vez de tupla.
- `_converter_item` passa `azure_boards_id=_id_existente(item)`.

### `modelos.py` (editado independentemente em cada pacote — não faz parte do mirror)
- `ItemBacklog.azure_boards_id: int | None = None`, acrescentado ao fim do dataclass, depois de
  `depende_de`.

### Testes (novos, um por pacote — `tests/test_contrato_id_existente.py`)
9 testes cada, replicando exatamente o brief: leitura de seção ausente, leitura de ID entre crases,
recusa parametrizada de valores não inteiros-positivos (`abc`, `0`, `-3`, `47.21`, `47 21`), recusa
de ID em item de folha (História) e recusa de Feature com ID cujo Epic pai não declara ID.

## Evidência de TDD

### RED — antes da implementação (pacote de origem)

```
$ cd publicar-backlog-azure-boards && uv run pytest tests/test_contrato_id_existente.py -q
==================================== ERRORS ====================================
_____________ ERROR collecting tests/test_contrato_id_existente.py _____________
ImportError while importing test module '.../tests/test_contrato_id_existente.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
tests/test_contrato_id_existente.py:3: in <module>
    from publicar_backlog_azure_boards.contrato_backlog import normalizar_id, validate_backlog
E   ImportError: cannot import name 'normalizar_id' from 'publicar_backlog_azure_boards.contrato_backlog'
=========================== short test summary info ============================
ERROR tests/test_contrato_id_existente.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.05s
```

Mesmo resultado (ImportError equivalente) no pacote de Demanda antes da implementação.

### GREEN — depois da implementação

```
$ cd publicar-backlog-azure-boards && uv run pytest tests/test_contrato_id_existente.py -v
collected 9 items
tests/test_contrato_id_existente.py .........                            [100%]
9 passed in 0.01s
```

Suíte completa dos dois pacotes:

```
$ cd publicar-backlog-azure-boards && uv run pytest -q
........................................................................ [ 39%]
........................................................................ [ 78%]
........................................                                 [100%]
184 passed in 0.26s

$ cd publicar-backlog-demanda-azure-boards && uv run pytest -q
........................................................................ [ 26%]
........................................................................ [ 52%]
........................................................................ [ 78%]
............................................................             [100%]
276 passed in 0.99s
```

`ruff check`, `ruff format --check` e `mypy src` passaram em ambos os pacotes sem achados:

```
$ uv run ruff check . && uv run ruff format --check . && uv run mypy src
All checks passed!
38 files already formatted
Success: no issues found in 15 source files   # (13 no pacote de origem)
```

### Invariante do hash (verificação explícita)

```
$ uv run pytest tests/test_planejar_publicacao.py -k hash -v
tests/test_planejar_publicacao.py::test_hash_nao_muda_para_backlog_sem_tags PASSED
```
Passou intacto nos dois pacotes; o literal `HASH_ANTES_DOS_CAMPOS_NOVOS` não foi tocado.

## Arquivos alterados

- `publicar-backlog-azure-boards/src/publicar_backlog_azure_boards/contrato_backlog.py`
- `publicar-backlog-azure-boards/src/publicar_backlog_azure_boards/interpretar_markdown.py`
- `publicar-backlog-azure-boards/src/publicar_backlog_azure_boards/modelos.py`
- `publicar-backlog-azure-boards/tests/test_contrato_id_existente.py` (novo)
- `publicar-backlog-demanda-azure-boards/src/publicar_backlog_demanda_azure_boards/contrato_backlog.py`
- `publicar-backlog-demanda-azure-boards/src/publicar_backlog_demanda_azure_boards/interpretar_markdown.py`
- `publicar-backlog-demanda-azure-boards/src/publicar_backlog_demanda_azure_boards/modelos.py`
- `publicar-backlog-demanda-azure-boards/tests/test_contrato_id_existente.py` (novo)

Commit: `26a0f51` — `feat: le e valida o Azure Boards ID de item ja publicado`

## Achados da autorrevisão

- **Armadilha de coluna 100 confirmada e evitada**: a primeira versão de
  `_validate_item`, depois de rodar `ruff format`, produziu a linha
  `f"{item.key} declara Azure Boards ID, mas seu pai {_parent_value(item)} não declara"` com
  exatamente 100 colunas contando caracteres Unicode (o `awk` padrão do macOS contou 101 porque
  mede bytes, e "não" tem um caractere multibyte) — ficou dentro do limite, mas por pouco, e só
  a checagem em Python (`len()` sobre codepoints) revelou o número real. Deixei a checagem de
  linha longa sempre em Python daqui em diante, não em `awk` cru, para não ser enganado por
  contagem de bytes.
  - **Atenção para a Tarefa 7**: essa mesma linha, ao ser espelhada para o pacote de Demanda
    (nome de pacote mais longo), continuou dentro de 100 colunas porque a linha não contém o
    nome do pacote — mas qualquer alteração futura que aproxime essa linha do limite deve ser
    conferida com uma contagem correta de caracteres, não de bytes.
- Conferi que nenhum outro chamador de `_validate_item` existia fora de `contrato_backlog.py`
  (assinatura mudou de 3 para 4 parâmetros posicionais).
- Conferi ausência de import cruzado entre os dois pacotes (`grep` por
  `publicar_backlog_azure_boards` dentro do pacote de Demanda e vice-versa: vazio).
- `SECTION_NAMES`, `_SECOES` e `_validate_item` cresceram por acréscimo; nada do que já existia
  foi removido ou reordenado.
- O campo novo (`azure_boards_id`) ficou no fim do dataclass `ItemBacklog`, depois de
  `depende_de`, com default `None`, como pedido.
- `modelos.py` foi editado independentemente em cada pacote (não está na lista de
  `MODULOS_ESPELHADOS` de `test_sincronia_com_origem.py`), então a divergência de conteúdo entre
  os dois arquivos (o pacote de Demanda tem `Demanda`, `demanda_id` etc.) foi preservada; só
  acrescentei a mesma linha nos dois.
- Os testes cobrem comportamento real: leitura de valor, recusa por formato, recusa por tipo de
  item (folha) e recusa por ancestral sem ID — todos verificando a mensagem de erro exata, não
  apenas a presença de "algum erro".

## Problemas ou preocupações

Nenhum. Escopo desta tarefa é só leitura e recusas; plano, manifesto e execução (uso real do
`azure_boards_id` para pendurar filhos em vez de recriar) ficam para a Tarefa 7, como o brief
determina.
