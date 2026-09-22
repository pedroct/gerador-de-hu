"""Leitor somente leitura de uma Demanda de Negócio no Azure Boards."""

from __future__ import annotations

import argparse
import base64
import errno
import getpass
import json
import os
import socket
import sys
import time
import tomllib
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
_CATEGORIAS_ERRO_PUBLICAS = {"consulta", "contrato", "configuração"}


class ErroConsultaDemanda(RuntimeError):
    """Indica que uma Demanda não pôde ser lida ou não atende ao contrato."""

    def __init__(
        self,
        mensagem: str,
        *,
        categoria: str = "consulta",
        campo_ausente: str | None = None,
    ) -> None:
        super().__init__(mensagem)
        self.categoria = (
            categoria if categoria in _CATEGORIAS_ERRO_PUBLICAS else "consulta"
        )
        self.campo_ausente = (
            campo_ausente if campo_ausente in CAMPOS_DEMANDA else None
        )

    @property
    def detalhe_publico(self) -> str | None:
        """Expõe somente diagnóstico derivado de dados controlados pelo contrato."""
        if self.campo_ausente is None:
            return None
        return f"campo remoto obrigatório ausente: {self.campo_ausente}"


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

_ERROS_REDE_TRANSITORIOS = {
    errno.ECONNABORTED,
    errno.ECONNREFUSED,
    errno.ECONNRESET,
    errno.EHOSTUNREACH,
    errno.ENETDOWN,
    errno.ENETRESET,
    errno.ENETUNREACH,
    errno.ETIMEDOUT,
}


class ErroConfiguracao(RuntimeError):
    """Indica que a configuração mínima não foi fornecida."""


def _urlerro_transitorio(erro: URLError) -> bool:
    """Retorna se a causa de uma URLError indica uma falha de rede transitória."""
    causa = erro.reason
    if isinstance(causa, (TimeoutError, ConnectionError, socket.timeout)):
        return True
    return isinstance(causa, OSError) and causa.errno in _ERROS_REDE_TRANSITORIOS


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("id_item", type=int, help="ID da Demanda de Negócio")
    parser.add_argument("--organizacao")
    parser.add_argument("--projeto")
    parser.add_argument("--config", type=str)
    parser.add_argument("--env-file", default=".env")
    return parser


_CHAVES_CONFIGURACAO = {
    "organizacao": "AZURE_DEVOPS_ORGANIZACAO",
    "projeto": "AZURE_DEVOPS_PROJETO",
    "token": "AZURE_DEVOPS_TOKEN",
}


def carregar_configuracao(
    argumentos: argparse.Namespace,
    *,
    ambiente: Mapping[str, str] | None = None,
) -> ConfiguracaoAzureBoards:
    """Carrega configuração com precedência argumento, TOML, .env e ambiente."""
    ambiente = os.environ if ambiente is None else ambiente
    valores_toml: dict[str, str] = {}
    if argumentos.config:
        try:
            with open(argumentos.config, "rb") as arquivo:
                documento = tomllib.load(arquivo)
        except (OSError, tomllib.TOMLDecodeError):
            raise ErroConfiguracao("Não foi possível ler o arquivo de configuração.") from None
        tabela = documento.get("azure_devops", documento)
        if not isinstance(tabela, dict):
            raise ErroConfiguracao("A configuração do Azure DevOps é inválida.")
        for nome, chave in _CHAVES_CONFIGURACAO.items():
            valor = tabela.get(chave, tabela.get(nome))
            if isinstance(valor, str) and valor.strip():
                valores_toml[chave] = valor.strip()

    valores_env_file: dict[str, str] = {}
    try:
        with open(argumentos.env_file, encoding="utf-8") as arquivo:
            for linha in arquivo:
                texto = linha.strip()
                if not texto or texto.startswith("#") or "=" not in texto:
                    continue
                chave, valor = texto.split("=", 1)
                chave = chave.strip()
                valor = valor.strip()
                if len(valor) >= 2 and valor[0] == valor[-1] and valor[0] in "\"'":
                    valor = valor[1:-1]
                if chave in _CHAVES_CONFIGURACAO.values() and valor:
                    valores_env_file[chave] = valor
    except OSError:
        pass

    valores: dict[str, str | None] = {}
    for nome, chave in _CHAVES_CONFIGURACAO.items():
        argumento = getattr(argumentos, nome, None)
        valores[chave] = (
            argumento
            or valores_toml.get(chave)
            or valores_env_file.get(chave)
            or ambiente.get(chave)
        )

    if not valores["AZURE_DEVOPS_ORGANIZACAO"]:
        raise ErroConfiguracao("A organização do Azure DevOps não foi informada.")
    if not valores["AZURE_DEVOPS_PROJETO"]:
        raise ErroConfiguracao("O projeto do Azure DevOps não foi informado.")
    token = valores["AZURE_DEVOPS_TOKEN"]
    if not token:
        if not sys.stdin.isatty():
            raise ErroConfiguracao("O token do Azure DevOps não foi informado.")
        token = getpass.getpass("Credencial do Azure DevOps: ")
    if not token:
        raise ErroConfiguracao("O token do Azure DevOps não foi informado.")
    return ConfiguracaoAzureBoards(
        organizacao=valores["AZURE_DEVOPS_ORGANIZACAO"],
        projeto=valores["AZURE_DEVOPS_PROJETO"],
        token=token,
    )


def requisitar_json(
    url: str,
    cabecalhos: dict[str, str],
    *,
    token: str | None = None,
    abrir: Callable[..., Any] = urlopen,
) -> dict[str, object]:
    """Faz uma requisição GET e decodifica seu corpo JSON como objeto."""
    headers = dict(cabecalhos)
    if token is not None:
        headers["Authorization"] = "Basic " + base64.b64encode(f":{token}".encode()).decode()
    for tentativa in range(3):
        requisicao = Request(url, headers=headers, method="GET")  # noqa: S310
        try:
            with abrir(requisicao) as resposta:  # noqa: S310 - a URL é construída pelo leitor HTTPS.
                corpo = resposta.read()
            payload = json.loads(corpo.decode("utf-8"))
            if not isinstance(payload, dict):
                raise ErroConsultaDemanda("A resposta JSON não é um objeto.")
            return payload
        except HTTPError as erro:
            if erro.code not in {408, 429, 500, 502, 503, 504} or tentativa == 2:
                raise ErroConsultaDemanda(f"Falha HTTP {erro.code}.") from None
        except URLError as erro:
            if not _urlerro_transitorio(erro) or tentativa == 2:
                raise ErroConsultaDemanda("Falha ao consultar o Azure DevOps.") from None
        except (UnicodeDecodeError, JSONDecodeError, OSError):
            raise ErroConsultaDemanda("Falha ao consultar o Azure DevOps.") from None
        if tentativa < 2:
            time.sleep(0.05 * (2**tentativa))
    raise ErroConsultaDemanda("Falha ao consultar o Azure DevOps.")


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
    cabecalhos = {"Accept": "application/json"}
    obter = requisitar or (
        lambda url, headers: _requisitar_json_seguro(url, headers, configuracao.token)
    )

    payload_item = _obter_payload(obter, url_item, cabecalhos, id_demanda)
    campos_item = _objeto(payload_item.get("fields"), f"ID {id_demanda}: fields inválido")
    _validar_identidade_item(payload_item, id_demanda, campos_item)

    payload_campos = _obter_payload(obter, url_campos, cabecalhos, id_demanda)
    campos_disponiveis = _extrair_campos(payload_campos, id_demanda)
    ausentes = [campo for campo in CAMPOS_DEMANDA if campo not in campos_disponiveis]
    if ausentes:
        raise ErroConsultaDemanda(
            f"ID {id_demanda}: o tipo {TIPO_DEMANDA!r} não define o campo {ausentes[0]}.",
            categoria="contrato",
            campo_ausente=ausentes[0],
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


def _requisitar_json_seguro(
    url: str, cabecalhos: dict[str, str], token: str
) -> dict[str, object]:
    try:
        return requisitar_json(url, cabecalhos, token=token)
    except ErroConsultaDemanda:
        raise


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
    except (JSONDecodeError, UnicodeDecodeError, URLError, OSError, ValueError):
        raise ErroConsultaDemanda(
            f"Falha ao consultar a Demanda {id_demanda}: erro de comunicação ou resposta inválida."
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
    if isinstance(valor, list) and not valor:
        return None
    if not isinstance(valor, str):
        raise ErroConsultaDemanda(f"ID {id_demanda}: campo {nome} não é textual.")
    return valor if valor.strip() else None


def principal(argv: list[str] | None = None) -> int:
    try:
        argumentos = construir_parser().parse_args(argv)
        configuracao = carregar_configuracao(argumentos)
        demanda = consultar_demanda(argumentos.id_item, configuracao)
        saida = {
            "id": demanda.id,
            "url": demanda.url,
            "tipo": demanda.tipo,
            "titulo": demanda.titulo,
            "campos": {
                campo: demanda.valores.get(campo)
                for campo in CAMPOS_DEMANDA
                if campo != "System.Title"
            },
        }
        print(json.dumps(saida, ensure_ascii=False))
        return 0
    except ErroConfiguracao:
        print("Erro [configuração]: não foi possível consultar a Demanda de Negócio.")
        return 1
    except ErroConsultaDemanda as erro:
        detalhe = erro.detalhe_publico or "não foi possível consultar a Demanda de Negócio"
        print(f"Erro [{erro.categoria}]: {detalhe}.")
        return 1


if __name__ == "__main__":
    raise SystemExit(principal())
