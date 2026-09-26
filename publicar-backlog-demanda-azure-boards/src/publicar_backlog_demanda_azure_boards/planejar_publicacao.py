"""Monta operações de publicação sem executar chamadas remotas."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence

from publicar_backlog_demanda_azure_boards.converter_para_html import (
    converter_criterios,
    converter_descricao,
)
from publicar_backlog_demanda_azure_boards.modelos import (
    ConfiguracaoPublicacao,
    ItemBacklog,
    OperacaoCriacao,
    PlanoPublicacao,
    TipoItem,
)
from publicar_backlog_demanda_azure_boards.titulo_hierarquico import montar_titulo

_ORDEM_TIPOS = {
    TipoItem.EPIC: 0,
    TipoItem.FEATURE: 1,
    TipoItem.HISTORIA_USUARIO: 2,
    TipoItem.BUG: 2,
}


class ErroDependenciaCiclica(ValueError):
    """Indica ciclo de dependência que impediria qualquer ordem de criação."""


def criar_plano(
    itens: Sequence[ItemBacklog],
    configuracao: ConfiguracaoPublicacao,
    data_geracao: str,
) -> PlanoPublicacao:
    """Cria o plano completo; a retomada só separa pendentes após validar o manifesto."""
    itens_ordenados = _ordenar_para_criacao(itens)
    operacoes = tuple(_criar_operacao(item, configuracao) for item in itens_ordenados)
    return PlanoPublicacao(
        operacoes=operacoes,
        hash_plano=_calcular_hash(itens_ordenados, configuracao, data_geracao),
        configuracao=configuracao,
    )


def _chave_ordenacao(item: ItemBacklog) -> tuple[int, tuple[int, int, int]]:
    primeiro, segundo, terceiro = (int(parte) for parte in item.chave.split("."))
    return (_ORDEM_TIPOS[item.tipo], (primeiro, segundo, terceiro))


def _ordenar_para_criacao(itens: Sequence[ItemBacklog]) -> list[ItemBacklog]:
    """Ordena por tipo e chave e depois puxa cada predecessor para antes do dependente.

    A travessia parte da ordem estável de hoje e emite em pós-ordem, então um backlog
    sem ``depende_de`` sai exatamente na sequência anterior — é o que preserva o hash
    e, com ele, a retomada de todo manifesto já gravado.

    Não trate ``item.pai`` como aresta implícita aqui: o contrato só permite ``Depende
    de`` partindo de item de folha, e toda folha já vem por último na ordem base, então
    todo contêiner ancestral já foi emitido antes de qualquer aresta de dependência ser
    seguida — acrescentar essa aresta resolveria um caso que a validação já proíbe.
    """
    base = sorted(itens, key=_chave_ordenacao)
    por_chave = {item.chave: item for item in base}
    resultado: list[ItemBacklog] = []
    concluidos: set[str] = set()
    em_visita: list[str] = []

    def visitar(item: ItemBacklog) -> None:
        if item.chave in concluidos:
            return
        if item.chave in em_visita:
            ciclo = " → ".join(em_visita[em_visita.index(item.chave) :] + [item.chave])
            raise ErroDependenciaCiclica(f"ciclo de dependência entre {ciclo}")
        em_visita.append(item.chave)
        for chave in item.depende_de:
            predecessor = por_chave.get(chave)
            if predecessor is not None:
                visitar(predecessor)
        em_visita.pop()
        concluidos.add(item.chave)
        resultado.append(item)

    for item in base:
        visitar(item)
    return resultado


def _criar_operacao(item: ItemBacklog, configuracao: ConfiguracaoPublicacao) -> OperacaoCriacao:
    return OperacaoCriacao(
        chave=item.chave,
        tipo=item.tipo,
        titulo=montar_titulo(item),
        descricao=converter_descricao(item.descricao),
        criterios_aceitacao=converter_criterios(item.criterios_aceitacao),
        chave_pai=item.pai,
        tipo_remoto=configuracao.mapeamento_tipos.nome_remoto(item.tipo),
        tags=item.tags,
        depende_de=item.depende_de,
    )


def _conteudo_do_item(item: ItemBacklog) -> dict[str, object]:
    conteudo: dict[str, object] = {
        "chave": item.chave,
        "tipo": item.tipo,
        "titulo": item.titulo,
        "titulo_curto": item.titulo_curto,
        "pai": item.pai,
        "descricao": item.descricao,
        "criterios_aceitacao": item.criterios_aceitacao,
    }
    # A chave só entra quando preenchida: um backlog sem campos novos precisa produzir
    # o hash anterior, ou todo manifesto de publicação parcial deixa de retomar. Não
    # "simplifique" incluindo sempre.
    if item.tags:
        conteudo["tags"] = list(item.tags)
    if item.depende_de:
        conteudo["depende_de"] = list(item.depende_de)
    return conteudo


def _calcular_hash(
    itens: Sequence[ItemBacklog], configuracao: ConfiguracaoPublicacao, data_geracao: str
) -> str:
    conteudo = {
        "configuracao": {
            "organizacao": configuracao.organizacao,
            "projeto": configuracao.projeto,
            "area_path": configuracao.area_path,
            "iteration_path": configuracao.iteration_path,
            "demanda_id": configuracao.demanda_id,
            "mapeamento_tipos": configuracao.mapeamento_tipos.como_dict(),
        },
        "data_geracao": data_geracao,
        "itens": [_conteudo_do_item(item) for item in itens],
    }
    serializado = json.dumps(conteudo, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serializado.encode()).hexdigest()
