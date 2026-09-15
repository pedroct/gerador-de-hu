# Publicador de backlog no Azure Boards

Executor Python isolável para validar e publicar um backlog Markdown no Azure Boards.

## Desenvolvimento

Este projeto usa Python 3.12 ou superior e `uv`:

```bash
uv lock
uv run pytest -v
uv run ruff check .
uv run mypy
```

As configurações locais devem ser copiadas de `.env.example`. Segredos não devem ser versionados.
