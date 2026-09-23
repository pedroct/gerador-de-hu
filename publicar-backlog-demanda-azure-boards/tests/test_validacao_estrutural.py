from __future__ import annotations

import importlib
from pathlib import Path

import pytest

import publicar_backlog_demanda_azure_boards.validacao_estrutural as modulo_validacao
from publicar_backlog_demanda_azure_boards.contrato_backlog import parse_backlog
from publicar_backlog_demanda_azure_boards.interpretar_markdown import interpretar_backlog
from publicar_backlog_demanda_azure_boards.validacao_estrutural import (
    ErroValidacaoEstrutural,
    validar_estrutura_backlog,
)

FIXTURE_VALIDO = Path(__file__).parent / "fixtures" / "valid-backlog.md"


def escrever_fixture_invalida(tmp_path: Path, texto: str) -> Path:
    caminho = tmp_path / "backlog-invalido.md"
    caminho.write_text(texto, encoding="utf-8")
    return caminho


def test_valida_fixture_completo_do_contrato() -> None:
    validar_estrutura_backlog(FIXTURE_VALIDO)


def test_rejeita_origem_ausente_mesmo_sem_refinement_status(tmp_path: Path) -> None:
    caminho = escrever_fixture_invalida(
        tmp_path,
        "# Backlog para Azure Boards\n\n## 1.0.0 [Epic] Épico\n\n### Description\ntexto",
    )

    with pytest.raises(ErroValidacaoEstrutural, match="não possui Origem na spec"):
        validar_estrutura_backlog(caminho)


def test_rejeita_campo_de_refinement_status_ausente(tmp_path: Path) -> None:
    caminho = escrever_fixture_invalida(
        tmp_path,
        "# Backlog para Azure Boards\n"
        "\n## 1.0.0 [Epic] Épico\n"
        "### Description\nOrigem na spec: seção 1.\n"
        "### 1.1.0 [Feature] Feature\n"
        "#### Parent\n`1.0.0`\n"
        "#### Description\nOrigem na spec: seção 1.1.\n"
        "#### 1.1.1 [User Story] História\n"
        "##### Parent\n`1.1.0`\n"
        "##### Description\n"
        "###### Card\nCard confirmado.\n"
        "###### Conversation\nConversation confirmada.\n"
        "Origem na spec: seção 1.1.1.\n"
        "##### Acceptance Criteria\n```gherkin\nCenário: válido\n```\n"
        "##### Refinement Status\n"
        "- Conversation: suficiente\n"
        "- Confirmation: Completa\n"
        "- Prontidão: Pronta\n",
    )

    with pytest.raises(ErroValidacaoEstrutural, match="campo de refinamento Card"):
        validar_estrutura_backlog(caminho)


def test_rejeita_heading_de_item_fora_do_contrato(tmp_path: Path) -> None:
    caminho = escrever_fixture_invalida(
        tmp_path,
        "# Backlog para Azure Boards\n\n## 123 [Epic] Épico inválido\n",
    )

    with pytest.raises(ErroValidacaoEstrutural, match="título de item de trabalho inválido"):
        validar_estrutura_backlog(caminho)


def test_validador_empacotado_nao_acessa_diretorio_irmao(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    modulo = importlib.reload(modulo_validacao)
    monkeypatch.setattr(Path, "is_file", lambda self: False)

    modulo.validar_estrutura_backlog(FIXTURE_VALIDO)


def test_contrato_e_interpretador_concordam_sobre_implementation_evidence(
    tmp_path: Path,
) -> None:
    """Guarda de deriva: os dois parsers do contrato devem separar a mesma fronteira
    entre Description e um heading `Implementation Evidence *(sufixo)*` seguinte."""
    texto = (
        "# Backlog para Azure Boards\n"
        "\n## 1.0.0 [Epic] Épico\n"
        "### Description\n"
        "Texto real da descrição. Origem na spec: seção 1.\n"
        "### Implementation Evidence *(sufixo)*\n"
        "Texto que não deveria vazar para a Description de nenhum dos dois parsers.\n"
    )
    caminho = escrever_fixture_invalida(tmp_path, texto)

    descricao_contrato = parse_backlog(texto)[0].section("Description")
    descricao_interpretada = interpretar_backlog(caminho)[0].descricao

    assert descricao_contrato == descricao_interpretada
    assert "Implementation Evidence" not in descricao_contrato
    assert "não deveria vazar" not in descricao_contrato
