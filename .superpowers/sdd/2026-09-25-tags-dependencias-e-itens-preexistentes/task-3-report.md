# Relatório da Tarefa 3: `Depende de` — leitura e recusas do contrato

## O que foi implementado

Em **ambos** os pacotes (`publicar-backlog-azure-boards` e `publicar-backlog-demanda-azure-boards`):

1. `contrato_backlog.py`:
   - Novas constantes `DEPENDE_DE = "Depende de"` e `CHAVE_RE = re.compile(r"^[1-9]\d*\.\d+\.\d+$")`.
   - `DEPENDE_DE` acrescentado a `SECTION_NAMES` (por acréscimo, `TAGS` preservado).
   - `normalizar_chaves(bruto) -> (chaves, erros)`: irmã de `normalizar_tags`, mesma semântica
     "tudo ou nada" — qualquer erro zera os valores. Deduplica, recusa entrada vazia entre vírgulas
     e recusa valor que não bate com o formato `E.F.S`.
   - `detectar_ciclo(pares) -> list[str] | None`: DFS com três estados (não visitado / na pilha /
     concluído); ao encontrar um nó já na pilha, devolve a fatia da pilha a partir dele — cobre o
     ciclo de um nó (item que depende de si mesmo) porque a checagem usa o próprio estado do nó, não
     comparação de pares distintos.
   - `_validate_item` ganhou o parâmetro `folhas: set[str]` e passou a validar a seção `Depende de`:
     erro de formato (via `normalizar_chaves`), dependência para chave inexistente e dependência
     para item que não é folha.
   - `validate_backlog` agora calcula `folhas` uma vez e passa a `_validate_item`; ao final, roda
     `detectar_ciclo` sobre todos os itens e acrescenta um erro de ciclo quando encontrado.
   - `from collections.abc import Sequence` acrescentado ao topo para o tipo de `detectar_ciclo`.

2. `interpretar_markdown.py`:
   - `"Depende de"` acrescentado a `_SECOES` (por acréscimo).
   - Nova função `_dependencias_do_item(item)`, espelhando `_tags_do_item`: seção ausente devolve
     `()`; seção presente com erro de formato ou vazia recusa com `ErroContratoMarkdown`.
   - `_converter_item` passa a preencher `depende_de=_dependencias_do_item(item)`.
   - Import de `normalizar_chaves` acrescentado; a linha de import de `contrato_backlog` foi
     quebrada em múltiplas linhas porque, no pacote de Demanda, o nome do módulo é mais longo e a
     forma de uma linha só passaria de 100 colunas depois da substituição mecânica de nome de pacote
     que o teste de sincronia exige (ver "Achados da autorrevisão").

3. `modelos.py`: `ItemBacklog.depende_de: tuple[str, ...] = ()` acrescentado ao fim do dataclass,
   depois de `tags`, com default. `OperacaoCriacao` **não** foi tocado — o link no payload é da
   Tarefa 5.

Não toquei em `_conteudo_do_item` nem `_calcular_hash` em `planejar_publicacao.py` (Tarefa 4).

## Evidência de TDD

**RED** — comando (idêntico nos dois pacotes):
```
cd publicar-backlog-azure-boards && uv run pytest tests/test_contrato_dependencias.py -q
cd publicar-backlog-demanda-azure-boards && uv run pytest tests/test_contrato_dependencias.py -q
```
Saída (mesma causa nos dois):
```
ImportError: cannot import name 'detectar_ciclo' from '...contrato_backlog'
1 error in 0.05s
```

**GREEN** — depois da implementação, suíte completa de cada pacote:
```
cd publicar-backlog-azure-boards && uv run pytest -q && uv run ruff check . && uv run ruff format --check . && uv run mypy src
→ 160 passed in 0.25s / All checks passed! / 29 files already formatted / Success: no issues found in 13 source files

cd publicar-backlog-demanda-azure-boards && uv run pytest -q && uv run ruff check . && uv run ruff format --check . && uv run mypy src
→ 252 passed in 0.97s / All checks passed! / 37 files already formatted / Success: no issues found in 15 source files
```
`test_hash_nao_muda_para_backlog_sem_tags` (o literal de hash da Tarefa 2b) continua passando nos
dois pacotes — confirmado, não tocado.

## Arquivos alterados

- `publicar-backlog-azure-boards/src/publicar_backlog_azure_boards/contrato_backlog.py`
- `publicar-backlog-azure-boards/src/publicar_backlog_azure_boards/interpretar_markdown.py`
- `publicar-backlog-azure-boards/src/publicar_backlog_azure_boards/modelos.py`
- `publicar-backlog-azure-boards/tests/test_contrato_dependencias.py` (novo)
- `publicar-backlog-demanda-azure-boards/src/publicar_backlog_demanda_azure_boards/contrato_backlog.py`
- `publicar-backlog-demanda-azure-boards/src/publicar_backlog_demanda_azure_boards/interpretar_markdown.py`
- `publicar-backlog-demanda-azure-boards/src/publicar_backlog_demanda_azure_boards/modelos.py`
- `publicar-backlog-demanda-azure-boards/tests/test_contrato_dependencias.py` (novo)

O arquivo `.superpowers/sdd/.gitignore` (modificado antes de eu começar, fora do escopo desta
tarefa) foi deixado de fora do commit de propósito.

## Achados da autorrevisão

- Descobri, ao rodar a suíte do pacote de Demanda pela primeira vez, um teste que eu não conhecia
  pelo brief: `tests/test_sincronia_com_origem.py::test_modulo_espelhado_e_identico_ao_da_origem`,
  que exige que `contrato_backlog.py` e `interpretar_markdown.py` (entre outros) no pacote de
  Demanda sejam **exatamente** o conteúdo do pacote de origem com uma substituição mecânica de
  string (`publicar_backlog_azure_boards` → `publicar_backlog_demanda_azure_boards`). Minha primeira
  tentativa de import (`from ... import normalizar_chaves, normalizar_tags` em uma linha só) passava
  de 100 colunas depois dessa substituição, porque o nome do pacote de Demanda é 8 caracteres mais
  longo. Corrigi quebrando o import em múltiplas linhas **no arquivo de origem** (não só no
  espelhado), para que a substituição mecânica continue produzindo um arquivo válido nos dois
  lados — e então regerei o arquivo do pacote de Demanda por substituição de string a partir do
  arquivo de origem já corrigido, em vez de editar os dois manualmente. Reconfirmei depois que
  `diff` entre os dois arquivos mostra só as linhas de import (nome do pacote e do módulo).
- `contrato_backlog.py` ficou byte-a-byte idêntico entre os dois pacotes (sem nenhum import de
  módulo, então nem precisou de substituição) — conferido com `diff` antes de copiar.
- `_validate_item` ganhou `folhas` como terceiro parâmetro posicional (depois de `keys`), conforme
  o brief avisou que a assinatura ainda vai crescer na Tarefa 6; não presumi que essa é a forma
  final.
- O teste `test_detecta_item_que_depende_de_si_mesmo` de fato exercita o caso do "ciclo de um nó":
  a implementação de `detectar_ciclo` usa o estado do próprio nó (`na pilha` vs `concluído`), não
  comparação de pares distintos, então esse caso é pego corretamente — verifiquei isso lendo a
  lógica, não só vendo o teste passar.
- Linhas conferidas com `awk '{print length}' | sort -rn` em todos os arquivos tocados e criados;
  máximo encontrado foi 99 colunas (dentro do limite de 100).
- Não toquei em `OperacaoCriacao`, `planejar_publicacao.py`, `cliente_azure_devops.py` nem em
  `_conteudo_do_item`/`_calcular_hash` — confirmado por `git status` mostrando só os arquivos desta
  tarefa como modificados (fora do `.gitignore` pré-existente).
- Os testes novos verificam comportamento real: parsing e dedup de `normalizar_chaves`, detecção de
  ciclo de 1/2/3 nós e ausência de ciclo, e as duas recusas estruturais (chave inexistente, chave
  não-folha) via `validate_backlog` fim a fim com um backlog Markdown completo — não são testes
  triviais de estrutura de dados.

## Problemas ou preocupações

Nenhum problema bloqueante. A única superfície nova e não antecipada no brief foi o teste de
sincronia mecânica entre pacotes, que me obrigou a reformatar o import de origem — resolvido sem
alterar comportamento, só a formatação da linha de import.
