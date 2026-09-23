"""Converte os campos copiáveis do backlog para o HTML aceito pelo Azure Boards."""

from markdown_it import MarkdownIt

_CONVERSOR = MarkdownIt("commonmark", {"html": False})


def converter_descricao(texto: str) -> str:
    """Converte uma descrição Markdown sem permitir HTML bruto de origem."""
    return str(_CONVERSOR.render(texto))


def converter_criterios(texto: str) -> str:
    """Converte critérios Gherkin, preservando cercas de código como blocos ``pre``."""
    return str(_CONVERSOR.render(texto))
