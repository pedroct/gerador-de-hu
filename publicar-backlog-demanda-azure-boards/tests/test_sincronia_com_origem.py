"""Garante que os módulos de cópia literal não divirjam da skill de origem."""

from pathlib import Path

import pytest

MODULOS_ESPELHADOS: tuple[str, ...] = (
    "contrato_backlog.py",
    "converter_para_html.py",
    "interpretar_markdown.py",
    "validacao_estrutural.py",
)

_RAIZ_SKILL = Path(__file__).resolve().parents[1]
_PACOTE_LOCAL = _RAIZ_SKILL / "src" / "publicar_backlog_demanda_azure_boards"
_PACOTE_ORIGEM = (
    _RAIZ_SKILL.parent / "publicar-backlog-azure-boards" / "src" / "publicar_backlog_azure_boards"
)


@pytest.mark.parametrize("modulo", MODULOS_ESPELHADOS)
def test_modulo_espelhado_e_identico_ao_da_origem(modulo: str) -> None:
    if not _PACOTE_ORIGEM.is_dir():
        pytest.skip(
            "A skill publicar-backlog-azure-boards não está presente; "
            "a comparação de sincronia não se aplica."
        )
    local = _PACOTE_LOCAL / modulo
    origem = _PACOTE_ORIGEM / modulo
    assert origem.is_file(), f"{modulo} não existe na skill de origem."
    esperado = origem.read_text(encoding="utf-8").replace(
        "publicar_backlog_azure_boards", "publicar_backlog_demanda_azure_boards"
    )
    assert local.read_text(encoding="utf-8") == esperado, (
        f"{modulo} divergiu da skill de origem. Ressincronize os dois lados antes de prosseguir."
    )


def test_modulos_espelhados_existem_no_pacote_local() -> None:
    ausentes = [modulo for modulo in MODULOS_ESPELHADOS if not (_PACOTE_LOCAL / modulo).is_file()]
    assert not ausentes, f"Módulos espelhados ausentes no pacote local: {ausentes}"
