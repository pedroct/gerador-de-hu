# Relatório — Tarefa 8: checagem cruzada do `demanda_id`

## O que foi implementado

Só no pacote `publicar-backlog-demanda-azure-boards` (esta é a única tarefa assimétrica):

### `executar_publicacao.py` (não `interpretar_markdown.py` — ver seção dedicada abaixo)

- `_DEMANDA_ORIGEM_RE` / `_DEMANDA_ID_RE`: mesmos padrões do brief.
- `extrair_demanda_origem(caminho: Path) -> int | None`: lê `Demanda de Negócio de origem` dos
  Metadados; devolve `None` para `Não se aplica`, levanta `ErroContratoMarkdown` (importado de
  `interpretar_markdown`) quando o metadado está ausente ou em formato inválido.
- `conferir_demanda_de_origem(caminho: Path, demanda_id: int) -> None`: recusa com `ValueError`
  quando o backlog declara `Não se aplica`, ou quando o ID declarado diverge do `demanda_id`
  configurado. A mensagem de divergência nomeia os dois valores: `"O backlog declara a Demanda
  #{declarada}, e a configuração informa #{demanda_id}."` — sem flag de sobreposição, por
  desenho (ver docstring da função).

### `cli.py`

- Import de `conferir_demanda_de_origem` acrescentado ao já existente de `executar_plano`.
- Chamada `conferir_demanda_de_origem(argumentos_parseados.backlog, destino.demanda_id)`
  inserida em `principal()`, imediatamente antes de `_verificar_preliminar(...)` — mesmo ponto
  do fluxo onde a Tarefa 7b acrescentou `verificar_item_existente`, e antes de qualquer chamada
  remota, de `_avisar_criterios_descartados` e de `_publicar` (autorização). Só executa no
  caminho `publicar` sem `--simulacao` (o único que de fato cria itens); `validar`, `planejar` e
  `--simulacao` retornam antes desse ponto e continuam sem a checagem, porque nenhum deles
  escreve.

Optei por **não** inserir a chamada dentro do corpo de `_verificar_preliminar` (que ganharia um
parâmetro `caminho_backlog` obrigatório): isso quebraria três testes existentes que chamam
`_verificar_preliminar` diretamente com um `plano` sintético sem arquivo de backlog real
(`test_cli.py::test_verificacao_preliminar_*` e
`test_skill_integration.py::test_verificacao_preliminar_valida_epicos_contra_a_demanda`). Chamar
a checagem em `principal()`, logo antes de invocar `_verificar_preliminar`, produz exatamente o
mesmo comportamento observável (mesma ordem, mesmo texto de erro, mesmo "antes de qualquer
escrita e antes de autorização") sem alterar a assinatura de uma função testada isoladamente por
outros cenários.

### Fixture (efeito colateral necessário, não escopo novo)

`tests/fixtures/valid-backlog.md` ganhou `- Demanda de Negócio de origem: `#13959`` — o mesmo
`demanda_id` já usado por `ConfiguracaoPublicacao` em `test_integracao_final.py` e
`test_skill_integration.py`. Sem essa linha, todo teste que executa `principal(["publicar", ...])`
até o fim (inclusive `--validar-apenas`) passaria a falhar com
`ErroContratoMarkdown: ... não possui Demanda de Negócio de origem`, porque o campo passou a ser
obrigatório no caminho de publicação real. Confirmei que nenhum teste depende do conteúdo textual
exato da seção de Metadados além das extrações pontuais (`extrair_data_geracao`), e que o parser
de itens (`interpretar_backlog`) ignora linhas de metadado fora de uma seção reconhecida — a
adição é inócua para todo o resto da suíte. A fixture homônima do pacote de origem
(`publicar-backlog-azure-boards`) **não** foi tocada; não há teste de sincronia entre as duas
fixtures (só entre os módulos `.py` listados em `MODULOS_ESPELHADOS`), e é esperado que divirjam
agora, pela mesma razão de fundo desta tarefa.

## Onde ficou `extrair_demanda_origem` e por quê

**Em `executar_publicacao.py`, não em `interpretar_markdown.py`.**

`test_sincronia_com_origem.py` exige que `interpretar_markdown.py` do pacote de Demanda seja
byte a byte igual ao do pacote de origem (só com o nome do pacote substituído). O pacote de
origem **não pode** ganhar `extrair_demanda_origem` nem a recusa — é exatamente o que o teste de
não-regressão em `publicar-backlog-azure-boards/tests/test_interpretar_markdown.py` prova. Se eu
tivesse posto a função em `interpretar_markdown.py` só do lado de Demanda, os dois arquivos
divergiriam e `test_modulo_espelhado_e_identico_ao_da_origem[interpretar_markdown.py]` quebraria
— violando a restrição explícita "Não quebre o teste de sincronia".

`executar_publicacao.py` não está em `MODULOS_ESPELHADOS`; já é um módulo exclusivo do pacote de
Demanda (não existe equivalente no pacote solto), e o próprio brief já pedia que
`conferir_demanda_de_origem` vivesse lá (confirmado pelo `import` do teste-modelo do brief). Pôr
as duas funções juntas nesse módulo resolve a tensão sem criar um módulo novo (o brief não pediu
um, e um módulo a mais só para duas funções pequenas seria YAGNI).

## Evidência de TDD

### RED — antes de implementar

```
$ cd publicar-backlog-demanda-azure-boards && uv run pytest tests/test_demanda_de_origem.py -q
ImportError while importing test module '.../tests/test_demanda_de_origem.py'.
E   ImportError: cannot import name 'conferir_demanda_de_origem' from
    'publicar_backlog_demanda_azure_boards.executar_publicacao'
1 error in 0.13s
```

(O teste de não-regressão em `publicar-backlog-azure-boards/tests/test_interpretar_markdown.py`
já nasceu verde — é isso que "não-regressão" significa; confirmado isoladamente antes de qualquer
mudança de produção: `18 passed`.)

### GREEN — depois de implementar

```
$ cd publicar-backlog-demanda-azure-boards && uv run pytest tests/test_demanda_de_origem.py -q
......                                                                   [100%]
6 passed in 0.10s
```

### Suíte inteira dos dois pacotes, incluindo sincronia e o invariante protegido

```
$ cd publicar-backlog-demanda-azure-boards && uv run pytest -q
........................................................................ [ 23%]
........................................................................ [ 47%]
........................................................................ [ 71%]
........................................................................ [ 95%]
.............                                                            [100%]
301 passed in 1.01s

$ uv run pytest -q -k test_hash_nao_muda_para_backlog_sem_tags
.                                                                        [100%]
1 passed, 300 deselected in 0.16s

$ uv run pytest tests/test_sincronia_com_origem.py -q
.....                                                                    [100%]
5 passed in 0.01s

$ cd ../publicar-backlog-azure-boards && uv run pytest -q
........................................................................ [ 35%]
........................................................................ [ 70%]
............................................................             [100%]
204 passed in 0.35s
```

`test_hash_nao_muda_para_backlog_sem_tags` passou sem qualquer alteração — o invariante não foi
tocado.

### Qualidade

```
$ (nos dois pacotes) uv run ruff check .        -> All checks passed!
$ (nos dois pacotes) uv run ruff format --check . -> all formatted (após uv run ruff format .)
$ (nos dois pacotes) uv run mypy src            -> Success: no issues found
```

Todas as linhas ficaram dentro de 100 colunas em caracteres (conferido com `len()` em Python, não
por contagem de bytes — que inflava por causa dos acentos).

## Arquivos alterados

- `publicar-backlog-demanda-azure-boards/src/publicar_backlog_demanda_azure_boards/executar_publicacao.py`
  (novo: `extrair_demanda_origem`, `conferir_demanda_de_origem`)
- `publicar-backlog-demanda-azure-boards/src/publicar_backlog_demanda_azure_boards/cli.py`
  (import + chamada em `principal`)
- `publicar-backlog-demanda-azure-boards/tests/test_demanda_de_origem.py` (novo)
- `publicar-backlog-demanda-azure-boards/tests/fixtures/valid-backlog.md` (linha de metadado
  acrescentada)
- `publicar-backlog-azure-boards/tests/test_interpretar_markdown.py` (teste de não-regressão)

## Achados da autorrevisão

- O brief sugeria os testes de `conferir_demanda_de_origem` e `extrair_demanda_origem`
  importando de `interpretar_markdown`; adaptei os imports para `executar_publicacao` pela razão
  de sincronia acima, mantendo o resto do teste (nomes, casos, mensagens) idêntico ao brief.
  `ErroContratoMarkdown` continua vindo de `interpretar_markdown` (fonte única da exceção).
- Cogitei colocar a chamada dentro de `_verificar_preliminar` (como a Tarefa 7b fez com
  `verificar_item_existente`), mas isso exigiria um parâmetro novo obrigatório e quebraria
  testes unitários existentes que chamam essa função isoladamente sem arquivo de backlog.
  Chamar em `principal()`, logo antes, preserva o mesmo ponto lógico do fluxo sem esse custo.
  Documentei a divergência acima.
- Revisei se a linha nova na fixture afeta algum teste que dependa do conteúdo textual exato dos
  Metadados — não encontrei nenhum (só `extrair_data_geracao`, que usa regex própria e ignora o
  resto da seção).
- Nenhuma flag de sobreposição foi criada, conforme restrição.
- `SKILL.md`/`README.md` não foram atualizados para mencionar o novo metadado obrigatório — não
  há teste que exija isso e o brief não pediu; decidi não fazer por YAGNI, mas sinalizo aqui para
  o controlador julgar se vale abrir um item de documentação separado.

## Problemas ou preocupações

Nenhum bloqueio. A única preocupação registrada é a de documentação (`SKILL.md`/`README.md`) não
mencionar o campo `Demanda de Negócio de origem` como obrigatório para publicar de verdade —
decisão consciente de escopo, não uma lacuna descoberta tarde demais.
