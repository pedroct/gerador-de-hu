"""Lê a Demanda de Negócio que ancora a publicação, sem qualquer escrita.

Este módulo não usa ``ClienteAzureDevOps`` de propósito: o cliente é construído com uma
``ConfiguracaoPublicacao`` já completa, e os caminhos dessa configuração são justamente o
que a Demanda fornece. A leitura precisa acontecer antes de o destino existir.
"""

from __future__ import annotations

import base64
import time
from typing import Any

import httpx

from publicar_backlog_demanda_azure_boards.cliente_azure_devops import (
    ErroDestinoInvalido,
    ErroFalhaTransitoria,
    ErroRespostaInvalida,
    _verificar_status,
)
from publicar_backlog_demanda_azure_boards.modelos import Demanda

_VERSAO_API = "7.2-preview.3"
_CAMPOS_TEXTO = ("System.Title", "System.AreaPath", "System.IterationPath")
# Mesmos códigos que `ClienteAzureDevOps` retenta: a leitura da Demanda não tem por que
# ser menos resiliente que as demais leituras do pacote.
_ERROS_RETENTAVEIS = frozenset({408, 429, 500, 502, 503, 504})
_MAX_TENTATIVAS = 3


def ler_demanda(
    organizacao: str,
    projeto: str,
    token: str,
    id_demanda: int,
    tipo_esperado: str,
    *,
    transport: httpx.BaseTransport | None = None,
    timeout: float = 10.0,
    espera_inicial: float = 0.2,
) -> Demanda:
    """Busca a Demanda por `GET` e valida tipo, projeto e campos antes de derivar o destino."""
    if id_demanda <= 0:
        raise ErroDestinoInvalido("O ID da Demanda de Negócio deve ser um inteiro positivo.")
    credencial = base64.b64encode(f":{token}".encode()).decode()
    url = (
        f"https://dev.azure.com/{organizacao}/{projeto}"
        f"/_apis/wit/workitems/{id_demanda}?$expand=Fields&api-version={_VERSAO_API}"
    )
    resposta = _buscar(url, credencial, transport, timeout, espera_inicial, id_demanda)
    try:
        _verificar_status(resposta)
    except ErroDestinoInvalido as erro:
        # Só o 404 chega aqui como destino inválido; os demais códigos preservam sua
        # classe, para que 401 e 403 não sejam confundidos com ID errado.
        raise ErroDestinoInvalido(
            f"Não foi possível ler a Demanda de Negócio {id_demanda}; confira o ID e o projeto."
        ) from erro

    try:
        corpo = resposta.json()
    except ValueError as erro:
        raise ErroRespostaInvalida(
            f"A resposta da Demanda {id_demanda} não é JSON consumível."
        ) from erro
    payload = _objeto(corpo, f"A resposta da Demanda {id_demanda} é inválida.")
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


def _buscar(
    url: str,
    credencial: str,
    transport: httpx.BaseTransport | None,
    timeout: float,
    espera_inicial: float,
    id_demanda: int,
) -> httpx.Response:
    """Executa o GET com as mesmas tentativas e o mesmo backoff do cliente REST."""
    with httpx.Client(
        headers={"Authorization": f"Basic {credencial}"},
        timeout=httpx.Timeout(timeout),
        transport=transport,
    ) as cliente:
        for tentativa in range(_MAX_TENTATIVAS):
            try:
                resposta = cliente.get(url)
            except httpx.RequestError as erro:
                # RequestError não herda de OSError nem de RuntimeError; sem esta
                # conversão, o erro atravessa a CLI como traceback cru.
                if tentativa == _MAX_TENTATIVAS - 1:
                    raise ErroFalhaTransitoria(
                        f"A leitura da Demanda {id_demanda} falhou por erro de rede."
                    ) from erro
            else:
                if resposta.status_code not in _ERROS_RETENTAVEIS:
                    return resposta
                if tentativa == _MAX_TENTATIVAS - 1:
                    raise ErroFalhaTransitoria(
                        f"A leitura da Demanda {id_demanda} não se completou "
                        f"(HTTP {resposta.status_code}) após {_MAX_TENTATIVAS} tentativas."
                    )
            time.sleep(espera_inicial * (2**tentativa))
    raise ErroFalhaTransitoria(f"A leitura da Demanda {id_demanda} não se completou.")


def _objeto(valor: object, mensagem: str) -> dict[str, Any]:
    if not isinstance(valor, dict):
        raise ErroDestinoInvalido(mensagem)
    return valor
