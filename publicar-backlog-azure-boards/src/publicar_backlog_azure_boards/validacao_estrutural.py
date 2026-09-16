"""Integra o validador estrutural mantido pela skill geradora de backlog."""

from __future__ import annotations

import importlib.util
import sys
from collections.abc import Callable
from functools import lru_cache
from pathlib import Path
from types import ModuleType
from typing import cast


class ErroValidacaoEstrutural(ValueError):
    """Indica que o contrato compartilhado rejeitou o backlog."""


@lru_cache(maxsize=1)
def _carregar_validador() -> Callable[[str, bool], list[str]]:
    raiz = Path(__file__).resolve().parents[3]
    caminho = raiz / "gerar-backlog-azure-boards" / "scripts" / "validate_backlog.py"
    if not caminho.is_file():
        raise RuntimeError(
            "O validador estrutural gerar-backlog-azure-boards/scripts/validate_backlog.py "
            "não foi encontrado."
        )
    especificacao = importlib.util.spec_from_file_location("_gerador_hu_validate_backlog", caminho)
    if especificacao is None or especificacao.loader is None:
        raise RuntimeError("Não foi possível carregar o validador estrutural do backlog.")
    modulo = importlib.util.module_from_spec(especificacao)
    sys.modules[especificacao.name] = modulo
    especificacao.loader.exec_module(modulo)
    return _obter_funcao_validacao(modulo)


def _obter_funcao_validacao(modulo: ModuleType) -> Callable[[str, bool], list[str]]:
    funcao = getattr(modulo, "validate_backlog", None)
    if not callable(funcao):
        raise RuntimeError("O validador estrutural não expõe validate_backlog.")
    return cast(Callable[[str, bool], list[str]], funcao)


def validar_estrutura_backlog(caminho: Path) -> None:
    """Executa o contrato compartilhado e agrega todos os erros antes do planejamento."""
    texto = caminho.read_text(encoding="utf-8")
    erros = _carregar_validador()(texto, False)
    if erros:
        detalhes = "\n".join(f"- {erro}" for erro in erros)
        raise ErroValidacaoEstrutural(f"O backlog falhou na validação estrutural:\n{detalhes}")
