from pathlib import Path

import pytest

RAIZ = Path(__file__).parents[1]
DOCUMENTOS = ("README.md", "SKILL.md")


def test_documentacao_descreve_bloqueios_de_seguranca() -> None:
    texto = (RAIZ / "README.md").read_text(encoding="utf-8")

    assert "reconciliação" in texto
    assert "sem eco" in texto
    assert "MCP" in texto and "opcional" in texto


@pytest.mark.parametrize("documento", DOCUMENTOS)
def test_documentacao_nao_oferece_caminhos_manuais(documento: str) -> None:
    """Os caminhos vêm da Demanda; oferecê-los na documentação seria mentira."""
    texto = (RAIZ / documento).read_text(encoding="utf-8")

    assert "--area-path" not in texto
    assert "--iteration-path" not in texto
    assert "AZURE_DEVOPS_AREA_PATH" not in texto
    assert "AZURE_DEVOPS_ITERATION_PATH" not in texto


@pytest.mark.parametrize("documento", DOCUMENTOS)
def test_documentacao_exige_a_demanda_nos_comandos(documento: str) -> None:
    texto = (RAIZ / documento).read_text(encoding="utf-8")

    assert "--demanda" in texto
    assert "AZURE_DEVOPS_DEMANDA" in texto


@pytest.mark.parametrize("documento", DOCUMENTOS)
def test_documentacao_registra_os_limites_proprios_desta_skill(documento: str) -> None:
    """Os três limites que distinguem esta skill da de origem."""
    texto = (RAIZ / documento).read_text(encoding="utf-8")

    assert "nunca é escrita" in texto
    assert "herdado" in texto or "herda" in texto
    assert "--simulacao" in texto and "token" in texto


def test_skill_md_declara_o_nome_e_o_gatilho_corretos() -> None:
    texto = (RAIZ / "SKILL.md").read_text(encoding="utf-8")

    assert "name: publicar-backlog-demanda-azure-boards" in texto
    assert "Demanda de Negócio" in texto.split("---")[1]


def test_agents_yaml_descreve_esta_skill() -> None:
    texto = (RAIZ / "agents" / "openai.yaml").read_text(encoding="utf-8")

    assert "publicar-backlog-demanda-azure-boards" in texto
    assert "Demanda" in texto
