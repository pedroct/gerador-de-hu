import tomllib
from pathlib import Path

import pytest

from publicar_backlog_azure_boards import main

CAMINHO_PYPROJECT = Path(__file__).parents[1] / "pyproject.toml"


def test_projeto_exige_python_312_ou_superior() -> None:
    texto = CAMINHO_PYPROJECT.read_text()
    assert 'requires-python = ">=3.12"' in texto


def test_projeto_declara_comando_em_portugues() -> None:
    dados = tomllib.loads(CAMINHO_PYPROJECT.read_text())
    assert "publicar-backlog-azure-boards" in dados["project"]["scripts"]


def test_comando_placeholder_encerra_controladamente(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as erro:
        main()

    assert erro.value.code == 1
    assert capsys.readouterr().err == (
        "O executor do publicador ainda não foi implementado; "
        "tente novamente após a conclusão das próximas tarefas.\n"
    )
