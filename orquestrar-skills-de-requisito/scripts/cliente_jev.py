"""Cliente mínimo para o modelo Jev (TypeSafe) via Decisions API do OpenRouter.

Cópia própria da skill: cada skill deste repositório é instalável avulsa
(`npx skills add --skill ...`), então não pode depender de módulo irmão.

Contrato: POST https://openrouter.ai/api/alpha/decisions
Corpo: {"model": ..., "state": ..., "questions": {...}}
Referência: https://openrouter.ai/blog/tutorials/how-to-use-jev/ e https://docs.typesafe.ai/api

Sem dependências externas de propósito. O abridor da requisição é injetável, como em
`redigir-spec-demanda-azure-boards/scripts/consultar_demanda.py`, o que permite testar
sem rede.
"""

from __future__ import annotations

import json
import os
import urllib.error
from collections.abc import Callable
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

ENDPOINT = "https://openrouter.ai/api/alpha/decisions"
MODELO = "typesafe/jev-1.13"
TIMEOUT_SEGUNDOS = 60


def _procurar_env() -> Path | None:
    """Procura um .env subindo a partir deste arquivo.

    A skill pode ser instalada avulsa (`npx skills add --skill ...`), então não há
    raiz de repositório garantida: sobe até encontrar ou até o topo do sistema.
    """
    for diretorio in Path(__file__).resolve().parents:
        candidato = diretorio / ".env"
        if candidato.is_file():
            return candidato
    return None


def carregar_chave() -> str:
    """Lê JEV_OPENROUTER_API do ambiente ou do .env mais próximo."""
    chave = os.environ.get("JEV_OPENROUTER_API")
    if chave:
        return chave

    arquivo = _procurar_env()
    if arquivo is None:
        raise RuntimeError(
            "JEV_OPENROUTER_API não está no ambiente e nenhum .env foi encontrado. "
            "Defina a variável ou crie um .env — veja .env.example."
        )

    for linha in arquivo.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha.startswith("JEV_OPENROUTER_API=") or linha.startswith("#"):
            continue
        valor = linha.split("=", 1)[1].strip().strip("\"'")
        if valor:
            return valor

    raise RuntimeError(f"JEV_OPENROUTER_API está ausente ou vazia em {arquivo}.")


def decidir(
    state: Any,
    questions: dict[str, Any],
    chave: str,
    abrir: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """Envia um pedido de decisão ao Jev e devolve a resposta já desserializada.

    `abrir` existe para teste: por padrão usa `urlopen`.
    """
    abrir = urlopen if abrir is None else abrir

    corpo = json.dumps(
        {"model": MODELO, "state": state, "questions": questions},
        ensure_ascii=False,
    ).encode("utf-8")

    requisicao = Request(  # noqa: S310
        ENDPOINT,
        data=corpo,
        method="POST",
        headers={
            "Authorization": f"Bearer {chave}",
            "Content-Type": "application/json",
        },
    )

    try:
        with abrir(requisicao, timeout=TIMEOUT_SEGUNDOS) as resposta:  # noqa: S310
            dados: dict[str, Any] = json.loads(resposta.read().decode("utf-8"))
            return dados
    except urllib.error.HTTPError as erro:
        detalhe = erro.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Decisions API devolveu HTTP {erro.code}: {detalhe}") from erro
