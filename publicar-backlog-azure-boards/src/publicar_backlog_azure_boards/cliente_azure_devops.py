"""Cliente REST mínimo e seguro para verificação e publicação no Azure DevOps."""

from __future__ import annotations

import base64
import time
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote, urlencode, urlparse

import httpx

from publicar_backlog_azure_boards.modelos import (
    ConfiguracaoPublicacao,
    OperacaoCriacao,
    TipoItem,
)

_TIPOS_OBRIGATORIOS = tuple(tipo.value for tipo in TipoItem)
_CAMPOS_OBRIGATORIOS = frozenset(
    {
        "System.Title",
        "System.Description",
        "Microsoft.VSTS.Common.AcceptanceCriteria",
        "System.AreaPath",
        "System.IterationPath",
    }
)
_RELACAO_HIERARQUICA = "System.LinkTypes.Hierarchy-Reverse"


class ErroAzureDevOps(RuntimeError):
    """Erro base para falhas comunicáveis do Azure DevOps."""


class ErroAutenticacao(ErroAzureDevOps):
    """A credencial não foi aceita pelo Azure DevOps."""


class ErroPermissao(ErroAzureDevOps):
    """A credencial não tem permissão para a operação."""


class ErroDestinoInvalido(ErroAzureDevOps):
    """Organização, projeto, tipo, campo ou caminho não existe."""


class ErroConflito(ErroAzureDevOps):
    """O Azure DevOps recusou a operação por conflito."""


class ErroFalhaTransitoria(ErroAzureDevOps):
    """Uma falha transitória persistiu após poucas tentativas."""


@dataclass(frozen=True)
class VerificacaoDestino:
    """Metadados confirmados antes de autorizar uma publicação."""

    tipos: tuple[str, ...]
    campos: tuple[str, ...]
    relacoes: tuple[str, ...]
    area_path: str
    iteration_path: str


@dataclass(frozen=True)
class RegistroCriado:
    """Identidade retornada pelo Azure DevOps após criar um work item."""

    id: int
    tipo: str
    url: str


class ClienteAzureDevOps:
    """Encapsula chamadas REST sem registrar ou expor a credencial."""

    VERSOES_API = {
        "criacao": "7.2-preview.3",
        "tipos": "7.2-preview.2",
        "campos": "7.2-preview.2",
        "relacoes": "7.2-preview.2",
        "classificacao": "7.2-preview.2",
    }
    _ERROS_RETENTAVEIS = frozenset({408, 429, 500, 502, 503, 504})

    def __init__(
        self,
        configuracao: ConfiguracaoPublicacao,
        token: str,
        *,
        transport: httpx.BaseTransport | None = None,
        timeout: float = 10.0,
        max_tentativas: int = 3,
        espera_inicial: float = 0.2,
    ) -> None:
        if max_tentativas < 1:
            raise ValueError("max_tentativas deve ser positivo")
        self.configuracao = configuracao
        self._base_url = (
            f"https://dev.azure.com/{quote(configuracao.organizacao, safe='')}/"
            f"{quote(configuracao.projeto, safe='')}"
        )
        credencial = base64.b64encode(f":{token}".encode()).decode()
        self._cliente = httpx.Client(
            base_url=self._base_url,
            headers={"Authorization": f"Basic {credencial}"},
            timeout=httpx.Timeout(timeout),
            transport=transport,
        )
        self._max_tentativas = max_tentativas
        self._espera_inicial = espera_inicial

    def verificar_destino(self, configuracao: ConfiguracaoPublicacao) -> VerificacaoDestino:
        """Consulta tipos, campos, relações e caminhos sem criar work items."""
        if configuracao != self.configuracao:
            raise ErroDestinoInvalido("A configuração consultada difere do cliente configurado.")

        tipos_payload = self._obter(self._url_api("/_apis/wit/workitemtypes", "tipos"))
        tipos = tuple(_nomes(tipos_payload, recurso="tipos de work item"))
        tipos_ausentes = set(_TIPOS_OBRIGATORIOS).difference(tipos)
        if tipos_ausentes:
            raise ErroDestinoInvalido(
                "O projeto não disponibiliza os tipos obrigatórios: "
                + ", ".join(sorted(tipos_ausentes))
                + "."
            )

        campos: set[str] = set()
        for tipo in _TIPOS_OBRIGATORIOS:
            payload = self._obter(
                self._url_api(f"/_apis/wit/workitemtypes/{quote(tipo, safe='')}/fields", "campos")
            )
            campos_do_tipo = set(
                _nomes(payload, campo="referenceName", recurso=f"campos de {tipo}")
            )
            campos_ausentes = _CAMPOS_OBRIGATORIOS.difference(campos_do_tipo)
            if campos_ausentes:
                raise ErroDestinoInvalido(
                    f"{tipo} não disponibiliza os campos obrigatórios: "
                    + ", ".join(sorted(campos_ausentes))
                    + "."
                )
            campos.update(campos_do_tipo)

        relacoes_payload = self._obter(
            self._url_api("/_apis/wit/workitemrelationtypes", "relacoes")
        )
        relacoes = tuple(
            _nomes(relacoes_payload, campo="referenceName", recurso="relações de work item")
        )
        if _RELACAO_HIERARQUICA not in relacoes:
            raise ErroDestinoInvalido(
                "A relação hierárquica de pai não está disponível no projeto."
            )
        self._validar_caminho("areas", configuracao.area_path)
        self._validar_caminho("iterations", configuracao.iteration_path)
        return VerificacaoDestino(
            tipos=tipos,
            campos=tuple(sorted(campos)),
            relacoes=relacoes,
            area_path=configuracao.area_path,
            iteration_path=configuracao.iteration_path,
        )

    def validar_operacao(self, operacao: OperacaoCriacao) -> None:
        """Valida o JSON Patch no endpoint de criação, sem persistir o item."""
        self._enviar_criacao(operacao, validar=True, id_pai=None)

    def criar_item(self, operacao: OperacaoCriacao, id_pai: int | None = None) -> RegistroCriado:
        """Cria um item e inclui a relação hierárquica apenas com pai identificado."""
        payload = self._enviar_criacao(operacao, validar=False, id_pai=id_pai)
        item_id = payload.get("id")
        url = payload.get("url")
        if isinstance(item_id, bool) or not isinstance(item_id, int) or item_id <= 0:
            raise ErroAzureDevOps("A resposta de criação não contém uma identidade válida.")
        if not isinstance(url, str) or not _url_azure_valida(url):
            raise ErroAzureDevOps("A resposta de criação não contém uma identidade válida.")
        return RegistroCriado(id=item_id, tipo=operacao.tipo.value, url=url)

    def _enviar_criacao(
        self, operacao: OperacaoCriacao, *, validar: bool, id_pai: int | None
    ) -> dict[str, Any]:
        patch: list[dict[str, object]] = [
            {"op": "add", "path": "/fields/System.Title", "value": operacao.titulo},
            {"op": "add", "path": "/fields/System.Description", "value": operacao.descricao},
            {
                "op": "add",
                "path": "/fields/Microsoft.VSTS.Common.AcceptanceCriteria",
                "value": operacao.criterios_aceitacao,
            },
            {"op": "add", "path": "/fields/System.AreaPath", "value": self.configuracao.area_path},
            {
                "op": "add",
                "path": "/fields/System.IterationPath",
                "value": self.configuracao.iteration_path,
            },
        ]
        if id_pai is not None:
            patch.append(
                {
                    "op": "add",
                    "path": "/relations/-",
                    "value": {
                        "rel": "System.LinkTypes.Hierarchy-Reverse",
                        "url": f"{self._base_url}/_apis/wit/workItems/{id_pai}",
                    },
                }
            )
        parametros = (("validateOnly", "true"),) if validar else ()
        url = self._url_api(
            f"/_apis/wit/workitems/{quote(operacao.tipo.value, safe='')}",
            "criacao",
            parametros=parametros,
        )
        return self._enviar("POST", url, json=patch, tipo_conteudo="application/json-patch+json")

    def _validar_caminho(self, grupo: str, caminho: str) -> None:
        payload = self._obter(
            self._url_api(
                f"/_apis/wit/classificationnodes/{grupo}/{quote(caminho, safe='')}",
                "classificacao",
            )
        )
        nome = payload.get("name")
        caminho_retornado = payload.get("path")
        caminho_esperado = "\\" + caminho.lstrip("\\")
        if (
            not isinstance(nome, str)
            or not nome
            or nome != caminho.rsplit("\\", maxsplit=1)[-1]
            or not isinstance(caminho_retornado, str)
            or caminho_retornado != caminho_esperado
        ):
            raise ErroDestinoInvalido(f"{grupo} não corresponde ao destino configurado.")

    def _url_api(
        self,
        caminho: str,
        operacao: str,
        *,
        parametros: tuple[tuple[str, str], ...] = (),
    ) -> str:
        consulta = urlencode((*parametros, ("api-version", self.VERSOES_API[operacao])))
        return f"{caminho}?{consulta}"

    def _obter(self, url: str) -> dict[str, Any]:
        return self._enviar("GET", url)

    def _enviar(
        self,
        metodo: str,
        url: str,
        *,
        json: object | None = None,
        tipo_conteudo: str | None = None,
    ) -> dict[str, Any]:
        headers = {"Content-Type": tipo_conteudo} if tipo_conteudo else None
        ultima: Exception | None = None
        tentativas = self._max_tentativas if metodo == "GET" else 1
        for tentativa in range(tentativas):
            try:
                resposta = self._cliente.request(metodo, url, json=json, headers=headers)
            except (httpx.TimeoutException, httpx.NetworkError) as erro:
                ultima = erro
            else:
                if resposta.status_code in self._ERROS_RETENTAVEIS:
                    ultima = ErroFalhaTransitoria(f"Falha transitória HTTP {resposta.status_code}.")
                else:
                    _verificar_status(resposta)
                    corpo = resposta.json()
                    if not isinstance(corpo, dict):
                        raise ErroAzureDevOps("A resposta do Azure DevOps não é um objeto JSON.")
                    return corpo
            if tentativa + 1 < tentativas:
                time.sleep(self._espera_inicial * (2**tentativa))
        raise ErroFalhaTransitoria(
            "O Azure DevOps não respondeu após as tentativas permitidas."
        ) from ultima


def _nomes(payload: Mapping[str, Any], *, campo: str = "name", recurso: str) -> list[str]:
    valores = payload.get("value")
    if not isinstance(valores, list) or not valores:
        raise ErroDestinoInvalido(f"A resposta de {recurso} não contém valores válidos.")

    nomes: list[str] = []
    for item in valores:
        valor = item.get(campo) if isinstance(item, Mapping) else None
        if not isinstance(valor, str) or not valor:
            raise ErroDestinoInvalido(f"A resposta de {recurso} contém um {campo} inválido.")
        nomes.append(valor)
    return nomes


def _url_azure_valida(valor: str) -> bool:
    if not valor or valor != valor.strip():
        return False
    url = urlparse(valor)
    return url.scheme == "https" and bool(url.netloc) and bool(url.path)


def _verificar_status(resposta: httpx.Response) -> None:
    erros: dict[int, type[ErroAzureDevOps]] = {
        401: ErroAutenticacao,
        403: ErroPermissao,
        404: ErroDestinoInvalido,
        409: ErroConflito,
    }
    classe = erros.get(resposta.status_code)
    if classe:
        raise classe(f"O Azure DevOps recusou a operação (HTTP {resposta.status_code}).")
    if resposta.is_error:
        raise ErroAzureDevOps(f"O Azure DevOps recusou a operação (HTTP {resposta.status_code}).")
