"""Base do publicador de backlog no Azure Boards."""

import sys


def main() -> None:
    """Encerra o ponto de entrada até que o executor seja implementado."""
    print(
        "O executor do publicador ainda não foi implementado; "
        "tente novamente após a conclusão das próximas tarefas.",
        file=sys.stderr,
    )
    raise SystemExit(1)
