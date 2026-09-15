# Relatório da Tarefa 6

## Resultado

Implementados o manifesto JSON versionado, a gravação atômica, a publicação sequencial e a
retomada segura após falha parcial.

Arquivos criados:

- `publicar-backlog-azure-boards/src/publicar_backlog_azure_boards/manifesto.py`
- `publicar-backlog-azure-boards/src/publicar_backlog_azure_boards/executar_publicacao.py`
- `publicar-backlog-azure-boards/tests/test_manifesto.py`
- `publicar-backlog-azure-boards/tests/test_executar_publicacao.py`

O manifesto preserva registros existentes, identifica o plano e o destino, e armazena o título
junto da identidade de cada item. Antes de ignorar um item já registrado, o executor confere hash,
destino, chave, tipo e título. A criação de filhos usa o ID do pai já registrado. Falhas param a
execução sem rollback, exclusão ou atualização.

## RED/GREEN

RED:

```text
uv run pytest tests/test_manifesto.py tests/test_executar_publicacao.py -v
2 erros de coleta: ModuleNotFoundError para manifesto e executar_publicacao
```

GREEN:

```text
uv run pytest tests/test_manifesto.py tests/test_executar_publicacao.py -v
6 passed in 0.09s
```

## Verificação

```text
uv run pytest -v
61 passed in 0.19s

uv run ruff check .
All checks passed!

uv run mypy
Success: no issues found in 10 source files

git diff --check
sem saída (sucesso)
```

Os testes cobrem manifesto inexistente, leitura e gravação dos metadados, substituição atômica,
gravação após cada sucesso, parada no segundo item com retomada sem duplicação e autorização
inválida sem chamadas de criação.

## Autorrevisão

- A autorização é verificada antes de qualquer criação.
- O manifesto não concede autorização; ele só registra o progresso do plano autorizado.
- O arquivo temporário fica no mesmo diretório e é sincronizado antes da substituição.
- Uma falha permanente interrompe a sequência e preserva os registros já gravados.
- Não foram implementados rollback, exclusão, atualização automática ou exposição de segredos.
- Mudanças ficaram restritas aos arquivos da Tarefa 6 e a este relatório.
