"""Expõe a validação estrutural empacotada do backlog."""

from __future__ import annotations

from pathlib import Path

from publicar_backlog_azure_boards.contrato_backlog import validate_backlog


class ErroValidacaoEstrutural(ValueError):
    """Indica que o contrato compartilhado rejeitou o backlog."""


def validar_estrutura_backlog(caminho: Path) -> None:
    """Executa o contrato compartilhado e agrega todos os erros antes do planejamento."""
    texto = caminho.read_text(encoding="utf-8")
    erros = validate_backlog(texto, False)
    if erros:
        detalhes = "\n".join(f"- {erro}" for erro in erros)
        raise ErroValidacaoEstrutural(f"O backlog falhou na validação estrutural:\n{detalhes}")
