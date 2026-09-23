"""Compatibilidade para executar a CLI diretamente a partir do repositório."""

from __future__ import annotations

import sys
from pathlib import Path

if __package__ in {None, ""}:
    origem = str(Path(__file__).resolve().parents[1] / "src")
    if origem not in sys.path:
        sys.path.insert(0, origem)

from publicar_backlog_demanda_azure_boards import main  # noqa: E402
from publicar_backlog_demanda_azure_boards.cli import principal  # noqa: E402, F401

if __name__ == "__main__":
    raise SystemExit(main())
