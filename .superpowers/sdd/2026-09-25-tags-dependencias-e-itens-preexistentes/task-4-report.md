# Relatório — Tarefa 4: ordenação topológica estável

## O que foi implementado

Em ambos os pacotes (`publicar-backlog-azure-boards` e `publicar-backlog-demanda-azure-boards`):

- `modelos.py`: acrescentado `OperacaoCriacao.depende_de: tuple[str, ...] = ()`, depois de `tags`,
  no fim do dataclass.
- `planejar_publicacao.py`:
  - Nova exceção `ErroDependenciaCiclica(ValueError)`.
  - Nova função `_ordenar_para_criacao(itens)`: ordena pela chave de ordenação existente
    (`_chave_ordenacao`, por tipo e depois por chave numérica) e em seguida faz uma travessia em
    DFS pós-ordem, visitando cada predecessor declarado em `depende_de` antes de emitir o próprio
    item. Detecta ciclo (item revisitado enquanto ainda em pilha de visita) e levanta
    `ErroDependenciaCiclica` com a cadeia formatada.
  - `criar_plano` passou a chamar `_ordenar_para_criacao` no lugar do `sorted` direto.
  - `_criar_operacao` passou a propagar `depende_de=item.depende_de` para `OperacaoCriacao`.
  - `_conteudo_do_item` passou a incluir `"depende_de"` na serialização do hash quando o campo
    estiver preenchido, seguindo o mesmo critério condicional e o mesmo comentário já existente
    para `tags`.

Nenhuma outra função ou assinatura pública mudou. `_criar_operacao` no pacote de Demanda continua
sem o parâmetro `data_geracao` (usa `montar_titulo`), exatamente como antes — essa é a única
assimetria intencional entre os dois arquivos, preexistente à tarefa.

## TDD — evidência

### RED

Testes novos adicionados primeiro em ambos os `tests/test_planejar_publicacao.py` (os 5 do brief,
verbatim). Rodando antes de tocar em produção:

```
$ cd publicar-backlog-azure-boards && uv run pytest tests/test_planejar_publicacao.py -q
...
FAILED tests/test_planejar_publicacao.py::test_predecessor_e_criado_antes_do_dependente_mesmo_com_chave_maior
  AssertionError: assert 3 < 2  (ordem antiga: ['1.0.0', '1.1.0', '1.1.1', '1.1.2'])
FAILED tests/test_planejar_publicacao.py::test_operacao_propaga_dependencias
  AttributeError: 'OperacaoCriacao' object has no attribute 'depende_de'
2 failed, 14 passed in 0.07s
```

```
$ cd publicar-backlog-demanda-azure-boards && uv run pytest tests/test_planejar_publicacao.py -q
...
FAILED tests/test_planejar_publicacao.py::test_predecessor_e_criado_antes_do_dependente_mesmo_com_chave_maior
FAILED tests/test_planejar_publicacao.py::test_operacao_propaga_dependencias
2 failed, 16 passed in 0.07s
```

(As outras 3 asserções novas — `test_ordem_sem_dependencias_e_identica_a_de_hoje`,
`test_pai_continua_antes_do_filho_com_dependencia_entre_irmaos`,
`test_hash_nao_muda_para_backlog_sem_dependencias` — já passavam mesmo antes da implementação,
porque descrevem comportamento que a ordenação por chave antiga já satisfazia por coincidência nesse
conjunto de fixtures; as duas falhas acima é que exigiam a lógica nova.)

### GREEN

Após implementar `_ordenar_para_criacao`, `ErroDependenciaCiclica`, o campo `depende_de` em
`OperacaoCriacao` e a propagação em `_criar_operacao`/`_conteudo_do_item`:

```
$ cd publicar-backlog-azure-boards && uv run pytest -q
165 passed in 0.33s

$ cd publicar-backlog-azure-boards && uv run pytest tests/test_planejar_publicacao.py -v \
    -k "hash_nao_muda or dependenc or predecessor or propaga_dependencias or ordem_sem"
6 passed in 0.04s
  (inclui test_hash_nao_muda_para_backlog_sem_tags PASSED — invariante preservada)

$ cd publicar-backlog-demanda-azure-boards && uv run pytest -q
257 passed in 1.04s

$ cd publicar-backlog-demanda-azure-boards && uv run pytest tests/test_planejar_publicacao.py -v \
    -k "hash_nao_muda or dependenc or predecessor or propaga_dependencias or ordem_sem"
6 passed in 0.04s
  (inclui test_hash_nao_muda_para_backlog_sem_tags PASSED)
```

`ruff check .`, `ruff format --check .` e `mypy src` passam em ambos os pacotes (formatação
aplicada nos dois arquivos de teste novos via `uv run ruff format`, que quebrou os construtores
`ItemBacklog` de linha única em multilinha — nenhuma mudança de produção precisou de reformatação).

## Arquivos alterados

- `publicar-backlog-azure-boards/src/publicar_backlog_azure_boards/modelos.py`
- `publicar-backlog-azure-boards/src/publicar_backlog_azure_boards/planejar_publicacao.py`
- `publicar-backlog-azure-boards/tests/test_planejar_publicacao.py`
- `publicar-backlog-demanda-azure-boards/src/publicar_backlog_demanda_azure_boards/modelos.py`
- `publicar-backlog-demanda-azure-boards/src/publicar_backlog_demanda_azure_boards/planejar_publicacao.py`
- `publicar-backlog-demanda-azure-boards/tests/test_planejar_publicacao.py`

## Autorrevisão

- `git diff -- */src` comparado entre os dois pacotes: a única diferença fora do que já existia
  antes da tarefa (caminho de import, ausência de `data_geracao`/uso de `montar_titulo` no pacote de
  Demanda, `demanda_id` no hash de configuração) é nenhuma — o trecho novo
  (`ErroDependenciaCiclica`, `_ordenar_para_criacao`, propagação em `_criar_operacao` e
  `_conteudo_do_item`) é byte-a-byte idêntico nos dois arquivos. Simetria confirmada manualmente,
  já que este arquivo não está coberto por `test_sincronia_com_origem.py`.
- Nenhuma linha de produção passa de 100 colunas (`awk 'length($0) > 100'` sobre os dois arquivos:
  vazio).
- O literal `HASH_ANTES_DOS_CAMPOS_NOVOS` não foi tocado; o teste que o usa continua verde nos dois
  pacotes.
- `_ordenar_para_criacao` implementa exatamente o algoritmo do brief (DFS pós-ordem a partir da
  ordem base), sem YAGNI adicional — nenhuma otimização, cache ou parâmetro extra foi introduzido.
- A guarda de ciclo em `_ordenar_para_criacao` é uma camada própria (pilha de visita local), distinta
  da validação estrutural em `contrato_backlog.detectar_ciclo`, como o brief pedia; não reaproveitei
  nem dependi de código de `contrato_backlog.py` para não criar acoplamento indevido nesta função.
- Testes novos verificam comportamento real (ordem observável via `chaves.index`, atributo
  `depende_de` na operação, e o hash) — nenhum teste é tautológico ou testa só a implementação.

## Problemas ou preocupações

Nenhum. Todos os comandos de verificação (`pytest`, `ruff check`, `ruff format --check`, `mypy src`)
passam nos dois pacotes, e a invariante de hash crítica (`HASH_ANTES_DOS_CAMPOS_NOVOS`) permanece
intacta.
