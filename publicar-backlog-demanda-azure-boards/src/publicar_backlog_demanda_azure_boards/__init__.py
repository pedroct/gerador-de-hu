"""Publicador de backlog no Azure Boards."""


def main() -> int:
    """Executa a mesma CLI usada pelo script de desenvolvimento."""
    from publicar_backlog_demanda_azure_boards.cli import principal

    return principal()
