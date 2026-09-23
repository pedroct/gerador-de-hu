"""Carrega a configuração local sem expor credenciais em representações textuais."""

from __future__ import annotations

import getpass
import os
import sys
import tomllib
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import TextIO

from pydantic import BaseModel, ConfigDict, SecretStr, field_validator

from publicar_backlog_demanda_azure_boards.modelos import (
    ConfiguracaoPublicacao,
    Demanda,
    MapeamentoTipos,
)


class ErroConfiguracao(ValueError):
    """Indica que não foi possível obter uma configuração segura e completa."""


class ConfiguracaoAzureDevOps(BaseModel):
    """Agrupa o destino e a credencial local, mantendo o token mascarado."""

    model_config = ConfigDict(frozen=True)

    organizacao: str
    projeto: str
    demanda_id: int
    tipo_demanda: str = "Demanda de Negócio"
    token: SecretStr | None = None
    tipo_epic: str = "Epic"
    tipo_feature: str = "Feature"
    tipo_user_story: str = "User Story"
    tipo_bug: str = "Bug"

    @field_validator(
        "organizacao",
        "projeto",
        "tipo_demanda",
        "tipo_epic",
        "tipo_feature",
        "tipo_user_story",
        "tipo_bug",
    )
    @classmethod
    def validar_texto_obrigatorio(cls, valor: str) -> str:
        """Rejeita campos de destino vazios ou preenchidos apenas por espaços."""
        texto = valor.strip()
        if not texto:
            raise ValueError("deve ser informado")
        return texto

    @field_validator("demanda_id")
    @classmethod
    def validar_demanda(cls, valor: int) -> int:
        """Rejeita um identificador de Demanda que não possa endereçar um work item."""
        if valor <= 0:
            raise ValueError("deve ser um inteiro positivo")
        return valor

    def publicacao_para(self, demanda: Demanda) -> ConfiguracaoPublicacao:
        """Deriva o destino a partir da Demanda, que é a dona dos caminhos.

        `Area Path` e `Iteration Path` deixaram de ser configuráveis por execução:
        publicar sob uma Demanda significa publicar onde ela está.
        """
        return ConfiguracaoPublicacao(
            organizacao=self.organizacao,
            projeto=self.projeto,
            area_path=_normalizar_caminho(self.projeto, demanda.area_path),
            iteration_path=_normalizar_caminho(self.projeto, demanda.iteration_path),
            demanda_id=self.demanda_id,
            mapeamento_tipos=MapeamentoTipos(
                epic=self.tipo_epic,
                feature=self.tipo_feature,
                historia_usuario=self.tipo_user_story,
                bug=self.tipo_bug,
            ),
        )

    def obter_token(self) -> str:
        """Devolve a credencial somente para fluxos remotos que a exigem."""
        if self.token is None:
            raise ErroConfiguracao("A credencial do Azure DevOps é obrigatória para chamadas HTTP.")
        return self.token.get_secret_value()


_CHAVES = {
    "organizacao": "AZURE_DEVOPS_ORGANIZACAO",
    "projeto": "AZURE_DEVOPS_PROJETO",
    "token": "AZURE_DEVOPS_" + "TOKEN",
    "tipo_epic": "AZURE_DEVOPS_TIPO_EPIC",
    "tipo_feature": "AZURE_DEVOPS_TIPO_FEATURE",
    "tipo_user_story": "AZURE_DEVOPS_TIPO_USER_STORY",
    "tipo_bug": "AZURE_DEVOPS_TIPO_BUG",
    "demanda_id": "AZURE_DEVOPS_DEMANDA",
    "tipo_demanda": "AZURE_DEVOPS_TIPO_DEMANDA",
}


def carregar_configuracao(
    argumentos: Mapping[str, str | None] | None = None,
    caminho_arquivo: Path | None = None,
    caminho_env: Path = Path(".env"),
    ambiente: Mapping[str, str] | None = None,
    entrada: TextIO | None = None,
    saida: TextIO | None = None,
    exigir_token: bool = True,
    ler_segredo: Callable[[str], str] | None = None,
) -> ConfiguracaoAzureDevOps:
    """Combina argumentos, TOML, ambiente e perguntas nessa ordem de precedência."""
    argumentos_normalizados = argumentos or {}
    arquivo = _ler_arquivo(caminho_arquivo)
    valores_ambiente = _ler_env(caminho_env)
    valores_ambiente.update(os.environ if ambiente is None else ambiente)
    entrada_interativa = entrada if entrada is not None else sys.stdin
    saida_interativa = saida if saida is not None else sys.stdout

    campos: tuple[str, ...] = (
        "organizacao",
        "projeto",
        "demanda_id",
        "tipo_demanda",
        "tipo_epic",
        "tipo_feature",
        "tipo_user_story",
        "tipo_bug",
    )
    if exigir_token:
        campos += ("token",)
    valores: dict[str, str | None] = {
        campo: _obter_valor(campo, argumentos_normalizados, arquivo, valores_ambiente)
        for campo in campos
    }
    for campo in ("organizacao", "projeto"):
        if not valores[campo]:
            valores[campo] = _perguntar(campo, entrada_interativa, saida_interativa)
    if exigir_token and not valores["token"]:
        leitor = ler_segredo or (lambda prompt: getpass.getpass(prompt))
        valores["token"] = leitor("Credencial do Azure DevOps: ").strip()

    tipos_padrao = {
        "tipo_demanda": "Demanda de Negócio",
        "tipo_epic": "Epic",
        "tipo_feature": "Feature",
        "tipo_user_story": "User Story",
        "tipo_bug": "Bug",
    }
    for campo, padrao in tipos_padrao.items():
        valores[campo] = valores[campo] or padrao

    bruto = valores["demanda_id"]
    if bruto is None:
        bruto = _perguntar("demanda_id", entrada_interativa, saida_interativa)
    try:
        demanda_id = int(str(bruto).strip().lstrip("#"))
    except ValueError as erro:
        raise ErroConfiguracao("O ID da Demanda de Negócio deve ser um número inteiro.") from erro

    try:
        return ConfiguracaoAzureDevOps(
            organizacao=_exigir_valor(valores["organizacao"], "Organização do Azure DevOps"),
            projeto=_exigir_valor(valores["projeto"], "Projeto do Azure DevOps"),
            demanda_id=demanda_id,
            tipo_demanda=_exigir_valor(valores["tipo_demanda"], "Tipo remoto da Demanda"),
            token=(
                SecretStr(_exigir_valor(valores["token"], "Credencial do Azure DevOps"))
                if exigir_token
                else None
            ),
            tipo_epic=_exigir_valor(valores["tipo_epic"], "Tipo remoto de Epic"),
            tipo_feature=_exigir_valor(valores["tipo_feature"], "Tipo remoto de Feature"),
            tipo_user_story=_exigir_valor(valores["tipo_user_story"], "Tipo remoto de User Story"),
            tipo_bug=_exigir_valor(valores["tipo_bug"], "Tipo remoto de Bug"),
        )
    except ValueError as erro:
        raise ErroConfiguracao("A configuração do Azure DevOps é inválida.") from erro


def _ler_arquivo(caminho: Path | None) -> Mapping[str, object]:
    if caminho is None:
        return {}
    with caminho.open("rb") as arquivo:
        conteudo = tomllib.load(arquivo)
    secao = conteudo.get("azure_devops", conteudo)
    if not isinstance(secao, dict):
        raise ErroConfiguracao("A seção azure_devops do arquivo deve ser uma tabela TOML.")
    return secao


def _ler_env(caminho: Path) -> dict[str, str]:
    if not caminho.is_file():
        return {}

    valores: dict[str, str] = {}
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        texto = linha.strip()
        if not texto or texto.startswith("#") or "=" not in texto:
            continue
        chave, valor = texto.split("=", maxsplit=1)
        valores[chave.strip()] = valor.strip().strip('"').strip("'")
    return valores


def _obter_valor(
    campo: str,
    argumentos: Mapping[str, str | None],
    arquivo: Mapping[str, object],
    ambiente: Mapping[str, str],
) -> str | None:
    chave_ambiente = _CHAVES[campo]
    candidatos: tuple[object | None, ...] = (
        argumentos.get(campo, argumentos.get(chave_ambiente)),
        arquivo.get(campo, arquivo.get(chave_ambiente)),
        ambiente.get(chave_ambiente),
    )
    for candidato in candidatos:
        if isinstance(candidato, str) and candidato.strip():
            return candidato.strip()
    return None


def _perguntar(campo: str, entrada: TextIO, saida: TextIO) -> str:
    rotulos = {
        "organizacao": "Organização do Azure DevOps",
        "projeto": "Projeto do Azure DevOps",
        "demanda_id": "ID da Demanda de Negócio",
    }
    rotulo = rotulos[campo]
    saida.write(f"{rotulo}: ")
    valor = _ler_entrada(entrada)
    if not valor:
        raise ErroConfiguracao(f"{rotulo} é obrigatório.")
    return valor


def _ler_entrada(entrada: TextIO) -> str:
    valor = entrada.readline()
    if not valor:
        raise ErroConfiguracao("A entrada interativa foi encerrada antes da configuração.")
    return valor.strip()


def _exigir_valor(valor: str | None, rotulo: str) -> str:
    if valor is None:
        raise ErroConfiguracao(f"{rotulo} é obrigatório.")
    return valor


def _normalizar_caminho(projeto: str, caminho: str) -> str:
    partes = tuple(
        parte.strip() for parte in caminho.replace("/", "\\").split("\\") if parte.strip()
    )
    if partes and partes[0].casefold() == projeto.casefold():
        return "\\".join(partes)
    return "\\".join((projeto, *partes))
