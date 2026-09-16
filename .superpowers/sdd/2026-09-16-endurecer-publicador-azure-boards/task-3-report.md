# Relatório — Task 3: Tornar o validador estrutural realmente isolável

## Resultado

O validador estrutural agora está disponível no próprio pacote do publicador. `validar_estrutura_backlog`
não importa mais scripts por caminho absoluto nem procura o diretório irmão `gerar-backlog-azure-boards`;
um wheel instalado consegue validar o backlog de forma isolada.

A lógica determinística de parsing e validação foi extraída para `contrato_backlog.py`, preservando as
regras de origem, `Refinement Status`, `Card`, `Conversation`, hierarquia, numeração, campos obrigatórios
e headings de itens. A CLI já executava essa validação antes da interpretação, planejamento,
autorização e criação do cliente, portanto não precisou de alteração. O `pyproject.toml` já declarava o
pacote completo em `tool.hatch.build.targets.wheel.packages`, incluindo automaticamente o novo módulo.

## Ciclos RED/GREEN

### RED

Comando:

```text
uv run pytest tests/test_validacao_estrutural.py tests/test_instalacao.py -q
```

Saída inicial:

```text
4 passed, 2 failed
```

As falhas reproduziram a dependência do diretório irmão e a ausência do módulo empacotado.

### GREEN

Após adicionar o contrato ao pacote e alterar o adaptador da validação:

```text
uv run pytest tests/test_validacao_estrutural.py tests/test_instalacao.py -q
6 passed
```

## Wheel real

```text
uv build
Successfully built dist/publicar_backlog_azure_boards-0.1.0-py3-none-any.whl

uv venv /tmp/publicador-wheel-test
uv pip install --python /tmp/publicador-wheel-test/bin/python dist/*.whl
/tmp/publicador-wheel-test/bin/publicar-backlog-azure-boards validar <fixture>
Backlog válido: 3 itens.
```

A validação também foi executada com o diretório de trabalho em `/tmp`, fora do checkout, e passou.

## Verificações finais

```text
uv run pytest -q
103 passed

uv run ruff check src tests
All checks passed!

uv run ruff format --check src tests
24 files already formatted

uv run mypy src
Success: no issues found in 13 source files

uv run bandit -r src
No issues identified.

git diff --check
saída vazia; sem erros de espaço em branco
```

## Arquivos alterados

- `publicar-backlog-azure-boards/src/publicar_backlog_azure_boards/contrato_backlog.py`: novo módulo
  empacotável com o contrato estrutural determinístico.
- `publicar-backlog-azure-boards/src/publicar_backlog_azure_boards/validacao_estrutural.py`: remove o
  carregamento dinâmico do checkout irmão e delega ao contrato empacotado.
- `publicar-backlog-azure-boards/tests/test_validacao_estrutural.py`: regressões de origem, status,
  headings, fixture válido e isolamento de filesystem.
- `publicar-backlog-azure-boards/tests/test_instalacao.py`: confirma que o módulo do contrato é
  importável pelo pacote.
- `pyproject.toml` e `cli.py` foram inspecionados e permaneceram sem alteração porque já atendiam ao
  empacotamento e à ordem de validação exigidos.

## Preocupações

Não há bloqueadores conhecidos. Como o contrato foi copiado do script da skill geradora, mudanças
futuras nas regras desse script precisarão ser refletidas também no módulo empacotado. O diretório
não rastreado preexistente `graphify-out/` não foi incluído nem alterado, e não foram despachados
subagentes ou revisores.
