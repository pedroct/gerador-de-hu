"""Leitor somente leitura de uma Demanda de Negócio no Azure Boards."""

from __future__ import annotations

import base64
import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from json import JSONDecodeError
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

TIPO_DEMANDA = "Demanda de Negócio"
CAMPOS_DEMANDA = (
    "System.Title",
    "Custom.DemandaAreaSolicitante",
    "Custom.DemandaPublicoAlvo",
    "Custom.DemandaValorEsperado",
    "Custom.DemandaDoraResolver",
    "Custom.DemandaRegraseRestricoes",
)


class ErroConsultaDemanda(RuntimeError):
    """Indica que uma Demanda não pôde ser lida ou não atende ao contrato."""


@dataclass(frozen=True)
class ConfiguracaoAzureBoards:
    """Destino e credencial necessários para uma consulta somente leitura."""

    organizacao: str
    projeto: str
    token: str


@dataclass(frozen=True)
class DemandaNegocio:
    id: int
    url: str
    tipo: str
    titulo: str
    valores: dict[str, str | None]


Requisitar = Callable[[str, dict[str, str]], dict[str, object]]


def requisitar_json(
    url: str,
    cabecalhos: dict[str, str],
    *,
    abrir: Callable[..., Any] = urlopen,
) -> dict[str, object]:
    """Faz uma requisição GET e decodifica seu corpo JSON como objeto."""
    requisicao = Request(url, headers=cabecalhos, method="GET")  # noqa: S310
    with abrir(requisicao) as resposta:  # noqa: S310 - a URL é construída pelo leitor HTTPS.
        corpo = resposta.read()
    payload = json.loads(corpo)
    if not isinstance(payload, dict):
        raise ValueError("a resposta JSON não é um objeto")
    return payload


def consultar_demanda(
    id_demanda: int,
    configuracao: ConfiguracaoAzureBoards,
    requisitar: Requisitar | None = None,
) -> DemandaNegocio:
    """Lê e valida uma Demanda de Negócio sem modificar o Azure Boards."""
    if isinstance(id_demanda, bool) or not isinstance(id_demanda, int) or id_demanda <= 0:
        raise ErroConsultaDemanda(f"ID da Demanda inválido: {id_demanda}.")

    organizacao = quote(configuracao.organizacao, safe="")
    projeto = quote(configuracao.projeto, safe="")
    tipo = quote(TIPO_DEMANDA, safe="")
    base_url = f"https://dev.azure.com/{organizacao}/{projeto}"
    url_item = f"{base_url}/_apis/wit/workitems/{id_demanda}?$expand=Fields&api-version=7.1"
    url_campos = f"{base_url}/_apis/wit/workitemtypes/{tipo}/fields?api-version=7.1"
    cabecalhos = {
        "Authorization": "Basic "
        + base64.b64encode(f":{configuracao.token}".encode()).decode(),
        "Accept": "application/json",
    }
    obter = requisitar or _requisitar_json_seguro

    payload_item = _obter_payload(obter, url_item, cabecalhos, id_demanda)
    campos_item = _objeto(payload_item.get("fields"), f"ID {id_demanda}: fields inválido")
    _validar_identidade_item(payload_item, id_demanda, campos_item)

    payload_campos = _obter_payload(obter, url_campos, cabecalhos, id_demanda)
    campos_disponiveis = _extrair_campos(payload_campos, id_demanda)
    ausentes = [campo for campo in CAMPOS_DEMANDA if campo not in campos_disponiveis]
    if ausentes:
        raise ErroConsultaDemanda(
            f"ID {id_demanda}: o tipo {TIPO_DEMANDA!r} não define o campo {ausentes[0]}."
        )

    titulo = _texto_obrigatorio(campos_item, "System.Title", id_demanda)
    valores = {
        campo: _texto_opcional(campos_item, campo, id_demanda)
        for campo in CAMPOS_DEMANDA
        if campo != "System.Title"
    }
    return DemandaNegocio(
        id=id_demanda,
        url=_url_item(payload_item, id_demanda),
        tipo=TIPO_DEMANDA,
        titulo=titulo,
        valores=valores,
    )


def _requisitar_json_seguro(url: str, cabecalhos: dict[str, str]) -> dict[str, object]:
    try:
        return requisitar_json(url, cabecalhos)
    except HTTPError:
        raise
    except (JSONDecodeError, UnicodeDecodeError, URLError, OSError, ValueError) as erro:
        raise ErroConsultaDemanda(f"Falha ao interpretar a resposta da consulta: {erro}.") from None


def _obter_payload(
    requisitar: Requisitar,
    url: str,
    cabecalhos: dict[str, str],
    id_demanda: int,
) -> dict[str, object]:
    try:
        payload = requisitar(url, cabecalhos)
    except HTTPError as erro:
        raise ErroConsultaDemanda(
            f"Falha HTTP {erro.code} ao consultar a Demanda {id_demanda}."
        ) from None
    except (JSONDecodeError, UnicodeDecodeError, URLError, OSError, ValueError) as erro:
        raise ErroConsultaDemanda(
            f"Falha ao consultar a Demanda {id_demanda}: {erro}."
        ) from None
    if not isinstance(payload, dict):
        raise ErroConsultaDemanda(f"ID {id_demanda}: a resposta não é um objeto JSON.")
    return payload


def _validar_identidade_item(
    payload: Mapping[str, object], id_demanda: int, campos: Mapping[str, object]
) -> None:
    id_remoto = payload.get("id")
    if isinstance(id_remoto, bool) or not isinstance(id_remoto, int) or id_remoto <= 0:
        raise ErroConsultaDemanda(f"ID {id_demanda}: a resposta tem ID remoto inválido.")
    if id_remoto != id_demanda:
        raise ErroConsultaDemanda(f"ID {id_demanda}: o ID remoto é {id_remoto}, não o solicitado.")
    url = payload.get("url")
    if not isinstance(url, str) or not url.strip() or not url.startswith("https://"):
        raise ErroConsultaDemanda(f"ID {id_demanda}: URL remota ausente ou não HTTPS.")
    tipo = campos.get("System.WorkItemType")
    if tipo != TIPO_DEMANDA:
        raise ErroConsultaDemanda(f"ID {id_demanda}: tipo de work item inesperado.")


def _url_item(payload: Mapping[str, object], id_demanda: int) -> str:
    url = payload["url"]
    if not isinstance(url, str):
        raise ErroConsultaDemanda(f"ID {id_demanda}: URL remota inválida.")
    return url


def _objeto(valor: object, mensagem: str) -> Mapping[str, object]:
    if not isinstance(valor, dict):
        raise ErroConsultaDemanda(mensagem)
    return valor


def _extrair_campos(payload: Mapping[str, object], id_demanda: int) -> set[str]:
    valor = payload.get("value")
    if not isinstance(valor, list) or not valor:
        raise ErroConsultaDemanda(f"ID {id_demanda}: resposta de campos inválida.")
    nomes: set[str] = set()
    for item in valor:
        if not isinstance(item, dict) or not isinstance(item.get("referenceName"), str):
            raise ErroConsultaDemanda(f"ID {id_demanda}: resposta de campos inválida.")
        nomes.add(item["referenceName"])
    return nomes


def _texto_obrigatorio(campos: Mapping[str, object], nome: str, id_demanda: int) -> str:
    valor = campos.get(nome)
    if not isinstance(valor, str) or not valor.strip():
        raise ErroConsultaDemanda(f"ID {id_demanda}: campo {nome} vazio ou não textual.")
    return valor


def _texto_opcional(campos: Mapping[str, object], nome: str, id_demanda: int) -> str | None:
    valor = campos.get(nome)
    if valor is None:
        return None
    if not isinstance(valor, str):
        raise ErroConsultaDemanda(f"ID {id_demanda}: campo {nome} não é textual.")
    return valor if valor.strip() else None
