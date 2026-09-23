"""Converte a chave documental do backlog na numeração usada no título do work item."""

from __future__ import annotations

from publicar_backlog_demanda_azure_boards.modelos import ItemBacklog

_LARGURA_MINIMA = 2


def numerar(chave: str) -> str:
    """Converte `E.F.S` na numeração hierárquica, descartando os níveis não usados.

    O contrato do backlog garante que um Épico seja `E.0.0` e uma Feature, `E.F.0`. Os
    componentes finais iguais a zero são, portanto, marcadores de nível ausente e não
    pertencem ao título: `1.0.0` vira `01` e `1.1.0` vira `01.01`.
    """
    componentes = chave.split(".")
    if len(componentes) != 3:
        raise ValueError(f"A chave {chave!r} não está no formato E.F.S.")
    try:
        numeros = [int(componente) for componente in componentes]
    except ValueError as erro:
        raise ValueError(f"A chave {chave!r} possui componente não numérico.") from erro
    if any(numero < 0 for numero in numeros):
        raise ValueError(f"A chave {chave!r} possui componente negativo.")
    while len(numeros) > 1 and numeros[-1] == 0:
        numeros.pop()
    return ".".join(str(numero).zfill(_LARGURA_MINIMA) for numero in numeros)


def montar_titulo(item: ItemBacklog) -> str:
    """Compõe o título publicado: numeração hierárquica seguida do texto do item."""
    return f"{numerar(item.chave)} {item.titulo_curto or item.titulo}"
