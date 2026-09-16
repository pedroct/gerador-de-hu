import tomllib
from pathlib import Path

from publicar_backlog_azure_boards import main

CAMINHO_PYPROJECT = Path(__file__).parents[1] / "pyproject.toml"


def test_projeto_exige_python_312_ou_superior() -> None:
    texto = CAMINHO_PYPROJECT.read_text()
    assert 'requires-python = ">=3.12"' in texto


def test_projeto_declara_comando_em_portugues() -> None:
    dados = tomllib.loads(CAMINHO_PYPROJECT.read_text())
    assert "publicar-backlog-azure-boards" in dados["project"]["scripts"]


def test_entry_point_instalado_chama_cli_real(monkeypatch, capsys) -> None:
    backlog = Path(__file__).parent / "fixtures" / "valid-backlog.md"
    monkeypatch.setattr("sys.argv", ["publicar-backlog-azure-boards", "validar", str(backlog)])

    codigo = main()

    assert codigo == 0
    assert "Backlog válido: 3 itens." in capsys.readouterr().out
