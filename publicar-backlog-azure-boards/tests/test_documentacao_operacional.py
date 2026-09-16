from pathlib import Path

RAIZ = Path(__file__).parents[1]


def test_documentacao_descreve_bloqueios_de_seguranca() -> None:
    texto = (RAIZ / "README.md").read_text(encoding="utf-8")

    assert "reconciliação" in texto
    assert "sem eco" in texto
    assert "MCP" in texto and "opcional" in texto
