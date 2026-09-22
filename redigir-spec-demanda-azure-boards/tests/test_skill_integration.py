import re
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


def test_fluxo_estatico_preserva_ordem_gatilhos_e_lacunas() -> None:
    marcadores = (
        "1. Receba o ID numérico",
        "2. Registre a fonte",
        "3. Converta cada valor",
        "4. Antes de investigar",
        "5. Preencha e salve a Spec-base",
        "6. Chame `especificar-debitos-tecnicos`",
        "7. Chame `especificar-telas-ux-ui`",
        "8. Somente se houver copy",
        "9. Salve a Spec principal",
    )
    posicoes = [SKILL.index(marcador) for marcador in marcadores]
    assert posicoes == sorted(posicoes)

    assert re.search(
        r"somente quando houver evidência de débito técnico ligada ao\s+escopo",
        SKILL,
    )
    assert "sempre depois de concluir a Spec-base completa" in SKILL
    assert "Somente se houver copy exibida ao usuário" in SKILL
    assert SKILL.index("depois da análise de telas") > SKILL.index("Somente se houver copy")

    assert re.search(
        r"Converta cada valor `null`, vazio ou lista vazia.*?Lacunas e perguntas abertas",
        SKILL,
        flags=re.DOTALL,
    )
    assert "pergunta objetiva para cada campo null" in SKILL


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
