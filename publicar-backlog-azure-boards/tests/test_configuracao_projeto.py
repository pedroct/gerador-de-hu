import tomllib
from pathlib import Path

CAMINHO_PYPROJECT = Path(__file__).parents[1] / "pyproject.toml"


def test_projeto_exige_python_312_ou_superior() -> None:
    texto = CAMINHO_PYPROJECT.read_text()
    assert 'requires-python = ">=3.12"' in texto


def test_projeto_declara_comando_em_portugues() -> None:
    dados = tomllib.loads(CAMINHO_PYPROJECT.read_text())
    assert "publicar-backlog-azure-boards" in dados["project"]["scripts"]
