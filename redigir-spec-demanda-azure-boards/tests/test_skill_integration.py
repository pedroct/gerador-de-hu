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
    # Os marcadores são o texto do passo, não seu número: inserir um passo não é uma regressão.
    marcadores = (
        "Receba o ID numérico",
        "Destino e credencial seguem a precedência",
        "Registre a fonte",
        "Converta cada valor",
        "Antes de investigar",
        "Preencha e salve a Spec-base",
        "Chame `especificar-debitos-tecnicos`",
        "Chame `especificar-telas-ux-ui`",
        "Somente se houver copy",
        "Salve a Spec principal",
    )
    posicoes = [SKILL.index(marcador) for marcador in marcadores]
    assert posicoes == sorted(posicoes)

    fluxo = SKILL[SKILL.index("## Fluxo obrigatório") : SKILL.index("## Limites de leitura")]
    numeros = [int(numero) for numero in re.findall(r"^(\d+)\. ", fluxo, flags=re.MULTILINE)]
    assert numeros == list(range(1, len(numeros) + 1)), "a numeração do fluxo tem furo"

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


def test_skill_documenta_configuracao_sem_expor_credencial() -> None:
    """Sem isso a CLI falha em `Erro [configuração]` e o agente não tem como se recuperar."""
    for texto in (
        "AZURE_DEVOPS_ORGANIZACAO",
        "AZURE_DEVOPS_PROJETO",
        "AZURE_DEVOPS_TOKEN",
        "--organizacao",
        "--projeto",
        "--config",
        "--env-file",
    ):
        assert texto in SKILL
    assert "Nunca a passe por argumento" in SKILL
    # Um argumento de credencial na CLI colocaria o segredo no comando registrado.
    assert "--token" not in SKILL


def template() -> str:
    inicio = SKILL.index("```markdown")
    return SKILL[inicio : SKILL.index("```", inicio + len("```markdown"))]


def test_template_nao_carrega_instrucoes_ao_agente() -> None:
    """Copiado literalmente, o template não deve despejar meta-instrução na Spec entregue."""
    corpo = template()
    for instrucao in (
        "não são requisito confirmado",
        "não devem ser promovidos",
        "alimentam os atores",
        "são os insumos desta seção",
    ):
        assert instrucao not in corpo
    assert "- Registrado na Demanda: ..." in corpo
    # A orientação continua existindo, só que fora do bloco a ser copiado.
    assert "## Como preencher o template" in SKILL
    assert "não são requisito confirmado" in SKILL


def test_skill_manda_normalizar_valor_que_quebraria_a_tabela() -> None:
    """Campos `html` do Boards podem conter marcação, `|` ou quebra de linha."""
    for texto in ("HTML", "quebras de linha", "\\|", "fora da tabela"):
        assert texto in SKILL


def test_skill_nomeia_os_campos_html_confirmados_no_tipo_remoto() -> None:
    """Confirmado por consulta real: estes três são declarados `html`, os outros são `string`."""
    secao = SKILL[SKILL.index("## Normalização dos valores registrados") :]
    for campo in (
        "Custom.DemandaValorEsperado",
        "Custom.DemandaDoraResolver",
        "Custom.DemandaRegraseRestricoes",
    ):
        assert re.search(rf"`{re.escape(campo)}` \| `html`", secao)
    assert "não precisam de conversão" in secao


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


_NUMEROS_POR_EXTENSO = {
    8: "oito",
    9: "nove",
    10: "dez",
    11: "onze",
    12: "doze",
}


def test_readme_conta_capacidades_de_acordo_com_a_propria_lista() -> None:
    """A contagem e a lista divergiram antes; uma checagem de substring não pegaria isso."""
    capacidades = re.findall(r"^- \*\*(.+?):\*\*", README, flags=re.MULTILINE)
    declarado = re.search(r"O fluxo combina (\w+) capacidades", README)
    assert declarado is not None
    assert declarado.group(1) == _NUMEROS_POR_EXTENSO[len(capacidades)]
    assert any("Demanda no Azure Boards" in capacidade for capacidade in capacidades)
