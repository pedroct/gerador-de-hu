# Relatório — Tarefa 7a: item pré-existente no modelo, no plano e no manifesto

## O que foi implementado

Nos dois pacotes (`publicar-backlog-azure-boards` e `publicar-backlog-demanda-azure-boards`),
em `modelos.py`, `planejar_publicacao.py` e `manifesto.py`, exatamente como o brief especificou:

### `modelos.py`
- Nova dataclass `ItemPreexistente(chave: str, tipo: TipoItem, id: int)`, posicionada logo
  após `ItemBacklog`.
- `RegistroManifesto` ganhou o campo `preexistente: bool = False` no fim, com o comentário
  fornecido no brief, verbatim.
- `PlanoPublicacao` ganhou `preexistentes: tuple[ItemPreexistente, ...] = ()` depois dos
  campos existentes.

### `planejar_publicacao.py`
- `criar_plano` agora separa, logo após `_ordenar_para_criacao`, os itens com
  `azure_boards_id` preenchido em `preexistentes` (tupla de `ItemPreexistente`) e monta
  `operacoes` apenas a partir de `a_criar` (itens sem ID declarado).
- `PlanoPublicacao` recebe `preexistentes=preexistentes`.
- `_calcular_hash` continua recebendo `itens_ordenados` (todos os itens, inclusive
  pré-existentes) — não foi alterado.
- `_conteudo_do_item` ganhou a terceira chave condicional `azure_boards_id`, ao lado de
  `tags` e `depende_de`, preservando o comentário existente sobre a assimetria do hash.

### `manifesto.py`
- `_serializar` inclui `"preexistente": registro.preexistente` em cada item.
- `_converter` lê de volta com `bool(dados_item.get("preexistente", False))`, garantindo
  que um manifesto gravado por versão anterior (sem a chave) continue válido, com a marca
  em `False`.

Nenhuma mudança em `executar_publicacao.py`, `cliente_azure_devops.py` ou `cli.py` — a
contagem de itens registrados em `cli.py` (`registrados = len(manifesto.itens)`) não foi
tocada porque, nesta tarefa, nada ainda semeia registros pré-existentes em
`manifesto.itens` (isso é a Tarefa 7b); portanto não há hoje nenhum registro marcado que
precise ser excluído dessa contagem.

## O que foi testado e resultados

Testes adicionados (idênticos, com os ajustes de import específicos de cada pacote) em
`tests/test_planejar_publicacao.py` e `tests/test_manifesto.py` dos dois pacotes, conforme
o brief:

- `test_item_com_id_declarado_nao_vira_operacao_de_criacao`
- `test_plano_sem_id_declarado_nao_tem_preexistentes`
- `test_hash_muda_quando_ha_id_declarado`
- `test_preserva_a_marca_de_preexistente_ao_gravar_e_ler`
- `test_manifesto_antigo_sem_a_marca_continua_valido`

## Evidência de TDD

### RED — pacote `publicar-backlog-azure-boards`

Comando:
```
uv run pytest tests/test_planejar_publicacao.py tests/test_manifesto.py -q
```
Saída (collection falha por `ImportError`; rodando `test_manifesto.py` isoladamente mostra
o `TypeError`/`KeyError` esperados):
```
ImportError while importing test module '.../tests/test_planejar_publicacao.py'.
E   ImportError: cannot import name 'ItemPreexistente' from 'publicar_backlog_azure_boards.modelos' (.../modelos.py)
```
```
$ uv run pytest tests/test_manifesto.py -q
...
E       TypeError: RegistroManifesto.__init__() takes 4 positional arguments but 5 were given
...
E       KeyError: 'preexistente'
2 failed, 16 passed in 0.04s
```

### RED — pacote `publicar-backlog-demanda-azure-boards`

```
$ uv run pytest tests/test_manifesto.py -q
...
E       KeyError: 'preexistente'
2 failed, 17 passed in 0.05s

$ uv run pytest tests/test_planejar_publicacao.py -q
...
E   ImportError: cannot import name 'ItemPreexistente' from 'publicar_backlog_demanda_azure_boards.modelos' (.../modelos.py)
1 error in 0.06s
```

### GREEN — pacote `publicar-backlog-azure-boards`

```
$ uv run pytest tests/test_planejar_publicacao.py tests/test_manifesto.py -q
......................................                                   [100%]
38 passed in 0.08s

$ uv run pytest -q
........................................................................ [ 37%]
........................................................................ [ 75%]
...............................................                          [100%]
191 passed in 0.36s
```

### GREEN — pacote `publicar-backlog-demanda-azure-boards`

```
$ uv run pytest -q
........................................................................ [ 25%]
........................................................................ [ 50%]
........................................................................ [ 76%]
...................................................................      [100%]
283 passed in 1.07s
```

### Invariante do hash (ambos os pacotes)

```
$ uv run pytest -q -k "test_hash_nao_muda_para_backlog_sem_tags"
.                                                                        [100%]
1 passed, 190 deselected in 0.14s   # publicar-backlog-azure-boards

.                                                                        [100%]
1 passed, 282 deselected in 0.15s   # publicar-backlog-demanda-azure-boards
```

`HASH_ANTES_DOS_CAMPOS_NOVOS` não foi tocado; continua verde nos dois pacotes.

### Qualidade (ambos os pacotes)

```
uv run ruff check .        → All checks passed!
uv run ruff format --check . → arquivos já formatados
uv run mypy src             → Success: no issues found
```

## Arquivos alterados

- `publicar-backlog-azure-boards/src/publicar_backlog_azure_boards/modelos.py`
- `publicar-backlog-azure-boards/src/publicar_backlog_azure_boards/planejar_publicacao.py`
- `publicar-backlog-azure-boards/src/publicar_backlog_azure_boards/manifesto.py`
- `publicar-backlog-azure-boards/tests/test_planejar_publicacao.py`
- `publicar-backlog-azure-boards/tests/test_manifesto.py`
- `publicar-backlog-demanda-azure-boards/src/publicar_backlog_demanda_azure_boards/modelos.py`
- `publicar-backlog-demanda-azure-boards/src/publicar_backlog_demanda_azure_boards/planejar_publicacao.py`
- `publicar-backlog-demanda-azure-boards/src/publicar_backlog_demanda_azure_boards/manifesto.py`
- `publicar-backlog-demanda-azure-boards/tests/test_planejar_publicacao.py`
- `publicar-backlog-demanda-azure-boards/tests/test_manifesto.py`

## Autorrevisão

- Diff dos dois pacotes é simétrico ponto a ponto (mesmas mudanças de produção e de teste,
  respeitando as diferenças de nome de pacote e a assinatura própria de `_criar_operacao`
  no pacote de demanda).
- Confirmado, por `grep`, que não há import cruzado entre os pacotes (a única menção de
  `publicar_backlog_azure_boards` dentro do pacote de demanda é em
  `tests/test_sincronia_com_origem.py`, já existente, que compara os módulos entre
  pacotes — não é um import de produção).
- Todas as linhas dos arquivos tocados foram medidas em caracteres via Python; nenhuma
  ultrapassa 100 colunas.
- `_calcular_hash` continua recebendo `itens_ordenados` (todos os itens) — não foi
  restringido a `a_criar` — preservando a intenção do brief de que o hash reflita o
  backlog completo.
- Campo novo em cada dataclass foi colocado ao final com default, preservando construção
  posicional dos testes existentes.
- Não toquei em `executar_publicacao.py`, `cliente_azure_devops.py` nem `cli.py`.

## Problemas ou preocupações

Nenhum. Suíte completa dos dois pacotes verde, invariante do hash preservado, lint/format/
mypy limpos, commit único cobrindo os dois pacotes.

## Commit

`f441027` — `feat: separa item ja publicado das operacoes de criacao`
