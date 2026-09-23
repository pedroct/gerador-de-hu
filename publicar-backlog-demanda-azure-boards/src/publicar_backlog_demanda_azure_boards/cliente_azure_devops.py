"""Cliente REST mínimo e seguro para verificação e publicação no Azure DevOps."""

from __future__ import annotations

import base64
import time
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote, unquote, urlencode, urlparse
from uuid import UUID

import httpx

from publicar_backlog_demanda_azure_boards.modelos import (
    ConfiguracaoPublicacao,
    OperacaoCriacao,
)

_CAMPOS_OBRIGATORIOS_COMUNS = frozenset(
    {
        "System.Title",
        "System.Description",
        "System.AreaPath",
        "System.IterationPath",
    }
)
_CAMPO_CRITERIOS_ACEITACAO = "Microsoft.VSTS.Common.AcceptanceCriteria"
_RELACAO_HIERARQUICA = "System.LinkTypes.Hierarchy-Reverse"
# O Azure DevOps sempre insere este segmento fixo em `path` logo após o projeto,
# mesmo quando a consulta usa o caminho curto sem ele (confirmado contra a API real).
_ROTULOS_ESTRUTURA = {"Areas": "Area", "Iterations": "Iteration"}


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


class ErroCriacaoAmbigua(ErroAzureDevOps):
    """A resposta não permite saber se o POST de criação persistiu o item."""


class ErroRespostaInvalida(ErroAzureDevOps):
    """A resposta bem-sucedida não contém JSON consumível pelo cliente."""


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
        self._base_organizacao_url = (
            f"https://dev.azure.com/{quote(configuracao.organizacao, safe='')}"
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
        self._campos_por_tipo: dict[str, frozenset[str]] = {}

    @property
    def tipos_remotos(self) -> tuple[str, ...]:
        """Expõe somente os nomes de tipo usados na verificação e na criação."""
        return self.configuracao.mapeamento_tipos.nomes_remotos()

    def verificar_destino(self, configuracao: ConfiguracaoPublicacao) -> VerificacaoDestino:
        """Consulta tipos, campos, relações e caminhos sem criar work items."""
        if configuracao != self.configuracao:
            raise ErroDestinoInvalido("A configuração consultada difere do cliente configurado.")

        tipos_payload = self._obter(self._url_api("/_apis/wit/workitemtypes", "tipos"))
        tipos = tuple(_nomes(tipos_payload, recurso="tipos de work item"))
        tipos_ausentes = set(self.tipos_remotos).difference(tipos)
        if tipos_ausentes:
            raise ErroDestinoInvalido(
                "O projeto não disponibiliza os tipos obrigatórios: "
                + ", ".join(sorted(tipos_ausentes))
                + "."
            )

        campos: set[str] = set()
        campos_por_tipo: dict[str, frozenset[str]] = {}
        for tipo in self.tipos_remotos:
            payload = self._obter(
                self._url_api(f"/_apis/wit/workitemtypes/{quote(tipo, safe='')}/fields", "campos")
            )
            campos_do_tipo = set(
                _nomes(payload, campo="referenceName", recurso=f"campos de {tipo}")
            )
            campos_ausentes = _CAMPOS_OBRIGATORIOS_COMUNS.difference(campos_do_tipo)
            if campos_ausentes:
                raise ErroDestinoInvalido(
                    f"{tipo} não disponibiliza os campos obrigatórios: "
                    + ", ".join(sorted(campos_ausentes))
                    + "."
                )
            campos_por_tipo[tipo] = frozenset(campos_do_tipo)
            campos.update(campos_do_tipo)

        self._campos_por_tipo = campos_por_tipo

        relacoes_payload = self._obter(
            self._url_api(
                "/_apis/wit/workitemrelationtypes",
                "relacoes",
                base_url=self._base_organizacao_url,
            )
        )
        relacoes = tuple(
            _nomes(relacoes_payload, campo="referenceName", recurso="relações de work item")
        )
        if _RELACAO_HIERARQUICA not in relacoes:
            raise ErroDestinoInvalido(
                "A relação hierárquica de pai não está disponível no projeto."
            )
        self._validar_caminho("Areas", "area", configuracao.area_path)
        self._validar_caminho("Iterations", "iteration", configuracao.iteration_path)
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
        try:
            item_id = payload.get("id")
            url = payload.get("url")
            if isinstance(item_id, bool) or not isinstance(item_id, int) or item_id <= 0:
                raise ValueError("id ausente ou inválido")
            if not isinstance(url, str) or not _url_azure_valida(url):
                raise ValueError("URL ausente, malformada ou não HTTPS")
        except (ValueError, UnicodeError) as erro:
            raise ErroCriacaoAmbigua(
                "A criação respondeu sem identidade válida; reconcilie manualmente o destino."
            ) from erro
        return RegistroCriado(id=item_id, tipo=operacao.tipo.value, url=url)

    def _enviar_criacao(
        self, operacao: OperacaoCriacao, *, validar: bool, id_pai: int | None
    ) -> dict[str, Any]:
        patch: list[dict[str, object]] = [
            {"op": "add", "path": "/fields/System.Title", "value": operacao.titulo},
            {"op": "add", "path": "/fields/System.Description", "value": operacao.descricao},
            {"op": "add", "path": "/fields/System.AreaPath", "value": self.configuracao.area_path},
            {
                "op": "add",
                "path": "/fields/System.IterationPath",
                "value": self.configuracao.iteration_path,
            },
        ]
        campos_tipo = self._campos_por_tipo.get(operacao.tipo_remoto)
        if campos_tipo is None or _CAMPO_CRITERIOS_ACEITACAO in campos_tipo:
            patch.insert(
                2,
                {
                    "op": "add",
                    "path": f"/fields/{_CAMPO_CRITERIOS_ACEITACAO}",
                    "value": operacao.criterios_aceitacao,
                },
            )
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
            f"/_apis/wit/workitems/${quote(operacao.tipo_remoto, safe='')}",
            "criacao",
            parametros=parametros,
        )
        try:
            return self._enviar(
                "POST", url, json=patch, tipo_conteudo="application/json-patch+json"
            )
        except ErroFalhaTransitoria as erro:
            if validar:
                raise
            raise ErroCriacaoAmbigua(
                "Não é possível confirmar se a criação foi persistida; "
                "reconcilie manualmente antes de nova escrita."
            ) from erro
        except ErroRespostaInvalida as erro:
            if validar:
                raise
            raise ErroCriacaoAmbigua(
                "Não é possível confirmar se a criação foi persistida; "
                "reconcilie manualmente antes de nova escrita."
            ) from erro
        except (ValueError, UnicodeError) as erro:
            if validar:
                raise
            raise ErroCriacaoAmbigua(
                "Não é possível confirmar se a criação foi persistida; "
                "reconcilie manualmente antes de nova escrita."
            ) from erro

    def _validar_caminho(self, grupo: str, tipo_estrutura: str, caminho: str) -> None:
        partes = tuple(
            parte.strip() for parte in caminho.replace("/", "\\").split("\\") if parte.strip()
        )
        if not partes or partes[0].casefold() != self.configuracao.projeto.casefold():
            raise ErroDestinoInvalido(
                f"{grupo} deve começar pelo projeto {self.configuracao.projeto}."
            )
        caminho_relativo = "/".join(quote(parte, safe="") for parte in partes[1:])
        sufixo = f"/{caminho_relativo}" if caminho_relativo else ""
        payload = self._obter(
            self._url_api(
                f"/_apis/wit/classificationnodes/{grupo}{sufixo}",
                "classificacao",
            )
        )
        nome = payload.get("name")
        caminho_retornado = payload.get("path")
        url_retornada = payload.get("url")
        estrutura_retornada = payload.get("structureType")
        caminho_esperado = "\\" + "\\".join((partes[0], _ROTULOS_ESTRUTURA[grupo], *partes[1:]))
        if (
            not isinstance(nome, str)
            or not nome
            or nome != partes[-1]
            or not isinstance(caminho_retornado, str)
            or caminho_retornado != caminho_esperado
            or not isinstance(url_retornada, str)
            or not _url_classificacao_valida(url_retornada, grupo, partes, self.configuracao)
            or estrutura_retornada != tipo_estrutura
        ):
            raise ErroDestinoInvalido(f"{grupo} não corresponde ao destino configurado.")

    def _url_api(
        self,
        caminho: str,
        operacao: str,
        *,
        parametros: tuple[tuple[str, str], ...] = (),
        base_url: str | None = None,
    ) -> str:
        consulta = urlencode((*parametros, ("api-version", self.VERSOES_API[operacao])))
        return f"{base_url or ''}{caminho}?{consulta}"

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
            except httpx.RequestError as erro:
                ultima = erro
            else:
                if resposta.status_code in self._ERROS_RETENTAVEIS:
                    ultima = ErroFalhaTransitoria(f"Falha transitória HTTP {resposta.status_code}.")
                else:
                    _verificar_status(resposta)
                    try:
                        corpo = resposta.json()
                    except ValueError as erro:
                        raise ErroRespostaInvalida(
                            "A resposta bem-sucedida do Azure DevOps não é JSON válido."
                        ) from erro
                    if not isinstance(corpo, dict):
                        raise ErroRespostaInvalida(
                            "A resposta do Azure DevOps não é um objeto JSON."
                        )
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
    try:
        url = urlparse(valor)
    except (ValueError, UnicodeError):
        return False
    return url.scheme == "https" and bool(url.netloc) and bool(url.path)


def _url_classificacao_valida(
    valor: str,
    grupo: str,
    partes: tuple[str, ...],
    configuracao: ConfiguracaoPublicacao,
) -> bool:
    """Confere a URL oficial do nó sem tratar seu caminho como campo do item."""
    if not _url_azure_valida(valor):
        return False
    try:
        url = urlparse(valor)
        hostname = url.hostname
        segmentos = tuple(unquote(segmento) for segmento in url.path.split("/") if segmento)
    except (ValueError, UnicodeError):
        return False

    caminho_nodo = tuple(partes[1:])
    esperado = ("_apis", "wit", "classificationnodes", grupo, *caminho_nodo)
    if (
        hostname is None
        or hostname.casefold() != "dev.azure.com"
        or len(segmentos) != len(esperado) + 2
        or segmentos[0].casefold() != configuracao.organizacao.casefold()
        or tuple(segmento.casefold() for segmento in segmentos[2:5])
        != tuple(segmento.casefold() for segmento in esperado[:3])
        or segmentos[5:] != esperado[3:]
    ):
        return False

    projeto_retornado = segmentos[1]
    if projeto_retornado.casefold() == configuracao.projeto.casefold():
        return True
    try:
        UUID(projeto_retornado)
    except (ValueError, AttributeError):
        return False
    return True


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
