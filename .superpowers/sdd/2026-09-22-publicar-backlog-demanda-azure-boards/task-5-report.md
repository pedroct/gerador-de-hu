# Task 5 — Relatório: A Demanda entra no destino

## Rodada de correção 1/5

**Achado da revisão (Importante, escopo de teste):** as três guardas que fecham o vínculo
criptográfico com a Demanda — rejeição de manifesto sem `demanda_id`
(`manifesto.py:390-391`), rejeição de `demanda_id <= 0` (`configuracao.py::validar_demanda`) e
rejeição de `demanda_id` não numérico (`configuracao.py`, conversão de `bruto`) — não tinham
nenhum teste que as exercitasse. O Step 1 do brief fixou um conjunto de testes sem casos
negativos; o coordenador decidiu que o achado vale porque a garantia central da tarefa
("uma confirmação emitida para uma Demanda não pode publicar sob outra") depende dessas três
guardas continuarem existindo, e uma guarda sem teste desaparece no primeiro refactor sem que
ninguém note. Código de produção não foi tocado nesta rodada — a revisão já o considerou
correto.

### O que mudou

- **`tests/test_manifesto.py`** — novo teste `test_manifesto_sem_demanda_id_e_rejeitado`,
  inserido logo após `test_manifesto_e_gravado_e_lido_com_seus_metadados` (fica perto das
  outras verificações de formato de round-trip do manifesto, antes dos testes de
  reconciliação, que é onde a leitura de `destino` já é exercitada). Constrói um `destino`
  a partir de `destino_json()` com a chave `"demanda_id"` removida, grava um manifesto JSON
  bruto com esse destino e chama `ler_manifesto`. Como `ler_manifesto` envolve toda falha em
  `ValueError(f"O manifesto {caminho} é inválido.") from erro`, o teste verifica a mensagem
  externa (`match="é inválido"`) e adicionalmente afirma que a causa encadeada
  (`excinfo.value.__cause__`) contém `"Demanda de Negócio"` — a mensagem exata que
  `_configuracao` levanta. Isso evita um teste que passaria por acaso com qualquer erro de
  desserialização.
- **`tests/test_autorizacao.py`** — dois novos testes, `test_demanda_id_nao_positivo_e_rejeitado`
  e `test_demanda_id_nao_numerico_e_rejeitado`, colocados no final do arquivo, logo após
  `test_repr_da_configuracao_nao_expoe_token` (o último dos testes que já chamam
  `carregar_configuracao` diretamente com um dicionário `ambiente` — mesmo padrão, mesmo
  arquivo, sem criar um arquivo novo só para dois casos). Ambos chamam `carregar_configuracao`
  com `AZURE_DEVOPS_DEMANDA="0"` e `AZURE_DEVOPS_DEMANDA="abc"`, respectivamente. O primeiro
  afirma `pytest.raises(ErroConfiguracao)` e verifica que a causa encadeada contém
  `"positivo"` (mensagem do `field_validator("demanda_id")` do pydantic, que embrulha em
  `ValidationError` e é recapturada pelo `except ValueError` de `carregar_configuracao`); o
  segundo afirma `pytest.raises(ErroConfiguracao, match="número inteiro")`, que é a mensagem
  literal levantada pela conversão `int(str(bruto)...)`. Foi preciso importar
  `ErroConfiguracao` de `publicar_backlog_demanda_azure_boards.configuracao` nesse arquivo
  (import quebrado em duas linhas para caber em 100 colunas).

### Prova de que cada teste falha se a guarda for removida

Antes de considerar os testes bons, sabotei cada guarda isoladamente (fora do commit, restaurando
o arquivo original logo em seguida) e confirmei que o teste correspondente falha:

- **Guarda do manifesto** — troquei o bloco `demanda_id = destino.get("demanda_id"); if not
  isinstance(...): raise ValueError(...)` por `demanda_id = destino.get("demanda_id", 0) or 0`
  (aceita silenciosamente ausência/zero). Resultado:
  ```
  $ uv run pytest tests/test_manifesto.py -v -k demanda
  FAILED tests/test_manifesto.py::test_manifesto_sem_demanda_id_e_rejeitado - Failed: DID NOT RAISE <class 'ValueError'>
  ```
  Restaurado o arquivo original a partir de backup; suíte voltou a passar.
- **Guarda `validar_demanda` (`<= 0`)** — esvaziei o corpo do validador (`return valor` sem a
  checagem). Resultado:
  ```
  $ uv run pytest tests/test_autorizacao.py -v -k "demanda_id_nao_positivo"
  FAILED tests/test_autorizacao.py::test_demanda_id_nao_positivo_e_rejeitado - Failed: DID NOT RAISE <class '...ErroConfiguracao'>
  ```
  Restaurado o arquivo original a partir de backup.
- **Guarda de conversão não numérica** — troquei o bloco `try: demanda_id = int(...) except
  ValueError: raise ErroConfiguracao(...)` por um valor fixo `demanda_id = 1` (nunca falha).
  Resultado:
  ```
  $ uv run pytest tests/test_autorizacao.py -v -k "demanda_id_nao_numerico"
  FAILED tests/test_autorizacao.py::test_demanda_id_nao_numerico_e_rejeitado - Failed: DID NOT RAISE <class '...ErroConfiguracao'>
  ```
  Restaurado o arquivo original a partir de backup; `git diff` confirmou zero divergência de
  `src/` em relação ao commit anterior antes de prosseguir.

### Testes que cobrem a correção e comando rodado

Arquivos: `tests/test_manifesto.py` (17 testes, incluindo o novo) e
`tests/test_autorizacao.py` (27 testes, incluindo os dois novos).

```
$ uv run pytest tests/test_manifesto.py tests/test_autorizacao.py -v
...
tests/test_manifesto.py::test_manifesto_sem_demanda_id_e_rejeitado PASSED
...
tests/test_autorizacao.py::test_demanda_id_nao_positivo_e_rejeitado PASSED
tests/test_autorizacao.py::test_demanda_id_nao_numerico_e_rejeitado PASSED
```

Suíte inteira, uma vez, após restaurar o código de produção:
```
$ uv run pytest -q
........................................................................ [ 46%]
........................................................................ [ 92%]
............                                                             [100%]
156 passed in 0.30s
```
156 = 153 da rodada anterior + 3 novos desta rodada. Sem warnings.

Qualidade também revalidada:
```
$ uv run ruff check .        → All checks passed!
$ uv run mypy                → Success: no issues found in 14 source files
$ uv run bandit -c pyproject.toml -r src → No issues identified.
```

### Arquivos alterados nesta rodada

- `tests/test_manifesto.py`
- `tests/test_autorizacao.py`

Nenhum arquivo de produção foi tocado.

### Commit

`579dad1 test: cobre as guardas de demanda_id contra regressao`

---

## O que foi implementado, passo a passo

## O que foi implementado, passo a passo

**Step 1 — Testes que falham.** Criado `tests/test_demanda_no_destino.py` com o texto
literal do brief: três testes cobrindo (a) `demanda_id` obrigatório em
`ConfiguracaoPublicacao`, (b) impressões de destino diferentes para Demandas diferentes, e
(c) a dataclass `Demanda` carregando `titulo`/caminhos.

**Step 2 — RED confirmado.**
```
uv run pytest tests/test_demanda_no_destino.py -v
```
Saída: `ImportError: cannot import name 'Demanda' from 'publicar_backlog_demanda_azure_boards.modelos'`
— exatamente o esperado pelo brief, já que `Demanda` ainda não existia.

**Step 3 — `modelos.py`.** Acrescentada a dataclass congelada `Demanda(id, titulo, area_path,
iteration_path, url)` com a docstring do brief explicando por que `titulo`/`url` ficam fora de
hash, impressão e manifesto. Em `ConfiguracaoPublicacao`, acrescentado `demanda_id: int` **antes**
de `mapeamento_tipos`, sem valor padrão — `mapeamento_tipos` continua sendo o único campo com
default. Em `assinatura_plano`, a chave `"demanda_id"` entrou no dicionário `configuracao`.

**Step 4 — `planejar_publicacao.py`.** Em `_calcular_hash`, acrescentada a chave
`"demanda_id": configuracao.demanda_id` ao dicionário `configuracao`, ao lado de
`data_geracao` (que permanece intacta no hash).

**Step 5 — `autorizacao.py`.** `imprimir_destino` passou a incluir `demanda_id` no conteúdo
resumido. `criar_frase_confirmacao` passou a emitir `DEMANDA {id}` entre a contagem de itens e
o projeto: `"{inicio} {qtd} ITENS DEMANDA {id} {projeto} {area_path} {iteration_path} {hash4}"`.

**Step 6 — `manifesto.py`.** `_serializar_configuracao` grava `demanda_id`. `_configuracao`
(leitura) agora exige `demanda_id` como inteiro positivo não-booleano, rejeitando com
`ValueError("O destino do manifesto não identifica a Demanda de Negócio.")` qualquer manifesto
sem essa identidade — um manifesto antigo (sem o campo) é tratado como formato inválido, não como
"Demanda zero" silenciosa.

**Step 7 — `configuracao.py`.** `ConfiguracaoAzureDevOps` ganhou `demanda_id: int` (obrigatório)
e `tipo_demanda: str = "Demanda de Negócio"`. Novo `field_validator("demanda_id")` rejeita valores
`<= 0`. `"tipo_demanda"` entrou na lista do validador de texto obrigatório. A property
`publicacao` agora passa `demanda_id=self.demanda_id` na construção de `ConfiguracaoPublicacao`.
`_CHAVES` ganhou `"demanda_id": "AZURE_DEVOPS_DEMANDA"` e `"tipo_demanda": "AZURE_DEVOPS_TIPO_DEMANDA"`.
Em `carregar_configuracao`: a tupla `campos` ganhou `"demanda_id"` e `"tipo_demanda"`;
`tipos_padrao` ganhou `"tipo_demanda": "Demanda de Negócio"`; um bloco novo resolve
`demanda_id` (pergunta interativa se ausente, converte para `int` aceitando prefixo `#`, e
levanta `ErroConfiguracao` com mensagem em português se não for um inteiro); o rótulo
`"demanda_id": "ID da Demanda de Negócio"` entrou em `_perguntar`; a construção final de
`ConfiguracaoAzureDevOps` passa `demanda_id=demanda_id` e
`tipo_demanda=_exigir_valor(valores["tipo_demanda"], "Tipo remoto da Demanda")`.
`area_path`/`iteration_path` permanecem intocados (Task 10 os remove).

**Step 8 — `cli.py`.** `_adicionar_opcoes_configuracao` ganhou
`parser.add_argument("--demanda", dest="demanda_id")` e `parser.add_argument("--tipo-demanda")`.
A tupla `nomes` de `_carregar_configuracao` ganhou `"demanda_id"` e `"tipo_demanda"`.
Os argumentos `--area-path`/`--iteration-path` permanecem (Task 10 os remove).

**Step 9 — Suíte herdada corrigida** (detalhes na seção própria abaixo).

**Step 10 — Commit.** `a6a19d2 feat: vincula o destino da publicacao a uma Demanda de Negocio`.

## Evidência TDD

**RED:**
```
$ uv run pytest tests/test_demanda_no_destino.py -v
...
ImportError: cannot import name 'Demanda' from 'publicar_backlog_demanda_azure_boards.modelos'
(.../src/publicar_backlog_demanda_azure_boards/modelos.py)
=========================== short test summary info ============================
ERROR tests/test_demanda_no_destino.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
```
Esperado porque `Demanda` e `demanda_id` ainda não existiam em `modelos.py` — confirma que o
teste está exercitando código que falta, não um erro de digitação no próprio teste.

**GREEN (arquivo novo isolado, após Steps 3–8):**
```
$ uv run pytest tests/test_demanda_no_destino.py -v
tests/test_demanda_no_destino.py::test_demanda_id_e_obrigatorio_no_destino PASSED
tests/test_demanda_no_destino.py::test_destinos_com_demandas_diferentes_tem_impressoes_diferentes PASSED
tests/test_demanda_no_destino.py::test_demanda_carrega_titulo_e_caminhos_para_derivar_o_destino PASSED
3 passed in 0.02s
```

**RED da suíte inteira (logo após os Steps 3–8, antes do Step 9):**
```
$ uv run pytest
collected 53 items / 7 errors
ERROR tests/test_autorizacao.py - TypeError: ConfiguracaoPublicacao.__init__() missing 1 required positional argument: 'demanda_id'
ERROR tests/test_cliente_azure_devops.py - TypeError: ...
ERROR tests/test_executar_publicacao.py - TypeError: ...
ERROR tests/test_integracao_final.py - TypeError: ...
ERROR tests/test_manifesto.py - TypeError: ...
ERROR tests/test_planejar_publicacao.py - TypeError: ...
ERROR tests/test_skill_integration.py - TypeError: ...
!!!!!!!!!!!!!!!!!!! Interrupted: 7 errors during collection !!!!!!!!!!!!!!!!!!!!
```
Exatamente o efeito esperado: `demanda_id` sem default quebra toda construção posicional
antiga de `ConfiguracaoPublicacao`.

**GREEN da suíte inteira (após Step 9):**
```
$ uv run pytest -q
........................................................................ [ 47%]
........................................................................ [ 94%]
.........                                                                [100%]
153 passed in 0.33s
```
150 testes herdados + 3 novos de `test_demanda_no_destino.py` = 153. Sem warnings.

## Testes herdados corrigidos (Step 9)

- **`tests/test_planejar_publicacao.py`** — `CONFIGURACAO` (kwargs) ganhou `demanda_id=13959`.
- **`tests/test_cliente_azure_devops.py`** — `CONFIGURACAO` (posicional) ganhou `13959` como
  5º argumento posicional (antes de `mapeamento_tipos`, que mantém o default).
- **`tests/test_executar_publicacao.py`** — idem, `CONFIGURACAO` posicional ganhou `13959`.
- **`tests/test_integracao_final.py`** — idem; linha quebrada em duas para caber em 100
  colunas (ruff `E501`).
- **`tests/test_manifesto.py`** — `CONFIGURACAO` posicional ganhou `13959`; a função auxiliar
  `destino_json()` ganhou `"demanda_id": 13959` no dicionário; a asserção de round-trip que
  compara `dados["reconciliacoes"]["1.0.0"]["destino"]` a um dicionário literal também ganhou
  `"demanda_id": 13959` (asserção não foi afrouxada — apenas completada com o campo novo).
- **`tests/test_skill_integration.py`** — `CONFIGURACAO` posicional ganhou `13959` (linha
  quebrada por `E501`); os dois testes que chamam `principal(...)` sem `cliente` injetado, com
  `--organizacao`/`--projeto`/`--area-path`/`--iteration-path` explícitos, ganharam
  `"--demanda", "13959"` no argv — sem isso, `carregar_configuracao` tentaria perguntar
  `demanda_id` interativamente e encontraria `entrada=StringIO()` vazio, falhando com
  `ErroConfiguracao("A entrada interativa foi encerrada...")`. O terceiro teste que usa
  `--organizacao`/etc (`test_validador_estrutural_existente_bloqueia_antes_do_planejamento`) não
  precisou de `--demanda`: ele usa um backlog estruturalmente inválido, que é rejeitado por
  `validar_estrutura_backlog` antes de `_carregar_configuracao` ser sequer chamado — verifiquei
  isso lendo o fluxo de `principal()` antes de decidir não tocar nesse teste.
- **`tests/test_autorizacao.py`** — `CONFIGURACAO` (kwargs) ganhou `demanda_id=13959`; a
  asserção literal da frase de lote mudou de
  `"AUTORIZAR LOTE 2 1 ITENS Projeto Projeto Projeto\\Sprint 18 7F3A"` para
  `"AUTORIZAR LOTE 2 1 ITENS DEMANDA 13959 Projeto Projeto Projeto\\Sprint 18 7F3A"`
  (único teste com a frase inteira hard-coded; os demais usam `criar_frase_confirmacao`
  dinamicamente e não precisaram de mudança). Os 7 testes que chamam `carregar_configuracao(...)`
  diretamente ganharam `"AZURE_DEVOPS_DEMANDA": "13959"` no dicionário `ambiente` — sem isso, a
  ausência do valor dispararia a pergunta interativa contra um `entrada` já roteirizado para
  outro propósito (escolha de area path, leitura de token, etc.), quebrando esses fluxos.
- **`tests/test_configuracao_projeto.py`** — o único teste que chama `carregar_configuracao`
  ganhou `"AZURE_DEVOPS_DEMANDA": "13959"` no `ambiente`, pelo mesmo motivo.

Nenhuma asserção de comportamento foi enfraquecida: todas as mudanças ou completam um literal
de destino com o campo novo, ou fornecem o valor de `demanda_id` pelo canal apropriado
(argumento, ambiente ou kwarg) para que o teste continue exercitando exatamente o que
exercitava antes.

## Arquivos alterados

Produção:
- `src/publicar_backlog_demanda_azure_boards/modelos.py`
- `src/publicar_backlog_demanda_azure_boards/autorizacao.py`
- `src/publicar_backlog_demanda_azure_boards/manifesto.py`
- `src/publicar_backlog_demanda_azure_boards/configuracao.py`
- `src/publicar_backlog_demanda_azure_boards/cli.py`
- `src/publicar_backlog_demanda_azure_boards/planejar_publicacao.py`

Testes:
- `tests/test_demanda_no_destino.py` (novo)
- `tests/test_manifesto.py`
- `tests/test_autorizacao.py`
- `tests/test_configuracao_projeto.py`
- `tests/test_planejar_publicacao.py`
- `tests/test_cliente_azure_devops.py`
- `tests/test_executar_publicacao.py`
- `tests/test_integracao_final.py`
- `tests/test_skill_integration.py`

Nenhum arquivo guardado por `test_sincronia_com_origem.py`
(`contrato_backlog.py`, `converter_para_html.py`, `interpretar_markdown.py`,
`validacao_estrutural.py`) foi tocado.

## Verificação de qualidade

```
$ uv run ruff check .        → All checks passed!
$ uv run mypy                → Success: no issues found in 14 source files
$ uv run bandit -c pyproject.toml -r src → No issues identified.
```
O hook `ruff-format` do pre-commit reformatou uma linha em `configuracao.py` (a mensagem de
erro do `ErroConfiguracao` de conversão de `demanda_id`, que eu havia quebrado em três linhas
sem necessidade — cabia em uma). Reexecutei a suíte (153 passed) antes de recommitar.

## Autorrevisão

- **Completude:** os 10 Steps foram executados. `demanda_id` está no hash
  (`planejar_publicacao.py::_calcular_hash`), na assinatura (`modelos.py::assinatura_plano`),
  na impressão de destino e na frase (`autorizacao.py`), no manifesto — gravação
  (`_serializar_configuracao`) e leitura/validação (`_configuracao`) —, na configuração
  (`ConfiguracaoAzureDevOps`, `carregar_configuracao`) e na CLI (`--demanda`, `--tipo-demanda`).
- **Qualidade:** nomes seguem a convenção existente (`demanda_id`, `tipo_demanda`); tipagem
  passa `mypy --strict` sem `# type: ignore` novo (o único `# type: ignore[call-arg]` é do
  próprio brief, no teste que verifica a ausência de default); mensagens de erro dizem o que
  falta e em que unidade (`"O ID da Demanda de Negócio deve ser um número inteiro."`,
  `"O destino do manifesto não identifica a Demanda de Negócio."`).
- **Disciplina:** não toquei `area_path`/`iteration_path` em `ConfiguracaoAzureDevOps`, não
  troquei `publicacao` por `publicacao_para(demanda)`, não removi os argumentos de CLI
  `--area-path`/`--iteration-path`, não criei `leitor_demanda.py`, não mudei
  `validar_operacao` nem pendurei Épicos na Demanda — tudo isso fica para as Tasks 7–10.
  `ConfiguracaoPublicacao.demanda_id` não tem valor padrão.
- **Testes:** os novos testes exercitam comportamento real (impressões distintas por Demanda,
  obrigatoriedade do campo, carga da dataclass `Demanda`); a suíte inteira roda limpa, sem
  warnings; nenhuma asserção herdada foi afrouxada — só completada ou alimentada pelo canal
  correto.

## Preocupações

- `configuracao.py` já era um arquivo com bastante lógica de precedência
  (argumento → arquivo → ambiente → pergunta) antes desta tarefa; acrescentar mais um campo
  seguiu o padrão existente, mas o arquivo está ficando longo (301 linhas) e cada novo campo
  obrigatório (como `demanda_id`, diferente dos campos com default) precisa de um bloco de
  resolução manual próprio (linhas 166–174) em vez de caber no loop genérico de `tipos_padrao`.
  Isso é uma observação de manutenibilidade, não um problema desta tarefa — não refatorei a
  função por estar fora do escopo do Step 7.
- `_apresentar_plano` em `cli.py` (saída textual do plano para o usuário) ainda não exibe
  `demanda_id` explicitamente na tela, só implicitamente via `Hash do plano`. O brief não pediu
  isso no Step 8 e nenhum teste cobra essa exibição, então não adicionei — mas é um ponto que
  as Tasks seguintes (8, 9 ou 10, que já consultam `configuracao.demanda_id`) podem querer
  revisitar para a experiência do operador.
