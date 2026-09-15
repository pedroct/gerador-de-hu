"""Monta operações de publicação sem executar chamadas remotas."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence

from publicar_backlog_azure_boards.converter_para_html import (
    converter_criterios,
    converter_descricao,
)
from publicar_backlog_azure_boards.modelos import (
    ConfiguracaoPublicacao,
    ItemBacklog,
    OperacaoCriacao,
    PlanoPublicacao,
    RegistroManifesto,
    TipoItem,
)

_ORDEM_TIPOS = {
    TipoItem.EPIC: 0,
    TipoItem.FEATURE: 1,
    TipoItem.HISTORIA_USUARIO: 2,
    TipoItem.BUG: 2,
}


def criar_plano(
    itens: Sequence[ItemBacklog],
    configuracao: ConfiguracaoPublicacao,
    registros: Mapping[str, RegistroManifesto],
) -> PlanoPublicacao:
    """Cria operações ordenadas para itens ainda ausentes do manifesto."""
    itens_ordenados = sorted(itens, key=_chave_ordenacao)
    operacoes = tuple(
        _criar_operacao(item) for item in itens_ordenados if item.chave not in registros
    )
    return PlanoPublicacao(
        operacoes=operacoes,
        hash_plano=_calcular_hash(itens_ordenados, configuracao),
    )


def _chave_ordenacao(item: ItemBacklog) -> tuple[int, tuple[int, int, int]]:
    primeiro, segundo, terceiro = (int(parte) for parte in item.chave.split("."))
    return (_ORDEM_TIPOS[item.tipo], (primeiro, segundo, terceiro))


def _criar_operacao(item: ItemBacklog) -> OperacaoCriacao:
    return OperacaoCriacao(
        chave=item.chave,
        tipo=item.tipo,
        titulo=item.titulo,
        descricao=converter_descricao(item.descricao),
        criterios_aceitacao=converter_criterios(item.criterios_aceitacao),
        chave_pai=item.pai,
    )


def _calcular_hash(
    itens: Sequence[ItemBacklog], configuracao: ConfiguracaoPublicacao
) -> str:
    conteudo = {
        "configuracao": {
            "organizacao": configuracao.organizacao,
            "projeto": configuracao.projeto,
            "area_path": configuracao.area_path,
            "iteration_path": configuracao.iteration_path,
        },
        "itens": [
            {
                "chave": item.chave,
                "tipo": item.tipo,
                "titulo": item.titulo,
                "pai": item.pai,
                "descricao": item.descricao,
                "criterios_aceitacao": item.criterios_aceitacao,
            }
            for item in itens
        ],
    }
    serializado = json.dumps(conteudo, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serializado.encode()).hexdigest()
