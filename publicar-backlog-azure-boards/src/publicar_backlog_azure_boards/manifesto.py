"""Leitura e gravação segura do manifesto de publicação."""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from publicar_backlog_azure_boards.modelos import (
    ConfiguracaoPublicacao,
    RegistroManifesto,
    TipoItem,
)


@dataclass(frozen=True)
class Manifesto:
    """Registra a identidade do plano e os work items já criados."""

    hash_plano: str = ""
    configuracao: ConfiguracaoPublicacao | None = None
    itens: dict[str, RegistroManifesto] = field(default_factory=dict)
    titulos: dict[str, str] = field(default_factory=dict)
    origem: str = "backlog.md"
    versao: int = 1


def ler_manifesto(caminho: Path) -> Manifesto:
    """Lê um manifesto existente ou retorna um manifesto vazio."""
    if not caminho.is_file():
        return Manifesto()

    try:
        dados = json.loads(caminho.read_text(encoding="utf-8"))
        return _converter(dados)
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as erro:
        raise ValueError(f"O manifesto {caminho} é inválido.") from erro


def gravar_manifesto(caminho: Path, manifesto: Manifesto) -> None:
    """Grava o manifesto em arquivo temporário no mesmo diretório e o substitui."""
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=caminho.parent,
            prefix=f".{caminho.name}.",
            delete=False,
        ) as arquivo:
            temporario = arquivo.name
            json.dump(_serializar(manifesto), arquivo, ensure_ascii=False, indent=2, sort_keys=True)
            arquivo.write("\n")
            arquivo.flush()
            os.fsync(arquivo.fileno())
        os.replace(temporario, caminho)
        temporario = None
        _sincronizar_diretorio(caminho.parent)
    finally:
        if temporario is not None:
            try:
                os.unlink(temporario)
            except FileNotFoundError:
                pass


def _serializar(manifesto: Manifesto) -> dict[str, Any]:
    configuracao = manifesto.configuracao
    if configuracao is None:
        destino: dict[str, str] | None = None
    else:
        destino = {
            "organizacao": configuracao.organizacao,
            "projeto": configuracao.projeto,
            "area_path": configuracao.area_path,
            "iteration_path": configuracao.iteration_path,
        }
    return {
        "versao": manifesto.versao,
        "origem": manifesto.origem,
        "hash_plano": manifesto.hash_plano,
        "destino": destino,
        "itens": {
            chave: {
                "id": registro.id,
                "tipo": registro.tipo.value,
                "titulo": manifesto.titulos.get(chave),
                "url": registro.url,
            }
            for chave, registro in manifesto.itens.items()
        },
    }


def _converter(dados: object) -> Manifesto:
    if not isinstance(dados, dict):
        raise ValueError("A raiz do manifesto deve ser um objeto JSON.")
    if dados.get("versao") != 1 or not isinstance(dados.get("origem"), str):
        raise ValueError("A versão ou a origem do manifesto é inválida.")
    hash_plano = dados.get("hash_plano")
    destino = dados.get("destino")
    itens = dados.get("itens")
    if (
        not isinstance(hash_plano, str)
        or not isinstance(destino, (dict, type(None)))
        or not isinstance(itens, dict)
    ):
        raise ValueError("O manifesto não contém seus campos obrigatórios.")
    if destino is None:
        if hash_plano or itens:
            raise ValueError("Um manifesto com dados exige um destino completo.")
        configuracao = None
    elif isinstance(destino, dict):
        configuracao = _configuracao(destino)
    else:
        raise ValueError("O destino do manifesto é inválido.")
    registros: dict[str, RegistroManifesto] = {}
    titulos: dict[str, str] = {}
    for chave, dados_item in itens.items():
        if not isinstance(chave, str) or not isinstance(dados_item, dict):
            raise ValueError("Um item do manifesto é inválido.")
        item_id = dados_item.get("id")
        tipo = dados_item.get("tipo")
        titulo = dados_item.get("titulo")
        url = dados_item.get("url")
        if (
            isinstance(item_id, bool)
            or not isinstance(item_id, int)
            or item_id <= 0
            or not isinstance(tipo, str)
            or not isinstance(titulo, str)
            or not titulo
            or not isinstance(url, str)
            or not url
        ):
            raise ValueError("Um item do manifesto não contém identidade completa.")
        try:
            tipo_item = TipoItem(tipo)
        except ValueError as erro:
            raise ValueError("Um item do manifesto tem tipo inválido.") from erro
        registros[chave] = RegistroManifesto(item_id, tipo_item, url)
        titulos[chave] = titulo
    return Manifesto(
        hash_plano=hash_plano,
        configuracao=configuracao,
        itens=registros,
        titulos=titulos,
        origem=dados["origem"],
    )


def _configuracao(destino: dict[str, object]) -> ConfiguracaoPublicacao:
    campos = ("organizacao", "projeto", "area_path", "iteration_path")
    valores = [destino.get(campo) for campo in campos]
    if not all(isinstance(valor, str) and valor for valor in valores):
        raise ValueError("O destino do manifesto é inválido.")
    return ConfiguracaoPublicacao(*valores)  # type: ignore[arg-type]


def _sincronizar_diretorio(diretorio: Path) -> None:
    descritor = os.open(diretorio, os.O_RDONLY)
    try:
        os.fsync(descritor)
    finally:
        os.close(descritor)
