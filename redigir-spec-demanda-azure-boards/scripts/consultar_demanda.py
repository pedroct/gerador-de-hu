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
from html.parser import HTMLParser
from json import JSONDecodeError
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

TIPO_DEMANDA = "Demanda de Negócio"
CAMPO_TITULO = "System.Title"
CAMPOS_DEMANDA = (
    CAMPO_TITULO,
    "Custom.DemandaAreaSolicitante",
    "Custom.DemandaPublicoAlvo",
    "Custom.DemandaValorEsperado",
    "Custom.DemandaDoraResolver",
    "Custom.DemandaRegraseRestricoes",
)
_CATEGORIAS_ERRO_PUBLICAS = {"consulta", "contrato", "configuração"}

TIPO_HTML = "html"
_TIPOS_TEXTUAIS = frozenset({"string", TIPO_HTML, "plainText"})
"""Tipos remotos que o leitor sabe converter em texto. Identidade e picklist não entram."""

_TAGS_BLOCO = frozenset({"p", "div", "tr", "blockquote", "h1", "h2", "h3", "h4", "h5", "h6"})

TIMEOUT_SEGUNDOS = 30
"""Limite de espera por requisição. Sem ele a CLI pode travar indefinidamente."""

_TENTATIVAS = 3
_ESPERAS_RETRY = (0.5, 1.0)
_ESPERA_RETRY_AFTER_MAXIMA = 5.0
_HTTP_TRANSITORIOS = frozenset({408, 429, 500, 502, 503, 504})
_FALHA_CONSULTA = "Falha ao consultar o Azure DevOps."

_DETALHES_HTTP_PUBLICOS = {
    401: "credencial inválida ou ausente para o Azure DevOps",
    403: "credencial sem permissão para ler esta Demanda de Negócio",
    404: "Demanda de Negócio não encontrada para o ID informado",
}
"""Diagnósticos derivados apenas do código HTTP, que não revelam nada da credencial."""


class ErroConsultaDemanda(RuntimeError):
    """Indica que uma Demanda não pôde ser lida ou não atende ao contrato."""

    def __init__(
        self,
        mensagem: str,
        *,
        categoria: str = "consulta",
        campo_ausente: str | None = None,
        campo_nao_textual: str | None = None,
        codigo_http: int | None = None,
    ) -> None:
        super().__init__(mensagem)
        self.categoria = categoria if categoria in _CATEGORIAS_ERRO_PUBLICAS else "consulta"
        self.campo_ausente = campo_ausente if campo_ausente in CAMPOS_DEMANDA else None
        self.campo_nao_textual = campo_nao_textual if campo_nao_textual in CAMPOS_DEMANDA else None
        self.codigo_http = codigo_http if codigo_http in _DETALHES_HTTP_PUBLICOS else None

    @property
    def detalhe_publico(self) -> str | None:
        """Expõe somente diagnóstico derivado de dados controlados pelo contrato."""
        if self.campo_ausente is not None:
            return f"campo remoto obrigatório ausente: {self.campo_ausente}"
        if self.campo_nao_textual is not None:
            return f"campo remoto com tipo não textual: {self.campo_nao_textual}"
        if self.codigo_http is not None:
            return _DETALHES_HTTP_PUBLICOS[self.codigo_http]
        return None


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


_ORGANIZACAO_AUSENTE = "informe a organização em --organizacao ou AZURE_DEVOPS_ORGANIZACAO"
_PROJETO_AUSENTE = "informe o projeto em --projeto ou AZURE_DEVOPS_PROJETO"
_CREDENCIAL_AUSENTE = "informe a credencial em AZURE_DEVOPS_TOKEN ou execute em terminal interativo"
_CONFIG_ILEGIVEL = "não foi possível ler o arquivo indicado em --config"
_CONFIG_INVALIDA = "a tabela azure_devops do arquivo de configuração é inválida"

_DETALHES_CONFIGURACAO_PUBLICOS = frozenset(
    {
        _ORGANIZACAO_AUSENTE,
        _PROJETO_AUSENTE,
        _CREDENCIAL_AUSENTE,
        _CONFIG_ILEGIVEL,
        _CONFIG_INVALIDA,
    }
)
"""Destino e caminho de arquivo não são segredo; o valor da credencial nunca aparece aqui."""


class ErroConfiguracao(RuntimeError):
    """Indica que a configuração mínima não foi fornecida."""

    def __init__(self, mensagem: str, *, detalhe_publico: str | None = None) -> None:
        super().__init__(mensagem)
        self.detalhe_publico = (
            detalhe_publico if detalhe_publico in _DETALHES_CONFIGURACAO_PUBLICOS else None
        )


class _ExtratorTexto(HTMLParser):
    """Reduz o HTML de um campo do Boards a texto legível, sem dependência externa."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._partes: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "br":
            self._partes.append("\n")
        elif tag == "li":
            self._partes.append("\n- ")

    def handle_endtag(self, tag: str) -> None:
        if tag in _TAGS_BLOCO:
            self._partes.append("\n")

    def handle_data(self, dados: str) -> None:
        self._partes.append(dados)

    def texto(self) -> str:
        bruto = "".join(self._partes).replace("\xa0", " ")
        linhas: list[str] = []
        for linha in bruto.split("\n"):
            limpa = " ".join(linha.split())
            # Preserva uma linha em branco como separador, nunca duas seguidas.
            if limpa or (linhas and linhas[-1]):
                linhas.append(limpa)
        return "\n".join(linhas).strip()


def converter_html(valor: str) -> str:
    """Converte um campo `html` em texto. Valor sem marcação atravessa inalterado."""
    extrator = _ExtratorTexto()
    extrator.feed(valor)
    extrator.close()
    return extrator.texto()


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


# Mapeia o nome curto (argumento e chave TOML) ao nome da variável de ambiente.
# Os valores são nomes de variável, nunca credenciais — daí o nosec em "token".
_CHAVES_CONFIGURACAO = {
    "organizacao": "AZURE_DEVOPS_ORGANIZACAO",
    "projeto": "AZURE_DEVOPS_PROJETO",
    "token": "AZURE_DEVOPS_TOKEN",  # nosec B105
}


def _ler_toml(caminho: str) -> dict[str, str]:
    """Lê a tabela `azure_devops` (ou a raiz) do arquivo indicado em `--config`."""
    try:
        with open(caminho, "rb") as arquivo:
            documento = tomllib.load(arquivo)
    except (OSError, tomllib.TOMLDecodeError):
        raise ErroConfiguracao(
            "Não foi possível ler o arquivo de configuração.",
            detalhe_publico=_CONFIG_ILEGIVEL,
        ) from None
    tabela = documento.get("azure_devops", documento)
    if not isinstance(tabela, dict):
        raise ErroConfiguracao(
            "A configuração do Azure DevOps é inválida.",
            detalhe_publico=_CONFIG_INVALIDA,
        )
    valores: dict[str, str] = {}
    for nome, chave in _CHAVES_CONFIGURACAO.items():
        valor = tabela.get(chave, tabela.get(nome))
        if isinstance(valor, str) and valor.strip():
            valores[chave] = valor.strip()
    return valores


def _ler_env_file(caminho: str) -> dict[str, str]:
    """Lê as chaves conhecidas de um `.env`. A ausência do arquivo não é erro."""
    valores: dict[str, str] = {}
    try:
        with open(caminho, encoding="utf-8") as arquivo:
            linhas = arquivo.readlines()
    except OSError:
        return valores
    for linha in linhas:
        texto = linha.strip()
        if not texto or texto.startswith("#") or "=" not in texto:
            continue
        chave, valor = (parte.strip() for parte in texto.split("=", 1))
        if len(valor) >= 2 and valor[0] == valor[-1] and valor[0] in "\"'":
            valor = valor[1:-1]
        if chave in _CHAVES_CONFIGURACAO.values() and valor:
            valores[chave] = valor
    return valores


def carregar_configuracao(
    argumentos: argparse.Namespace,
    *,
    ambiente: Mapping[str, str] | None = None,
) -> ConfiguracaoAzureBoards:
    """Carrega configuração com precedência argumento, TOML, .env e ambiente."""
    ambiente = os.environ if ambiente is None else ambiente
    valores_toml = _ler_toml(argumentos.config) if argumentos.config else {}
    valores_env_file = _ler_env_file(argumentos.env_file)

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
        raise ErroConfiguracao(
            "A organização do Azure DevOps não foi informada.",
            detalhe_publico=_ORGANIZACAO_AUSENTE,
        )
    if not valores["AZURE_DEVOPS_PROJETO"]:
        raise ErroConfiguracao(
            "O projeto do Azure DevOps não foi informado.",
            detalhe_publico=_PROJETO_AUSENTE,
        )
    token = valores["AZURE_DEVOPS_TOKEN"]
    if not token:
        if not sys.stdin.isatty():
            raise ErroConfiguracao(
                "O token do Azure DevOps não foi informado.",
                detalhe_publico=_CREDENCIAL_AUSENTE,
            )
        token = getpass.getpass("Credencial do Azure DevOps: ")
    if not token:
        raise ErroConfiguracao(
            "O token do Azure DevOps não foi informado.",
            detalhe_publico=_CREDENCIAL_AUSENTE,
        )
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
    abrir: Callable[..., Any] | None = None,
) -> dict[str, object]:
    """Faz uma requisição GET e decodifica seu corpo JSON como objeto."""
    # Resolvido na chamada, e não como default, para que o transporte seja substituível.
    abrir = urlopen if abrir is None else abrir
    headers = dict(cabecalhos)
    if token is not None:
        headers["Authorization"] = "Basic " + base64.b64encode(f":{token}".encode()).decode()
    for tentativa in range(_TENTATIVAS):
        requisicao = Request(url, headers=headers, method="GET")  # noqa: S310
        try:
            # A URL é construída pelo leitor e sempre HTTPS; daí o S310 suprimido.
            with abrir(requisicao, timeout=TIMEOUT_SEGUNDOS) as resposta:  # noqa: S310
                corpo = resposta.read()
            payload = json.loads(corpo.decode("utf-8"))
            if not isinstance(payload, dict):
                raise ErroConsultaDemanda("A resposta JSON não é um objeto.")
            return payload
        except (UnicodeDecodeError, JSONDecodeError, OSError) as erro:
            espera = _espera_apos_falha(erro, tentativa)
        time.sleep(espera)
    raise ErroConsultaDemanda(_FALHA_CONSULTA)


def _espera_apos_falha(erro: Exception, tentativa: int) -> float:
    """Decide se a falha é repetível: devolve a espera ou levanta o erro público."""
    ultima = tentativa == _TENTATIVAS - 1
    if isinstance(erro, HTTPError):
        if erro.code not in _HTTP_TRANSITORIOS or ultima:
            raise ErroConsultaDemanda(f"Falha HTTP {erro.code}.", codigo_http=erro.code) from None
        return _espera_retry(tentativa, erro)
    if isinstance(erro, URLError):
        if not _urlerro_transitorio(erro) or ultima:
            raise ErroConsultaDemanda(_FALHA_CONSULTA) from None
        return _espera_retry(tentativa)
    # Um timeout do socket chega cru, fora de URLError, e é tão transitório quanto.
    if isinstance(erro, (TimeoutError, ConnectionError)) and not ultima:
        return _espera_retry(tentativa)
    raise ErroConsultaDemanda(_FALHA_CONSULTA) from None


def _espera_retry(tentativa: int, erro: HTTPError | None = None) -> float:
    """Calcula a espera até a próxima tentativa, honrando Retry-After quando presente."""
    padrao = _ESPERAS_RETRY[min(tentativa, len(_ESPERAS_RETRY) - 1)]
    if erro is None:
        return padrao
    return max(padrao, _retry_after_segundos(erro) or 0.0)


def _retry_after_segundos(erro: HTTPError) -> float | None:
    """Lê Retry-After em segundos, ignorando o formato de data e valores fora de faixa."""
    cabecalhos = getattr(erro, "headers", None)
    bruto = cabecalhos.get("Retry-After") if cabecalhos is not None else None
    if not isinstance(bruto, str):
        return None
    try:
        segundos = float(bruto.strip())
    except ValueError:
        return None
    if segundos <= 0:
        return None
    return min(segundos, _ESPERA_RETRY_AFTER_MAXIMA)


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
    url_tipos = f"{base_url}/_apis/wit/fields?api-version=7.1"
    cabecalhos = {"Accept": "application/json"}
    obter = requisitar or (
        lambda url, headers: requisitar_json(url, headers, token=configuracao.token)
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

    payload_tipos = _obter_payload(obter, url_tipos, cabecalhos, id_demanda)
    tipos = _extrair_tipos(payload_tipos, id_demanda)
    _validar_tipos(tipos, id_demanda)

    titulo = _texto_obrigatorio(
        campos_item, CAMPO_TITULO, id_demanda, html=tipos[CAMPO_TITULO] == TIPO_HTML
    )
    valores = {
        campo: _texto_opcional(campos_item, campo, id_demanda, html=tipos[campo] == TIPO_HTML)
        for campo in CAMPOS_DEMANDA
        if campo != CAMPO_TITULO
    }
    return DemandaNegocio(
        id=id_demanda,
        url=_url_item(payload_item, id_demanda),
        tipo=TIPO_DEMANDA,
        titulo=titulo,
        valores=valores,
    )


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
            f"Falha HTTP {erro.code} ao consultar a Demanda {id_demanda}.",
            codigo_http=erro.code,
        ) from None
    # URLError deriva de OSError; JSONDecodeError e UnicodeDecodeError, de ValueError.
    except (OSError, ValueError):
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


def _extrair_tipos(payload: Mapping[str, object], id_demanda: int) -> dict[str, str]:
    """Mapeia cada campo remoto ao seu tipo declarado, que diz o que precisa de conversão."""
    valor = payload.get("value")
    if not isinstance(valor, list) or not valor:
        raise ErroConsultaDemanda(f"ID {id_demanda}: resposta de tipos de campo inválida.")
    tipos: dict[str, str] = {}
    for item in valor:
        if not isinstance(item, dict):
            continue
        nome, tipo = item.get("referenceName"), item.get("type")
        if isinstance(nome, str) and isinstance(tipo, str):
            tipos[nome] = tipo
    return tipos


def _validar_tipos(tipos: Mapping[str, str], id_demanda: int) -> None:
    """Recusa antes de redigir um campo que o leitor não sabe converter em texto."""
    for campo in CAMPOS_DEMANDA:
        tipo = tipos.get(campo)
        if tipo is None:
            raise ErroConsultaDemanda(
                f"ID {id_demanda}: o tipo remoto do campo {campo} não foi encontrado.",
                categoria="contrato",
                campo_ausente=campo,
            )
        if tipo not in _TIPOS_TEXTUAIS:
            raise ErroConsultaDemanda(
                f"ID {id_demanda}: campo {campo} tem tipo remoto {tipo!r}, não textual.",
                categoria="contrato",
                campo_nao_textual=campo,
            )


def _texto_obrigatorio(
    campos: Mapping[str, object], nome: str, id_demanda: int, *, html: bool = False
) -> str:
    valor = campos.get(nome)
    if not isinstance(valor, str) or not valor.strip():
        raise ErroConsultaDemanda(f"ID {id_demanda}: campo {nome} vazio ou não textual.")
    texto = converter_html(valor) if html else valor
    if not texto.strip():
        raise ErroConsultaDemanda(f"ID {id_demanda}: campo {nome} vazio ou não textual.")
    return texto


def _texto_opcional(
    campos: Mapping[str, object], nome: str, id_demanda: int, *, html: bool = False
) -> str | None:
    valor = campos.get(nome)
    if valor is None:
        return None
    if isinstance(valor, list) and not valor:
        return None
    if not isinstance(valor, str):
        raise ErroConsultaDemanda(f"ID {id_demanda}: campo {nome} não é textual.")
    texto = converter_html(valor) if html else valor
    return texto if texto.strip() else None


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
                if campo != CAMPO_TITULO
            },
        }
        print(json.dumps(saida, ensure_ascii=False))
        return 0
    except ErroConfiguracao as erro:
        detalhe = erro.detalhe_publico or "não foi possível consultar a Demanda de Negócio"
        print(f"Erro [configuração]: {detalhe}.", file=sys.stderr)
        return 1
    except ErroConsultaDemanda as erro:
        detalhe = erro.detalhe_publico or "não foi possível consultar a Demanda de Negócio"
        print(f"Erro [{erro.categoria}]: {detalhe}.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(principal())
