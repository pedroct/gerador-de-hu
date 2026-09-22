from pathlib import Path


RAIZ_SKILL = Path(__file__).resolve().parents[1]
SKILL = (RAIZ_SKILL / "SKILL.md").read_text(encoding="utf-8")
REFERENCIA = (
    RAIZ_SKILL / "references" / "investigacao-demanda-azure-boards.md"
).read_text(encoding="utf-8")
RAIZ_PROJETO = RAIZ_SKILL.parent
README = (RAIZ_PROJETO / "README.md").read_text(encoding="utf-8")
PYPROJECT = (RAIZ_PROJETO / "pyproject.toml").read_text(encoding="utf-8")


def test_skill_exige_tipo_campos_e_leitura_sem_escrita() -> None:
    for texto in (
        "Demanda de Negócio",
        "System.Title",
        "Custom.DemandaAreaSolicitante",
        "Custom.DemandaPublicoAlvo",
        "Custom.DemandaValorEsperado",
        "Custom.DemandaDoraResolver",
        "Custom.DemandaRegraseRestricoes",
        "consultar_demanda.py",
        "GET",
    ):
        assert texto in SKILL
    for verbo in ("POST", "PATCH", "PUT", "DELETE"):
        assert f"não execute {verbo}" in SKILL


def test_orquestracao_preserva_limites_das_skills_chamadas() -> None:
    for skill in (
        "especificar-debitos-tecnicos",
        "especificar-telas-ux-ui",
        "revisar-textos-requisitos",
    ):
        assert skill in SKILL
    assert "não aceita uma sugestão" in SKILL
    assert "documento separado" in SKILL
    assert "não chamar entrevista, geração ou publicação de backlog" in SKILL


def test_template_preserva_rastreabilidade_e_lacunas() -> None:
    for secao in (
        "Fonte da Demanda",
        "Escopo",
        "Repositórios considerados",
        "Problema relatado",
        "Comportamento atual (evidência no código)",
        "Comportamento esperado",
        "Classificação",
        "Atores e vocabulário identificados no código",
        "Lacunas e perguntas abertas",
    ):
        assert secao in SKILL
    assert "null" in SKILL
    assert "EXPLICITO" in SKILL
    assert "INFERIDO" in SKILL


def test_referencia_delimita_investigacao_somente_leitura() -> None:
    for texto in (
        "rg",
        "find",
        "git status",
        "caminho:linha",
        "Registrado na Demanda",
        "Evidenciado pelo código",
        "Lacuna",
        "síntese GEPRO",
    ):
        assert texto in REFERENCIA
    for acao in ("aplicação", "teste", "build", "migração"):
        assert f"Não execute {acao}" in REFERENCIA


def test_projeto_documenta_a_skill_e_a_inclui_na_suite() -> None:
    for texto in (
        "redigir-spec-demanda-azure-boards",
        "ID de uma Demanda de Negócio já criada no Azure Boards",
        "Custom.DemandaAreaSolicitante",
        "Custom.DemandaPublicoAlvo",
        "Custom.DemandaValorEsperado",
        "Custom.DemandaDoraResolver",
        "Custom.DemandaRegraseRestricoes",
    ):
        assert texto in README
    assert "redigir-spec-demanda-azure-boards/tests" in PYPROJECT
