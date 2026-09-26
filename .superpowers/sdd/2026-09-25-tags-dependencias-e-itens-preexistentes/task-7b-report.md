# Relatório — Tarefa 7b: execução e conferência do item pré-existente

## O que foi implementado

Em **ambos** os pacotes (`publicar-backlog-azure-boards` e `publicar-backlog-demanda-azure-boards`):

### `cliente_azure_devops.py`

- `VERSOES_API` ganhou a chave `"consulta": "7.2-preview.3"` (mesma família de `"criacao"`, que já
  usa o recurso `/_apis/wit/workitems`).
- `url_do_item(id_item) -> str`: monta `f"{self._base_url}/_apis/wit/workItems/{id_item}"`.
- `verificar_item_existente(id_item, tipo_esperado) -> None`: faz `GET
  /_apis/wit/workitems/{id_item}`, lê `fields["System.WorkItemType"]` e levanta
  `ErroDestinoInvalido` se divergir do tipo esperado — exatamente como o brief especificou.

### `executar_publicacao.py`

- `ClientePublicador` (Protocol) ganhou `url_do_item(self, id_item: int) -> str: ...`.
- `executar_plano` agora semeia `registros` **e `titulos`** com cada `plano.preexistentes` antes do
  laço de criação:
  ```python
  registros[preexistente.chave] = RegistroManifesto(
      preexistente.id, preexistente.tipo, cliente.url_do_item(preexistente.id), preexistente=True,
  )
  titulos.setdefault(preexistente.chave, f"(item pré-existente, Azure Boards #{preexistente.id})")
  ```
  O `titulos.setdefault(...)` **não estava no snippet do brief** e foi necessário: sem ele, o
  primeiro `gravar_manifesto` dentro do laço grava `itens[chave].titulo = None` (porque
  `ItemPreexistente` não carrega título), e o teste do brief falhava ao reler o manifesto com
  `ValueError: Um item do manifesto não contém identidade completa.` Encontrado ao rodar o teste
  fornecido (ver GREEN abaixo) — o rótulo é só informativo, nunca comparado ao backlog, porque a
  chave de um preexistente não está em `plano.operacoes`.
- Com isso, a checagem de pai (`operacao.chave_pai not in registros`) passa a encontrar o item
  declarado sem recriá-lo, e nenhuma operação de criação existe para ele (Tarefa 7a já o removeu de
  `plano.operacoes`).

### `cli.py` (além do que o brief listou em "Arquivos" — ver seção de achados)

- `ClientePublicacao` (Protocol) ganhou `verificar_item_existente` e `url_do_item` (o segundo por
  exigência do mypy: `executar_plano` agora exige `url_do_item` no `ClientePublicador`, e `cli.py`
  passa `cliente_real: ClientePublicacao` para ele).
- `_verificar_preliminar` ganhou o parâmetro `preexistentes: Sequence[ItemPreexistente] = ()` e, para
  cada um, chama `cliente.verificar_item_existente(preexistente.id, tipo_remoto)` **antes** do laço
  que valida as operações de criação — ou seja, antes de qualquer chamada que crie algo e antes de
  `_publicar` pedir autorização. `tipo_remoto` vem de
  `configuracao.mapeamento_tipos.nome_remoto(preexistente.tipo)`, não de um literal fixo.
- `principal` passa `plano.preexistentes` nessa chamada.

## Por que mexi em `cli.py` além da lista "Arquivos" do brief

A seção "Arquivos" do brief cita só `executar_publicacao.py` e `cliente_azure_devops.py`. Mas o
Passo 3 do próprio brief, e a seção "Restrições globais" do prompt da tarefa, dizem explicitamente:
"Chame `verificar_item_existente` uma vez por item pré-existente na verificação preliminar, antes de
pedir autorização — é lá que os outros avisos do publicador já aparecem." Essa verificação preliminar
só existe em `cli.py` (`_verificar_preliminar`, chamada em `principal` antes de `_publicar`). Segui a
instrução explícita e mais detalhada, não a lista de arquivos resumida, e documento aqui a
divergência para revisão.

## Testes escritos e resultados (evidência de TDD)

### RED — antes da implementação

```
$ cd publicar-backlog-azure-boards && uv run pytest tests/test_executar_publicacao.py tests/test_cliente_azure_devops.py -q
...
FAILED tests/test_executar_publicacao.py::test_item_preexistente_nao_e_recriado_e_serve_de_pai
FAILED tests/test_cliente_azure_devops.py::test_url_do_item_monta_o_caminho_canonico
FAILED tests/test_cliente_azure_devops.py::test_verificar_item_existente_aceita_o_tipo_esperado
FAILED tests/test_cliente_azure_devops.py::test_verificar_item_existente_recusa_tipo_divergente
4 failed, 50 passed in 0.18s
```

Mesmo resultado (4 failed) no pacote `publicar-backlog-demanda-azure-boards` (52 passed antes das
falhas, por ter mais testes de base).

Depois de implementar só `cliente_azure_devops.py`, rodei de novo e restou 1 falha (a de
`executar_publicacao.py`, por causa do `id_pai` do pai preexistente não estar em `registros` ainda):

```
ValueError: O pai 1.0.0 do item 1.1.0 não foi publicado.
```

Implementei `executar_publicacao.py` (registros) e o teste ainda falhava, agora mais adiante, ao
reler o manifesto gravado:

```
ValueError: Um item do manifesto não contém identidade completa.
```

Isso apontou a lacuna do título (ver seção acima). Depois de adicionar `titulos.setdefault(...)`:

### GREEN — depois da implementação completa

```
$ cd publicar-backlog-azure-boards && uv run pytest tests/test_executar_publicacao.py tests/test_cliente_azure_devops.py -q
......................................................                   [100%]
54 passed in 0.13s

$ cd publicar-backlog-demanda-azure-boards && uv run pytest tests/test_executar_publicacao.py tests/test_cliente_azure_devops.py -q
........................................................                 [100%]
56 passed in 0.13s
```

### `cli.py` — wiring da verificação preliminar

Não havia `tests/test_cli.py` em nenhum dos pacotes (todo teste de CLI passa por `principal()` em
`test_integracao_final.py`, que não tem fixture de backlog com `Azure Boards ID`). Criar um backlog
Markdown válido só para isso adicionaria complexidade desproporcional (regras de contrato estrutural,
metadados, critérios de aceitação). Optei por testar `_verificar_preliminar` diretamente — é a mesma
abordagem de "cliente espião" já usada em `test_executar_publicacao.py` e `test_integracao_final.py`
— criando `tests/test_cli.py` em ambos os pacotes com 3 testes:

- confere cada item pré-existente (múltiplos, na ordem);
- usa o tipo remoto **mapeado** (`MapeamentoTipos` customizado), não um literal fixo;
- sem preexistentes, não chama `verificar_item_existente` (garante que os testes de integração
  existentes, cujo `ClienteSimulado` não tem esse método, continuam passando sem quebrar).

Este bloco foi implementado antes de eu registrar formalmente o RED (a mudança em `cli.py` seguiu
direto da leitura da instrução explícita, no mesmo bloco de trabalho da wiring). Validei
retroativamente que a chamada antiga de `_verificar_preliminar` aceitava só 3 argumentos posicionais
— chamar com um 4º argumento (`preexistentes`) teria estourado `TypeError` antes da mudança, e não
havia chamada a `verificar_item_existente` em lugar nenhum do fluxo antigo — então o RED real teria
sido `TypeError`/ausência de chamada. Resultado atual:

```
$ cd publicar-backlog-azure-boards && uv run pytest tests/test_cli.py -q
...                                                                      [100%]
3 passed in 0.22s

$ cd publicar-backlog-demanda-azure-boards && uv run pytest tests/test_cli.py -q
...                                                                      [100%]
3 passed in 0.20s
```

## Suíte inteira, lint, format, mypy (Passo 4)

```
$ cd publicar-backlog-azure-boards
$ uv run pytest -q
198 passed in 0.28s
$ uv run ruff check .
All checks passed!
$ uv run ruff format --check .
31 files already formatted
$ uv run mypy src
Success: no issues found in 13 source files

$ cd publicar-backlog-demanda-azure-boards
$ uv run pytest -q
290 passed in 0.99s
$ uv run ruff check .
All checks passed!
$ uv run ruff format --check .
39 files already formatted
$ uv run mypy src
Success: no issues found in 15 source files
```

`test_hash_nao_muda_para_backlog_sem_tags` está entre os 198/290 testes verdes nos dois pacotes — o
hash não foi tocado.

Linhas adicionadas conferidas em Python (`len(linha) > 100` contando caracteres, não bytes): nenhuma
linha do diff excede 100 caracteres nos arquivos de produção nem de teste (inclusive os dois
`tests/test_cli.py` novos).

## Conclusão sobre a verificação nomeada em `cli.py:147` ("registrados")

**Concordo com a avaliação: nenhuma mudança é necessária.** Confirmando pela leitura:

1. `registrados = len(manifesto.itens)` é lido do manifesto **em disco antes** desta execução (via
   `ler_manifesto`, antes de qualquer seed de preexistentes em memória). Depois que uma execução
   grava pelo menos uma operação no manifesto, os preexistentes seedados também passam a fazer parte
   de `manifesto.itens` persistido (porque `_manifesto_atualizado` usa o dict `registros` inteiro).
   Numa próxima invocação da CLI, `len(manifesto.itens)` passará a contá-los — e isso está correto: o
   rótulo diz "registrados", não "criados", e um preexistente genuinamente está registrado no
   manifesto (é o que o rastreia como pai resolvido).
2. `contagem = Counter(operacao.tipo_remoto for operacao in pendentes)` ("Por tipo remoto") itera só
   `pendentes`, que vem de `plano.operacoes` (via `validar_manifesto` ou direto), e a Tarefa 7a já
   garante que preexistentes nunca entram em `plano.operacoes`. Essa contagem exclui preexistentes
   por construção, sem precisar de nenhum filtro extra.

Não fiz nenhuma mudança em `cli.py` para este ponto especificamente (a única mudança em `cli.py` foi
a wiring de `_verificar_preliminar` descrita acima).

## Achado fora do escopo declarado: `validar_manifesto` quebra a segunda rodada

Ao me autorrevisar, notei que `validar_manifesto` (em `manifesto.py`, fora da lista de arquivos desta
tarefa) **não sabe sobre preexistentes**. Ela itera `manifesto.itens.items()` e, para cada chave,
exige `operacoes.get(chave)` (onde `operacoes` vem de `plano.operacoes`); se a chave não está lá,
levanta `ValueError("O item {chave} do manifesto não pertence ao backlog completo.")`. Como a Tarefa
7a garante que a chave de um preexistente **nunca** está em `plano.operacoes`, qualquer segunda
chamada de `executar_plano`/`publicar` sobre um manifesto que já persistiu o preexistente (isto é,
depois que ao menos uma operação foi criada numa rodada anterior) vai falhar nessa checagem — mesmo
que nada tenha mudado no backlog.

Reproduzi isso isoladamente (script descartável, não commitado): plano com Epic preexistente `#4721`
e Feature `1.1.0` a criar; `executar_plano` roda e grava o manifesto com sucesso; ao chamar
`validar_manifesto` de novo com o mesmo manifesto e o mesmo plano (simulando uma segunda invocação da
CLI), o resultado é:

```
Primeira rodada OK. itens no manifesto: ['1.0.0', '1.1.0']
Segunda rodada: validar_manifesto FALHOU: O item 1.0.0 do manifesto não pertence ao backlog completo.
```

Isso é exatamente o cenário motivador desta tarefa e do plano inteiro — "a segunda rodada sobre o
mesmo fluxo encontra o Epic já publicado" — e ele quebra assim que a primeira rodada grava qualquer
operação no manifesto (não quebra se a primeira rodada não autorizar nenhuma operação, porque
`gravar_manifesto` só é chamado dentro do laço de criação). Não toquei em `manifesto.py`: está fora
da lista de arquivos desta tarefa, é uma mudança de mais alto risco (a mesma função tem outras
checagens de reconciliação e round-trip que a Tarefa 7a e outras tarefas já blindaram com testes), e
a invariante do hash (que eu não deveria tocar) vive no mesmo arquivo/vizinhança conceitual. Deixo
para decisão do controlador se isso vira uma Tarefa 7c ou um ajuste em `validar_manifesto` (a correção
mais direta seria pular a checagem "não pertence ao backlog completo" para registros com
`preexistente=True`, cruzando-os contra `plano.preexistentes` por chave/id/tipo em vez de
`plano.operacoes`).

## Arquivos alterados

- `publicar-backlog-azure-boards/src/publicar_backlog_azure_boards/cliente_azure_devops.py`
- `publicar-backlog-azure-boards/src/publicar_backlog_azure_boards/executar_publicacao.py`
- `publicar-backlog-azure-boards/src/publicar_backlog_azure_boards/cli.py`
- `publicar-backlog-azure-boards/tests/test_cliente_azure_devops.py`
- `publicar-backlog-azure-boards/tests/test_executar_publicacao.py`
- `publicar-backlog-azure-boards/tests/test_cli.py` (novo)
- Os mesmos seis arquivos em `publicar-backlog-demanda-azure-boards` (caminhos equivalentes)

## Achados da autorrevisão

- Os dois pacotes ficaram simétricos linha a linha nas partes de produção (só diferindo onde a
  Demanda já divergia antes, como `validar_operacao(operacao, id_pai=...)`).
- Nenhum import cruzado entre os pacotes.
- `verificar_item_existente` trata `dados.get("fields", {}).get("System.WorkItemType")` como `None`
  quando o campo não vem na resposta, e a mensagem de erro mostra o `None` — comportamento aceitável
  (não é um caminho exercitado pelos testes, mas não quebra nada e a mensagem continua informativa).
- Considerei se o `titulos.setdefault` deveria usar `=` em vez de `setdefault`; usei `setdefault` para
  não sobrescrever um título já existente no manifesto lido do disco (round-trip de uma reconciliação
  anterior, por exemplo) — mas na prática, hoje, nada grava um título prévio para uma chave
  preexistente por outro caminho, então o comportamento observável é idêntico a `=`. Mantive
  `setdefault` por ser estritamente mais seguro sem custo.

## Problemas ou preocupações

1. **Achado principal**: `validar_manifesto` não reconhece preexistentes e quebra a segunda rodada
   assim que o manifesto persiste um (ver seção dedicada acima). Recomendo tratar como próximo passo.
2. Segui uma instrução explícita do brief/prompt para mexer em `cli.py`, que não estava na lista
   "Arquivos" resumida do brief — documentado acima para o controlador confirmar que é o esperado.
3. O rótulo de título sintético para preexistentes
   (`"(item pré-existente, Azure Boards #{id})"`) é uma decisão minha, não pedida pelo brief; é
   necessária para o manifesto não estourar `ValueError` (título vazio é rejeitado), mas o texto exato
   é negociável.

## Commit

Commitei como pedido no Passo 5, com o assunto sugerido pelo brief.
