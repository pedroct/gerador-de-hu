"""Lê a Demanda de Negócio que ancora a publicação, sem qualquer escrita.

Este módulo não usa ``ClienteAzureDevOps`` de propósito: o cliente é construído com uma
``ConfiguracaoPublicacao`` já completa, e os caminhos dessa configuração são justamente o
que a Demanda fornece. A leitura precisa acontecer antes de o destino existir.
"""

from __future__ import annotations

import base64
from typing import Any

import httpx

from publicar_backlog_demanda_azure_boards.cliente_azure_devops import (
    ErroDestinoInvalido,
    _verificar_status,
)
from publicar_backlog_demanda_azure_boards.modelos import Demanda

_VERSAO_API = "7.2-preview.3"
_CAMPOS_TEXTO = ("System.Title", "System.AreaPath", "System.IterationPath")


def ler_demanda(
    organizacao: str,
    projeto: str,
    token: str,
    id_demanda: int,
    tipo_esperado: str,
    *,
    transport: httpx.BaseTransport | None = None,
    timeout: float = 10.0,
) -> Demanda:
    """Busca a Demanda por `GET` e valida tipo, projeto e campos antes de derivar o destino."""
    if id_demanda <= 0:
        raise ErroDestinoInvalido("O ID da Demanda de Negócio deve ser um inteiro positivo.")
    credencial = base64.b64encode(f":{token}".encode()).decode()
    url = (
        f"https://dev.azure.com/{organizacao}/{projeto}"
        f"/_apis/wit/workitems/{id_demanda}?$expand=Fields&api-version={_VERSAO_API}"
    )
    with httpx.Client(
        headers={"Authorization": f"Basic {credencial}"},
        timeout=httpx.Timeout(timeout),
        transport=transport,
    ) as cliente:
        resposta = cliente.get(url)
    try:
        _verificar_status(resposta)
    except Exception as erro:
        raise ErroDestinoInvalido(
            f"Não foi possível ler a Demanda de Negócio {id_demanda}."
        ) from erro

    payload = _objeto(resposta.json(), f"A resposta da Demanda {id_demanda} é inválida.")
    campos = _objeto(payload.get("fields"), f"A Demanda {id_demanda} não devolveu seus campos.")

    tipo = campos.get("System.WorkItemType")
    if tipo != tipo_esperado:
        raise ErroDestinoInvalido(
            f"O work item {id_demanda} é do tipo {tipo!r}; "
            f"esta skill publica apenas sob {tipo_esperado!r}."
        )

    team_project = campos.get("System.TeamProject")
    if team_project != projeto:
        raise ErroDestinoInvalido(
            f"A Demanda {id_demanda} pertence ao projeto {team_project!r}, "
            f"e não a {projeto!r}; o vínculo hierárquico não cruza projeto."
        )

    for campo in _CAMPOS_TEXTO:
        valor = campos.get(campo)
        if not isinstance(valor, str) or not valor.strip():
            raise ErroDestinoInvalido(
                f"A Demanda {id_demanda} não possui {campo}; não há de onde herdar o destino."
            )

    url_item = payload.get("url")
    if not isinstance(url_item, str) or not url_item.startswith("https://"):
        raise ErroDestinoInvalido(f"A Demanda {id_demanda} não devolveu uma URL utilizável.")

    return Demanda(
        id=id_demanda,
        titulo=str(campos["System.Title"]).strip(),
        area_path=str(campos["System.AreaPath"]).strip(),
        iteration_path=str(campos["System.IterationPath"]).strip(),
        url=url_item,
    )


def _objeto(valor: object, mensagem: str) -> dict[str, Any]:
    if not isinstance(valor, dict):
        raise ErroDestinoInvalido(mensagem)
    return valor
