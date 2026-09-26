"""Interpreta o contrato Markdown de backlog sem executar operações remotas."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from publicar_backlog_azure_boards.contrato_backlog import (
    AZURE_BOARDS_ID,
    DEPENDE_DE,
    IMPLEMENTATION_EVIDENCE,
    SECTION_NAMES,
    TAGS,
    normalizar_chaves,
    normalizar_id,
    normalizar_tags,
)
from publicar_backlog_azure_boards.modelos import ItemBacklog, TipoItem

_HEADING_RE = re.compile(r"^(?P<marcas>#{1,6}) (?P<conteudo>.+)$")
_ITEM_RE = re.compile(
    r"^(?P<marcas>#{1,6}) (?P<chave>[1-9]\d*\.\d+\.\d+) "
    r"\[(?P<tipo>Epic|Feature|User Story|Bug)\] (?P<titulo>\S.*)$"
)
_DATA_GERACAO_RE = re.compile(r"^- Data de geração: `(\d{4}-\d{2}-\d{2})`$", re.MULTILINE)
# Os dois parsers do contrato precisam reconhecer exatamente as mesmas seções: uma seção
# conhecida só aqui explode como "heading fora do contrato" no outro caminho, e uma seção
# conhecida só lá é anexada em silêncio ao conteúdo da seção anterior. Em vez de repetir a
# lista, este módulo reusa a de ``contrato_backlog`` — não há dois conjuntos para divergir.
_SECOES = SECTION_NAMES
_FOLHAS = {TipoItem.HISTORIA_USUARIO, TipoItem.BUG}


class ErroContratoMarkdown(ValueError):
    """Indica que o backlog não respeita o contrato de publicação."""


@dataclass
class _ItemEmConstrucao:
    chave: str
    tipo: TipoItem
    titulo: str
    nivel: int
    secoes: dict[str, list[str]] = field(default_factory=dict)

    def texto_secao(self, nome: str) -> str:
        return "\n".join(self.secoes.get(nome, [])).strip()


def interpretar_backlog(caminho: Path) -> list[ItemBacklog]:
    """Lê ``caminho`` e devolve itens tipados, recusando qualquer contrato inválido."""
    texto = caminho.read_text(encoding="utf-8")
    itens_em_construcao = _extrair_itens(texto)
    _validar_itens(itens_em_construcao)
    return [_converter_item(item) for item in itens_em_construcao]


def extrair_data_geracao(caminho: Path) -> str:
    """Lê a data fixa de geração dos Metadados; nunca deriva do relógio."""
    texto = caminho.read_text(encoding="utf-8")
    correspondencia = _DATA_GERACAO_RE.search(texto)
    if correspondencia is None:
        raise ErroContratoMarkdown(
            "Metadados e cobertura não possui Data de geração no formato `AAAA-MM-DD`"
        )
    data = correspondencia.group(1)
    try:
        date.fromisoformat(data)
    except ValueError as erro:
        raise ErroContratoMarkdown(f"Data de geração inválida: {data}") from erro
    return data


def _extrair_itens(texto: str) -> list[_ItemEmConstrucao]:
    itens: list[_ItemEmConstrucao] = []
    atual: _ItemEmConstrucao | None = None
    secao_atual: str | None = None
    em_cerca = False

    for linha in texto.splitlines():
        if linha.lstrip().startswith("```"):
            em_cerca = not em_cerca
            if atual is not None and secao_atual is not None:
                atual.secoes.setdefault(secao_atual, []).append(linha)
            continue

        if em_cerca:
            if atual is not None and secao_atual is not None:
                atual.secoes.setdefault(secao_atual, []).append(linha)
            continue

        item = _ITEM_RE.match(linha)
        if item is not None:
            atual = _ItemEmConstrucao(
                chave=item.group("chave"),
                tipo=TipoItem(item.group("tipo")),
                titulo=item.group("titulo"),
                nivel=len(item.group("marcas")),
            )
            itens.append(atual)
            secao_atual = None
            continue

        heading = _HEADING_RE.match(linha)
        if heading is not None:
            if atual is None:
                _validar_heading_inicial(linha)
            else:
                secao_atual = _tratar_heading(atual, secao_atual, heading, linha)
            continue

        if atual is not None and secao_atual is not None:
            atual.secoes.setdefault(secao_atual, []).append(linha)

    if em_cerca:
        raise ErroContratoMarkdown("cerca de código não encerrada")
    return itens


def _validar_heading_inicial(linha: str) -> None:
    if linha not in {"# Backlog para Azure Boards", "## Metadados e cobertura"}:
        raise ErroContratoMarkdown(f"heading fora do contrato: {linha}")


def _tratar_heading(
    item: _ItemEmConstrucao,
    secao_atual: str | None,
    heading: re.Match[str],
    linha: str,
) -> str | None:
    nivel = len(heading.group("marcas"))
    conteudo = heading.group("conteudo")
    if nivel == item.nivel + 1:
        nome_secao = _nome_secao(conteudo)
        if nome_secao is None:
            raise ErroContratoMarkdown(f"heading fora do contrato: {linha}")
        item.secoes.setdefault(nome_secao, [])
        return nome_secao
    if (
        nivel == item.nivel + 2
        and secao_atual == "Description"
        and item.tipo in _FOLHAS
        and conteudo in {"Card", "Conversation"}
    ):
        item.secoes["Description"].append(f"### {conteudo}")
        return secao_atual
    raise ErroContratoMarkdown(f"heading fora do contrato: {linha}")


def _nome_secao(conteudo: str) -> str | None:
    if conteudo in _SECOES:
        return conteudo
    if conteudo.startswith(f"{IMPLEMENTATION_EVIDENCE} "):
        return IMPLEMENTATION_EVIDENCE
    return None


def _validar_itens(itens: list[_ItemEmConstrucao]) -> None:
    if not itens:
        raise ErroContratoMarkdown("o backlog não possui itens")

    por_chave = {item.chave: item for item in itens}
    if len(por_chave) != len(itens):
        raise ErroContratoMarkdown("o backlog possui chaves duplicadas")

    for item in itens:
        _validar_item(item, por_chave)


def _validar_item(item: _ItemEmConstrucao, por_chave: dict[str, _ItemEmConstrucao]) -> None:
    _validar_chave_e_nivel(item)
    if not item.texto_secao("Description"):
        raise ErroContratoMarkdown(f"{item.chave} não possui Description")

    if item.tipo is TipoItem.EPIC:
        return

    pai = _valor_pai(item)
    if pai is None:
        raise ErroContratoMarkdown(f"{item.chave} não possui Parent")
    pai_item = por_chave.get(pai)
    if pai_item is None:
        raise ErroContratoMarkdown(f"{item.chave} referencia pai inexistente: {pai}")
    if pai != _chave_pai_esperada(item):
        raise ErroContratoMarkdown(f"{item.chave} possui pai incompatível: {pai}")
    tipo_pai = TipoItem.EPIC if item.tipo is TipoItem.FEATURE else TipoItem.FEATURE
    if pai_item.tipo is not tipo_pai:
        raise ErroContratoMarkdown(f"{item.chave} possui pai de tipo inválido: {pai}")
    if item.tipo in _FOLHAS and "Acceptance Criteria" not in item.secoes:
        raise ErroContratoMarkdown(f"{item.chave} não possui Acceptance Criteria")
    if item.tipo in _FOLHAS:
        _validar_criterios_aceitacao(item)


def _validar_chave_e_nivel(item: _ItemEmConstrucao) -> None:
    primeiro, segundo, terceiro = (int(parte) for parte in item.chave.split("."))
    valido = {
        TipoItem.EPIC: item.nivel == 2 and segundo == 0 and terceiro == 0,
        TipoItem.FEATURE: item.nivel == 3 and segundo > 0 and terceiro == 0,
        TipoItem.HISTORIA_USUARIO: item.nivel == 4 and segundo > 0 and terceiro > 0,
        TipoItem.BUG: item.nivel == 4 and segundo > 0 and terceiro > 0,
    }[item.tipo]
    if not valido or primeiro <= 0:
        raise ErroContratoMarkdown(
            f"{item.chave} possui chave ou nível incompatível com {item.tipo}"
        )


def _valor_pai(item: _ItemEmConstrucao) -> str | None:
    valor = item.texto_secao("Parent").strip("`").strip()
    return valor or None


def _chave_pai_esperada(item: _ItemEmConstrucao) -> str:
    epic, feature, _ = item.chave.split(".")
    if item.tipo is TipoItem.FEATURE:
        return f"{epic}.0.0"
    return f"{epic}.{feature}.0"


def _validar_criterios_aceitacao(item: _ItemEmConstrucao) -> None:
    linhas = item.texto_secao("Acceptance Criteria").splitlines()
    em_bloco = False
    for linha in linhas:
        if not linha.strip():
            continue
        if linha.startswith("```gherkin") and not em_bloco:
            em_bloco = True
            continue
        if linha == "```" and em_bloco:
            em_bloco = False
            continue
        if not em_bloco:
            raise ErroContratoMarkdown(
                f"{item.chave} possui Acceptance Criteria fora de bloco gherkin"
            )
    if em_bloco:
        raise ErroContratoMarkdown(f"{item.chave} possui bloco gherkin não encerrado")


def _tags_do_item(item: _ItemEmConstrucao) -> tuple[str, ...]:
    if TAGS not in item.secoes:
        return ()
    tags, erros = normalizar_tags(item.texto_secao(TAGS))
    if erros:
        raise ErroContratoMarkdown(f"{item.chave}: {erros[0]}")
    if not tags:
        raise ErroContratoMarkdown(f"{item.chave} possui a seção {TAGS} presente e vazia")
    return tags


def _dependencias_do_item(item: _ItemEmConstrucao) -> tuple[str, ...]:
    if DEPENDE_DE not in item.secoes:
        return ()
    chaves, erros = normalizar_chaves(item.texto_secao(DEPENDE_DE))
    if erros:
        raise ErroContratoMarkdown(f"{item.chave}: {erros[0]}")
    if not chaves:
        raise ErroContratoMarkdown(f"{item.chave} possui a seção {DEPENDE_DE} presente e vazia")
    return chaves


def _id_existente(item: _ItemEmConstrucao) -> int | None:
    if AZURE_BOARDS_ID not in item.secoes:
        return None
    valor, erros = normalizar_id(item.texto_secao(AZURE_BOARDS_ID))
    if erros:
        raise ErroContratoMarkdown(f"{item.chave}: {erros[0]}")
    if valor is None:
        raise ErroContratoMarkdown(
            f"{item.chave} possui a seção {AZURE_BOARDS_ID} presente e vazia"
        )
    return valor


def _converter_item(item: _ItemEmConstrucao) -> ItemBacklog:
    return ItemBacklog(
        chave=item.chave,
        tipo=item.tipo,
        titulo=item.titulo,
        pai=None if item.tipo is TipoItem.EPIC else _valor_pai(item),
        descricao=item.texto_secao("Description"),
        criterios_aceitacao=item.texto_secao("Acceptance Criteria"),
        titulo_curto=item.texto_secao("Título curto"),
        tags=_tags_do_item(item),
        depende_de=_dependencias_do_item(item),
        azure_boards_id=_id_existente(item),
    )
