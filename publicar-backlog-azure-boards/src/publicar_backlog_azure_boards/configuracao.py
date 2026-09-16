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

from publicar_backlog_azure_boards.modelos import ConfiguracaoPublicacao, MapeamentoTipos


class ErroConfiguracao(ValueError):
    """Indica que não foi possível obter uma configuração segura e completa."""


class ConfiguracaoAzureDevOps(BaseModel):
    """Agrupa o destino e a credencial local, mantendo o token mascarado."""

    model_config = ConfigDict(frozen=True)

    organizacao: str
    projeto: str
    area_path: str
    iteration_path: str
    token: SecretStr | None = None
    tipo_epic: str = "Epic"
    tipo_feature: str = "Feature"
    tipo_user_story: str = "User Story"
    tipo_bug: str = "Bug"

    @field_validator(
        "organizacao",
        "projeto",
        "area_path",
        "iteration_path",
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

    @property
    def publicacao(self) -> ConfiguracaoPublicacao:
        """Expõe somente os dados de destino necessários para montar o plano."""
        return ConfiguracaoPublicacao(
            organizacao=self.organizacao,
            projeto=self.projeto,
            area_path=_normalizar_caminho(self.projeto, self.area_path),
            iteration_path=_normalizar_caminho(self.projeto, self.iteration_path),
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
    "area_path": "AZURE_DEVOPS_AREA_PATH",
    "area_paths": "AZURE_DEVOPS_AREA_PATHS",
    "iteration_path": "AZURE_DEVOPS_ITERATION_PATH",
    "token": "AZURE_DEVOPS_" + "TOKEN",
    "tipo_epic": "AZURE_DEVOPS_TIPO_EPIC",
    "tipo_feature": "AZURE_DEVOPS_TIPO_FEATURE",
    "tipo_user_story": "AZURE_DEVOPS_TIPO_USER_STORY",
    "tipo_bug": "AZURE_DEVOPS_TIPO_BUG",
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
        "iteration_path",
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
    valores["area_path"] = _obter_area_path(
        argumentos_normalizados,
        arquivo,
        valores_ambiente,
        entrada_interativa,
        saida_interativa,
    )

    for campo in ("organizacao", "projeto", "iteration_path"):
        if not valores[campo]:
            valores[campo] = _perguntar(campo, entrada_interativa, saida_interativa)
    if exigir_token and not valores["token"]:
        leitor = ler_segredo or (lambda prompt: getpass.getpass(prompt))
        valores["token"] = leitor("Credencial do Azure DevOps: ").strip()

    tipos_padrao = {
        "tipo_epic": "Epic",
        "tipo_feature": "Feature",
        "tipo_user_story": "User Story",
        "tipo_bug": "Bug",
    }
    for campo, padrao in tipos_padrao.items():
        valores[campo] = valores[campo] or padrao

    try:
        return ConfiguracaoAzureDevOps(
            organizacao=_exigir_valor(valores["organizacao"], "Organização do Azure DevOps"),
            projeto=_exigir_valor(valores["projeto"], "Projeto do Azure DevOps"),
            area_path=_exigir_valor(valores["area_path"], "Area Path"),
            iteration_path=_exigir_valor(valores["iteration_path"], "Iteration Path"),
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


def _obter_area_path(
    argumentos: Mapping[str, str | None],
    arquivo: Mapping[str, object],
    ambiente: Mapping[str, str],
    entrada: TextIO,
    saida: TextIO,
) -> str:
    area_path = _obter_valor("area_path", argumentos, arquivo, ambiente)
    if area_path:
        return area_path

    area_paths = _obter_valor("area_paths", argumentos, arquivo, ambiente)
    opcoes = tuple(opcao.strip() for opcao in (area_paths or "").split(",") if opcao.strip())
    if len(opcoes) == 1:
        return opcoes[0]
    if len(opcoes) > 1:
        saida.write("Selecione um Area Path: " + ", ".join(opcoes) + "\n")
        escolha = _ler_entrada(entrada)
        if escolha not in opcoes:
            raise ErroConfiguracao("É necessário selecionar um Area Path disponível.")
        return escolha
    return _perguntar("area_path", entrada, saida)


def _perguntar(campo: str, entrada: TextIO, saida: TextIO) -> str:
    rotulos = {
        "organizacao": "Organização do Azure DevOps",
        "projeto": "Projeto do Azure DevOps",
        "area_path": "Area Path",
        "iteration_path": "Iteration Path",
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
