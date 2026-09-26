"""Confere o `demanda_id` configurado contra a Demanda de Negócio declarada no backlog.

`extrair_demanda_origem` e `conferir_demanda_de_origem` vivem em `executar_publicacao.py`,
não em `interpretar_markdown.py`: este último é espelhado byte a byte no pacote
`publicar-backlog-azure-boards` (ver `test_sincronia_com_origem.py`), e a publicadora solta
não pode ganhar esta recusa — ela publica de propósito sem vínculo com uma Demanda quando o
backlog de débitos técnicos declara a origem só para rastreabilidade. `executar_publicacao.py`
não é um módulo espelhado, então é onde a assimetria pode viver sem quebrar a sincronia.
"""

from pathlib import Path

import pytest

from publicar_backlog_demanda_azure_boards.executar_publicacao import (
    conferir_demanda_de_origem,
    extrair_demanda_origem,
)
from publicar_backlog_demanda_azure_boards.interpretar_markdown import ErroContratoMarkdown

CABECALHO = (
    "# Backlog para Azure Boards\n\n## Metadados e cobertura\n- Data de geração: `2026-09-25`\n"
)


def test_le_o_id_da_demanda_de_origem(tmp_path: Path) -> None:
    caminho = tmp_path / "backlog.md"
    caminho.write_text(CABECALHO + "- Demanda de Negócio de origem: `#14125`\n", encoding="utf-8")

    assert extrair_demanda_origem(caminho) == 14125


def test_devolve_none_quando_o_backlog_declara_nao_se_aplica(tmp_path: Path) -> None:
    caminho = tmp_path / "backlog.md"
    caminho.write_text(
        CABECALHO
        + "- Demanda de Negócio de origem: Não se aplica — a spec não nasceu de uma Demanda\n",
        encoding="utf-8",
    )

    assert extrair_demanda_origem(caminho) is None


def test_rejeita_metadado_ausente(tmp_path: Path) -> None:
    caminho = tmp_path / "backlog.md"
    caminho.write_text(CABECALHO, encoding="utf-8")

    with pytest.raises(ErroContratoMarkdown, match="Demanda de Negócio de origem"):
        extrair_demanda_origem(caminho)


def backlog_com_demanda(tmp_path: Path, linha: str) -> Path:
    caminho = tmp_path / "backlog.md"
    caminho.write_text(CABECALHO + linha, encoding="utf-8")
    return caminho


def test_recusa_quando_o_id_informado_diverge_do_backlog(tmp_path: Path) -> None:
    caminho = backlog_com_demanda(tmp_path, "- Demanda de Negócio de origem: `#14125`\n")

    with pytest.raises(ValueError, match="#14125.*#99999"):
        conferir_demanda_de_origem(caminho, demanda_id=99999)


def test_recusa_backlog_que_nao_nasceu_de_demanda(tmp_path: Path) -> None:
    caminho = backlog_com_demanda(
        tmp_path,
        "- Demanda de Negócio de origem: Não se aplica — a spec não nasceu de uma Demanda\n",
    )

    with pytest.raises(ValueError, match="Não se aplica"):
        conferir_demanda_de_origem(caminho, demanda_id=14125)


def test_aceita_quando_o_id_confere(tmp_path: Path) -> None:
    caminho = backlog_com_demanda(tmp_path, "- Demanda de Negócio de origem: `#14125`\n")

    conferir_demanda_de_origem(caminho, demanda_id=14125)
