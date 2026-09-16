from __future__ import annotations

import importlib


def test_contrato_estrutural_faz_parte_do_pacote_instalado() -> None:
    modulo = importlib.import_module("publicar_backlog_azure_boards.contrato_backlog")

    assert callable(modulo.validate_backlog)
