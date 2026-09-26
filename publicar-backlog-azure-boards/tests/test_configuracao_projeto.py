import tomllib
from io import StringIO
from pathlib import Path

from publicar_backlog_azure_boards import main
from publicar_backlog_azure_boards.configuracao import carregar_configuracao

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
    assert "Backlog válido: 4 itens." in capsys.readouterr().out


def test_token_interativo_usa_getpass_do_modulo(monkeypatch) -> None:
    chamadas: list[str] = []

    def ler_sem_eco(prompt: str) -> str:
        chamadas.append(prompt)
        return "token-seguro"

    monkeypatch.setattr("getpass.getpass", ler_sem_eco)

    configuracao = carregar_configuracao(
        ambiente={
            "AZURE_DEVOPS_ORGANIZACAO": "organizacao",
            "AZURE_DEVOPS_PROJETO": "Projeto",
            "AZURE_DEVOPS_AREA_PATH": "Projeto",
            "AZURE_DEVOPS_ITERATION_PATH": r"Projeto\Sprint 18",
        },
        entrada=StringIO(),
        saida=StringIO(),
    )

    assert configuracao.obter_token() == "token-seguro"
    assert chamadas == ["Credencial do Azure DevOps: "]
