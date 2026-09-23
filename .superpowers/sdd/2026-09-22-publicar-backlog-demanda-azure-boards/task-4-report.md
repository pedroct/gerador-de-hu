# Task 4: O plano passa a usar o título hierárquico — Relatório

## O que foi implementado

Em `planejar_publicacao.py`:

- Importado `montar_titulo` de `publicar_backlog_demanda_azure_boards.titulo_hierarquico`.
- `_criar_operacao` deixou de receber `data_geracao` e de montar o título com
  `f"{data_geracao} {item.chave} {item.titulo_curto or item.titulo}"`; agora chama
  `montar_titulo(item)`.
- A chamada em `criar_plano` foi ajustada para `_criar_operacao(item, configuracao)`.
- `criar_plano(itens, configuracao, data_geracao)` manteve a assinatura inalterada.
  `data_geracao` continua sendo passado para `_calcular_hash` — nada mudou ali.

Em `tests/test_planejar_publicacao.py`:

- Este arquivo não tem fixture `configuracao_exemplo`; os testes existentes já usam a constante de
  módulo `CONFIGURACAO`. Segui a instrução de fallback do brief e reaproveitei essa construção local
  nos dois novos testes, em vez de introduzir uma fixture nova fora do escopo da tarefa.
- Adicionados os dois testes do Step 1 do brief (adaptados para usar `CONFIGURACAO` em vez de
  `configuracao_exemplo`): `test_titulo_usa_numeracao_hierarquica_sem_data` e
  `test_data_de_geracao_continua_no_hash`.
- Corrigidos os dois testes herdados que afirmavam o título datado (ver seção própria abaixo).

## Evidência TDD

### RED

Comando:
```
uv run pytest tests/test_planejar_publicacao.py -v
```

Saída (trecho relevante, antes do Step 3):
```
tests/test_planejar_publicacao.py::test_titulo_usa_numeracao_hierarquica_sem_data FAILED [ 80%]
...
>       assert titulos["1.0.0"] == "01 Gestão do projeto"
E       AssertionError: assert '2026-09-22 1...ão do projeto' == '01 Gestão do projeto'
E
E         - 01 Gestão do projeto
E         + 2026-09-22 1.0.0 Gestão do projeto

1 failed, 9 passed in 0.06s
```

Falha esperada: o título ainda vinha prefixado pela data (`2026-09-22 1.0.0 ...`), confirmando que a
montagem antiga (`f"{data_geracao} {item.chave} ..."`) continuava em uso antes da Task 3 ser
consumida. Os demais 9 testes do arquivo passaram porque ainda afirmavam o formato antigo (inclusive
os dois que precisariam ser corrigidos no Step 4 — eles não falharam nesse ponto porque a mudança de
código ainda não tinha sido aplicada; a falha deles só apareceria depois do Step 3, e foi corrigida
junto no Step 4 antes de rodar a suíte completa).

### GREEN

Comando:
```
uv run pytest -v
```

Saída (fim):
```
tests/test_planejar_publicacao.py::test_plano_ordena_epic_feature_e_folha PASSED
tests/test_planejar_publicacao.py::test_plano_preserva_backlog_completo_para_validar_retomada PASSED
tests/test_planejar_publicacao.py::test_plano_converte_apenas_campos_copiaveis_e_inclui_pai PASSED
tests/test_planejar_publicacao.py::test_operacao_usa_titulo_com_numeracao_hierarquica PASSED
tests/test_planejar_publicacao.py::test_operacao_usa_titulo_curto_quando_declarado PASSED
tests/test_planejar_publicacao.py::test_hash_muda_quando_destino_muda PASSED
tests/test_planejar_publicacao.py::test_hash_muda_quando_data_de_geracao_muda PASSED
tests/test_planejar_publicacao.py::test_titulo_usa_numeracao_hierarquica_sem_data PASSED
tests/test_planejar_publicacao.py::test_data_de_geracao_continua_no_hash PASSED
tests/test_planejar_publicacao.py::test_mapeamento_product_backlog_item_integra_operacao_e_hash PASSED
...
============================= 150 passed in 0.26s ==============================
```

## Suíte inteira (contagem final)

Comando: `uv run pytest -q`

```
........................................................................ [ 48%]
........................................................................ [ 96%]
......                                                                   [100%]
150 passed in 0.29s
```

A suíte estava em **148 testes** antes desta tarefa. Agora está em **150**: os dois testes novos do
Step 1 (`test_titulo_usa_numeracao_hierarquica_sem_data` e `test_data_de_geracao_continua_no_hash`)
foram adicionados; nenhum teste existente foi removido ou desativado. 148 + 2 = 150, confere.

## Testes herdados corrigidos (Step 4)

Busca usada: `grep -rn '2026-\|data_geracao' tests/*.py | grep -i titulo`, mais uma checagem adicional
por `grep -rn "titulo =="` e por padrão de data literal em todos os `tests/*.py` para garantir que
nenhuma outra ocorrência escapasse. Resultado: só havia duas afirmações do título datado, ambas em
`tests/test_planejar_publicacao.py`:

1. `test_operacao_prefixa_titulo_com_data_de_geracao_e_chave_documental` (renomeado para
   `test_operacao_usa_titulo_com_numeracao_hierarquica`, já que o nome antigo descrevia o
   comportamento removido) — asserção trocada de
   `historia.titulo == "2026-09-16 1.1.1 História"` para `historia.titulo == "01.01.01 História"`.
2. `test_operacao_usa_titulo_curto_quando_declarado` — asserção trocada de
   `plano.operacoes[0].titulo == "2026-09-16 1.1.1 História curta"` para
   `plano.operacoes[0].titulo == "01.01.01 História curta"`.

Em ambos os casos a chave é `1.1.1`, que `numerar()` converte para `01.01.01` — verificado batendo
com os casos de teste de `test_titulo_hierarquico.py` (`1.1.1` → `01.01.01`).

Outras ocorrências de datas em `tests/test_manifesto.py` e `tests/test_executar_publicacao.py`
(`"2026-09-16T15:00:00+00:00"`) são timestamps de reconciliação, não têm relação com título e não
foram tocadas.

Nenhuma asserção foi afrouxada: todas continuam checando igualdade exata (`==`), nenhuma virou `in`,
nenhum `xfail` foi usado.

## Arquivos alterados

- `publicar-backlog-demanda-azure-boards/src/publicar_backlog_demanda_azure_boards/planejar_publicacao.py`
- `publicar-backlog-demanda-azure-boards/tests/test_planejar_publicacao.py`

Os quatro módulos protegidos pelo teste-guarda (`contrato_backlog.py`, `converter_para_html.py`,
`interpretar_markdown.py`, `validacao_estrutural.py`) não foram tocados —
`test_sincronia_com_origem.py` continua verde.

## Checagens de qualidade

```
uv run ruff check src tests   → All checks passed!
uv run mypy src                → Success: no issues found in 14 source files
uv run bandit -r src -q        → (sem achados)
```

Hooks de pre-commit (ruff, ruff-format, mypy strict, bandit, commitizen) rodaram no commit e
passaram todos.

## Commit

`f75582a feat: publica titulos com numeracao hierarquica`
(2 arquivos alterados: `planejar_publicacao.py` e `test_planejar_publicacao.py`)

## Autorrevisão

- **Completude:** os 6 Steps do brief foram seguidos na ordem (RED → troca de código → correção dos
  herdados → suíte inteira → commit). Busquei todas as ocorrências de título datado com grep amplo,
  não só as que quebraram primeiro — confirmei que só existiam duas.
- **Qualidade:** `_criar_operacao` ficou mais simples (uma linha a menos de assinatura, um parâmetro
  a menos). Renomeei o teste cujo nome descrevia o comportamento antigo removido, para não deixar
  uma afirmação certa com um nome enganoso.
- **Disciplina:** não toquei nos quatro módulos protegidos, não alterei `titulo_hierarquico.py` (é
  entrega da Task 3, só consumi `montar_titulo`), não introduzi fixture nova nem reestruturei nada
  fora do escopo. `criar_plano` manteve assinatura e `data_geracao` continua no hash
  (`test_data_de_geracao_continua_no_hash` e `test_hash_muda_quando_data_de_geracao_muda` provam
  isso nas duas pontas: teste novo e teste herdado).
- **Testes:** todas as asserções novas e corrigidas verificam o valor real de `titulo`/`hash_plano`
  produzido, sem enfraquecimento. Saída da suíte sem warnings.

## Preocupações

Nenhuma. A mudança foi pontual e todos os testes relevantes (novos, herdados corrigidos e o
teste-guarda de sincronia) passam.
