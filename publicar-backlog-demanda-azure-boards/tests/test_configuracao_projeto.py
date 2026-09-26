import tomllib
from io import StringIO
from pathlib import Path

import pytest

from publicar_backlog_demanda_azure_boards import main
from publicar_backlog_demanda_azure_boards.cli import construir_parser
from publicar_backlog_demanda_azure_boards.configuracao import (
    ConfiguracaoAzureDevOps,
    carregar_configuracao,
)
from publicar_backlog_demanda_azure_boards.modelos import Demanda

CAMINHO_PYPROJECT = Path(__file__).parents[1] / "pyproject.toml"


def test_projeto_exige_python_312_ou_superior() -> None:
    texto = CAMINHO_PYPROJECT.read_text()
    assert 'requires-python = ">=3.12"' in texto


def test_projeto_declara_comando_em_portugues() -> None:
    dados = tomllib.loads(CAMINHO_PYPROJECT.read_text())
    assert "publicar-backlog-demanda-azure-boards" in dados["project"]["scripts"]


def test_entry_point_instalado_chama_cli_real(monkeypatch, capsys) -> None:
    backlog = Path(__file__).parent / "fixtures" / "valid-backlog.md"
    monkeypatch.setattr(
        "sys.argv", ["publicar-backlog-demanda-azure-boards", "validar", str(backlog)]
    )

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
            "AZURE_DEVOPS_DEMANDA": "13959",
        },
        entrada=StringIO(),
        saida=StringIO(),
    )

    assert configuracao.obter_token() == "token-seguro"
    assert chamadas == ["Credencial do Azure DevOps: "]


def test_destino_herda_os_caminhos_da_demanda() -> None:
    configuracao = carregar_configuracao(
        argumentos={
            "organizacao": "contoso",
            "projeto": "CESOP-DILIGENCIA",
            "demanda_id": "13959",
        },
        caminho_env=Path("arquivo-inexistente.env"),
        ambiente={},
        exigir_token=False,
    )
    demanda = Demanda(
        id=13959,
        titulo="PADRONIZAÇÃO",
        area_path="CESOP-DILIGENCIA\\Sustentacao",
        iteration_path="CESOP-DILIGENCIA\\Sprint 18",
        url="https://dev.azure.com/contoso/_apis/wit/workItems/13959",
    )

    destino = configuracao.publicacao_para(demanda)

    assert destino.area_path == "CESOP-DILIGENCIA\\Sustentacao"
    assert destino.iteration_path == "CESOP-DILIGENCIA\\Sprint 18"
    assert destino.demanda_id == 13959


def test_configuracao_nao_aceita_mais_caminhos_manuais() -> None:
    assert "area_path" not in ConfiguracaoAzureDevOps.model_fields
    assert "iteration_path" not in ConfiguracaoAzureDevOps.model_fields


def test_a_cli_aceita_a_demanda() -> None:
    argumentos = construir_parser().parse_args(["planejar", "backlog.md", "--demanda", "13959"])
    assert argumentos.demanda_id == "13959"


def test_a_cli_nao_oferece_mais_os_caminhos_manuais() -> None:
    """A ajuda de topo não lista flags de subcomando; o teste precisa parseá-las.

    Afirmar sobre `construir_parser().format_help()` passaria vazio mesmo com os
    argumentos ainda existindo, porque eles vivem nos subparsers.
    """
    for caminho_manual in ("--area-path", "--iteration-path"):
        with pytest.raises(SystemExit):
            construir_parser().parse_args(["planejar", "backlog.md", caminho_manual, "Projeto"])


@pytest.mark.parametrize(
    ("bruto", "trecho"),
    [
        ("0", "inteiro positivo"),
        ("-5", "inteiro positivo"),
        ("abc", "número inteiro"),
        ("1_3", "número inteiro"),
        ("١٣", "número inteiro"),
        ("13.0", "número inteiro"),
        # Valor vazio é "não informado" em toda a camada de configuração, como para
        # organização e projeto: cai na pergunta interativa, que aqui não tem resposta.
        ("", "entrada interativa"),
    ],
)
def test_id_de_demanda_invalido_nomeia_o_problema(bruto: str, trecho: str) -> None:
    """Colar `1_3` ou dígitos de outro locale publicaria sob outro work item."""
    from publicar_backlog_demanda_azure_boards.configuracao import ErroConfiguracao

    with pytest.raises(ErroConfiguracao) as erro:
        carregar_configuracao(
            argumentos={
                "organizacao": "contoso",
                "projeto": "CESOP-DILIGENCIA",
                "demanda_id": bruto,
            },
            caminho_env=Path("arquivo-inexistente.env"),
            ambiente={},
            entrada=StringIO(),
            saida=StringIO(),
            exigir_token=False,
        )

    assert trecho in str(erro.value)
