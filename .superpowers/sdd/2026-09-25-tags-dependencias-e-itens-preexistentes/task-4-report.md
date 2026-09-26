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

---

## Correção pós-revisão: achado Crítico — dependência entre ramos diferentes

### O achado

O revisor reproduziu um caso em que um item **não-folha** (Epic ou Feature) declarava `depende_de`
apontando para uma folha de outro ramo da hierarquia. Como `_ordenar_para_criacao` só segue a aresta
`depende_de` e não trata `item.pai` como aresta implícita, a folha-alvo era puxada para o início do
resultado sem seus próprios ancestrais — invertendo pai e filho.

### A decisão do coordenador (não minha, registrada aqui por rastreabilidade)

A correção não vai no algoritmo de ordenação. Dois pontos sustentam isso:

1. O caso que a spec de fato permite (folha depende de folha, em ramos diferentes) já sai correto
   hoje — por construção, toda folha vem por último na ordem base, então todo contêiner ancestral já
   foi emitido antes de qualquer aresta de dependência ser seguida.
2. A spec diz textualmente que `Depende de` "vale entre quaisquer dois itens de folha". A validação
   da Tarefa 3 já exigia que o **alvo** fosse folha, mas não validava a **origem**. Essa lacuna — não
   o algoritmo de ordenação — é a causa raiz: o caso reproduzido pelo revisor é um caso que o
   contrato já deveria proibir.

Por isso a correção ficou inteiramente em `contrato_backlog._validate_item` (validação estrutural),
não em `planejar_publicacao._ordenar_para_criacao`.

### O que mudou

Em **ambos** os pacotes:

- `contrato_backlog.py`, dentro do bloco `if DEPENDE_DE in item.sections:` de `_validate_item`:
  acrescentada a checagem `if item.key not in folhas: errors.append(f"{item.key} declara Depende de,
  permitido só em item de folha")`, usando o `folhas` já recebido como parâmetro (sem recalcular).
- `test_contrato_dependencias.py`: acrescentada a fixture `BACKLOG_COM_DUAS_FOLHAS` (Epic → Feature →
  duas Histórias-folha, com placeholders `{depende_de_epic}`, `{depende_de_feature}` e
  `{depende_de_leaf}` para inserir a seção `Depende de` em cada nível) e três testes:
  - `test_recusa_dependencia_declarada_em_feature`
  - `test_recusa_dependencia_declarada_em_epic`
  - `test_folha_com_dependencia_continua_aceita` (não-regressão: folha dependendo de folha continua
    aceito, `erros == []`)
- `planejar_publicacao.py`: nenhuma mudança de lógica. Acrescentada uma frase ao docstring de
  `_ordenar_para_criacao` explicando por que a aresta de pai não é necessária (para que ninguém
  "conserte" isso de novo).
- `test_planejar_publicacao.py`: acrescentado `test_dependencia_entre_ramos_preserva_pai_antes_do_filho`,
  que documenta o caso do achado (folha em ramo 1 depende de folha em ramo 3) e confirma que os pais
  de ambos os ramos saem antes de seus filhos.

### Evidência de TDD

**RED** — confirmado removendo temporariamente a checagem nova (via `sed`, restaurada em seguida a
partir de um backup local, sem tocar no histórico do git) e rodando os testes novos de validação:

```
$ cd publicar-backlog-azure-boards && uv run pytest tests/test_contrato_dependencias.py -k "declarada_em" -v
FAILED tests/test_contrato_dependencias.py::test_recusa_dependencia_declarada_em_feature
FAILED tests/test_contrato_dependencias.py::test_recusa_dependencia_declarada_em_epic
2 failed, 11 deselected in 0.02s
```

Restaurada a checagem, os mesmos dois testes passam:

```
$ cd publicar-backlog-azure-boards && uv run pytest tests/test_contrato_dependencias.py -q
13 passed in 0.01s
```

`test_dependencia_entre_ramos_preserva_pai_antes_do_filho` (o teste de ordenação do brief da revisão)
já passa **sem** nenhuma mudança em `planejar_publicacao.py` — confirmando experimentalmente o ponto
1 da decisão do coordenador (o algoritmo de ordenação já está correto para o caso que a spec permite;
só faltava a validação recusar o caso que a spec proíbe):

```
$ cd publicar-backlog-azure-boards && uv run pytest tests/test_planejar_publicacao.py -k dependencia_entre_ramos -v
tests/test_planejar_publicacao.py::test_dependencia_entre_ramos_preserva_pai_antes_do_filho PASSED
1 passed, 16 deselected in 0.06s
```

### GREEN — suíte completa

```
$ cd publicar-backlog-azure-boards && uv run pytest -q && uv run ruff check . && \
    uv run ruff format --check . && uv run mypy src
169 passed in 0.31s
All checks passed!
29 files left unchanged
Success: no issues found in 13 source files

$ cd publicar-backlog-demanda-azure-boards && uv run pytest -q && uv run ruff check . && \
    uv run ruff format --check . && uv run mypy src
261 passed in 1.06s
All checks passed!
37 files left unchanged
Success: no issues found in 15 source files
```

Invariante crítica reconfirmada nos dois pacotes:

```
$ uv run pytest tests/test_planejar_publicacao.py::test_hash_nao_muda_para_backlog_sem_tags -v
tests/test_planejar_publicacao.py::test_hash_nao_muda_para_backlog_sem_tags PASSED
```

Sincronia (`contrato_backlog.py` está na lista de módulos espelhados):

```
$ cd publicar-backlog-demanda-azure-boards && uv run pytest tests/test_sincronia_com_origem.py -v
5 passed in 0.01s
```

### Achados da autorrevisão da correção

- `diff` do `contrato_backlog.py` entre os dois pacotes: idêntico byte a byte (o arquivo não contém
  o nome do pacote em nenhum lugar, então `cp` direto já satisfaz `test_sincronia_com_origem.py`).
- Nenhuma linha nova passa de 100 colunas em nenhum dos 8 arquivos tocados (verificado com
  `awk 'length($0) > 100'`).
- A checagem nova usa o parâmetro `folhas` já recebido por `_validate_item`, sem recalcular a
  partir de `item.kind` — conforme pedido.
- A checagem é aditiva (não usa `elif`/`return` antecipado): quando um item não-folha declara
  `Depende de` malformado (ex.: chave inválida), ambos os erros aparecem juntos, consistente com o
  padrão já usado para `Tags` na mesma função.
- O achado **menor** do revisor (profundidade de recursão de `visitar` proporcional ao maior
  encadeamento de `depende_de`) foi deixado como está, por instrução explícita do coordenador — não
  mexi nele.

### Problemas ou preocupações

Nenhum. Todas as verificações pedidas passaram, incluindo a invariante de hash e a sincronia entre
pacotes.
