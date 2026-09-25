import re
import sys
from pathlib import Path

RAIZ_SKILL = Path(__file__).resolve().parents[1]
SKILL = (RAIZ_SKILL / "SKILL.md").read_text(encoding="utf-8")
REFERENCIA = (RAIZ_SKILL / "references" / "investigacao-demanda-azure-boards.md").read_text(
    encoding="utf-8"
)
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
        "Crie a pasta da Demanda",
        "Chame `especificar-debitos-tecnicos`",
        "Chame `especificar-telas-ux-ui`",
        "Somente se houver copy",
        "Confirme que a pasta da Demanda",
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
    assert "classificada por audiência conforme **Audiência das lacunas**" in SKILL


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


def sem_quebras(texto: str) -> str:
    """Normaliza o reflow do Markdown para a asserção não quebrar ao reformatar o parágrafo."""
    return " ".join(texto.split())


def test_lacuna_tem_id_audiencia_e_evidencia() -> None:
    corpo = template()
    assert "- **N1 · Negócio** —" in corpo
    assert "- **T1 · Técnico** —" in corpo
    assert "<!-- evidência:" in corpo


def test_criterio_de_audiencia_e_checavel() -> None:
    secao = sem_quebras(SKILL[SKILL.index("## Audiência das lacunas") :])
    assert "muda o que o usuário percebe" in secao
    assert "uma lacuna, uma decisão, uma audiência" in secao.lower()


def test_regra_de_traducao_proibe_codigo_na_pergunta() -> None:
    secao = sem_quebras(SKILL[SKILL.index("## Audiência das lacunas") :])
    assert "verificar_lacunas.py" in secao
    for proibido in ("arquivo", "classe", "método", "número de linha"):
        assert proibido in secao


def test_lacunas_do_template_nao_violam_o_proprio_verificador() -> None:
    """O exemplo do template não pode ser o primeiro a quebrar a regra que ensina."""
    sys.path.insert(0, str(RAIZ_SKILL / "scripts"))
    from verificar_lacunas import extrair_lacunas, verificar

    # Sem esta contagem, o teste passaria vazio caso o template deixasse de casar com o extrator.
    assert len(extrair_lacunas(template())) == 2
    assert verificar(template()) == []


def test_skill_delega_a_conversao_de_html_ao_leitor() -> None:
    """A CLI converte pelo tipo declarado; a skill não deve reconverter nem presumir campos."""
    secao = sem_quebras(SKILL[SKILL.index("## Valores já convertidos pelo leitor") :])
    for exigencia in (
        "Não converta HTML você mesmo",
        "Não presuma quais campos são `html`",
        "é conteúdo literal que o autor digitou",
        # A responsabilidade que sobra para o agente é só a tabela.
        "escape `|` como `\\|`",
    ):
        assert exigencia in secao


def test_leitor_nao_grava_a_lista_de_campos_html_no_codigo() -> None:
    """Fixar os campos no código gravaria a configuração atual do Boards e quebraria em silêncio."""
    fonte = (RAIZ_SKILL / "scripts" / "consultar_demanda.py").read_text(encoding="utf-8")
    assert "CAMPOS_HTML" not in fonte
    for campo in (
        "Custom.DemandaValorEsperado",
        "Custom.DemandaDoraResolver",
        "Custom.DemandaRegraseRestricoes",
    ):
        # Os campos aparecem só em CAMPOS_DEMANDA, nunca numa lista de "estes são html".
        assert fonte.count(f'"{campo}"') == 1
    assert "_apis/wit/fields?api-version" in fonte


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


def test_skill_define_a_pasta_da_demanda_e_o_vocabulario_fechado() -> None:
    for texto in (
        "DN-<id>-<slug>",
        "docs/specs/",
        "spec.md",
        "debitos-tecnicos.md",
        "telas-ux-ui.md",
        "revisao-textos.md",
    ):
        assert texto in SKILL


def test_pasta_existente_e_reaproveitada() -> None:
    """Regerar a mesma Demanda não pode criar uma segunda pasta nem abortar."""
    secao = sem_quebras(SKILL[SKILL.index("## Pasta da Demanda") :])
    assert "reaproveite a pasta existente" in secao
    assert "nunca crie uma segunda pasta" in secao


def test_slug_degenerado_nao_produz_nome_quebrado() -> None:
    """Título só com pontuação ou acentos não pode gerar `DN-14125-` nem hífen final."""
    secao = sem_quebras(SKILL[SKILL.index("## Pasta da Demanda") :])
    assert "sem hífen inicial nem final" in secao
    assert "use apenas `DN-<id>`" in secao


def test_skill_informa_o_caminho_usado() -> None:
    assert "informe ao usuário o caminho" in sem_quebras(SKILL)


def test_pasta_inclui_negocio_md() -> None:
    assert "negocio.md" in SKILL


def test_negocio_md_nao_carrega_evidencia_de_codigo() -> None:
    secao = sem_quebras(SKILL[SKILL.index("## Template de negocio.md") :])
    assert "nunca entra em `negocio.md`" in secao
    assert "fato observado" in secao


def test_negocio_md_e_gerado_mesmo_sem_lacuna_de_negocio() -> None:
    """Sem o documento, a reunião de negócio fica sem pauta e ninguém percebe."""
    secao = sem_quebras(SKILL[SKILL.index("## Template de negocio.md") :])
    assert "gere `negocio.md` mesmo assim" in secao


def test_handoff_nomeia_as_duas_rodadas_sem_encadear() -> None:
    fluxo = SKILL[SKILL.index("## Fluxo obrigatório") : SKILL.index("## Pasta da Demanda")]
    assert "entrevistar-lacunas-requisito" in fluxo
    assert "escopo `negócio`" in fluxo
    assert "escopo `técnico`" in fluxo
    assert "não chamar entrevista, geração ou publicação de backlog" in fluxo


def test_passo_10_roda_o_verificador_com_raiz_e_caminho_explicitos() -> None:
    """Sem a raiz da skill e sem o caminho, o comando do passo 10 sai com código 2."""
    passo = sem_quebras(SKILL[SKILL.index("10. Confirme") : SKILL.index("## Pasta da Demanda")])
    assert "a partir da raiz desta skill" in passo
    assert "scripts/verificar_lacunas.py <caminho completo de spec.md>" in passo


def test_negocio_md_e_descartavel_e_sempre_regerado() -> None:
    """Uma cópia de rodada anterior lista decisões já tomadas e uma contagem técnica vencida."""
    secao = sem_quebras(SKILL[SKILL.index("## Template de negocio.md") :])
    assert "descartável e sempre regerado a partir de `spec.md`" in secao
    assert "Uma cópia desatualizada nunca é fonte" in secao


def test_prosa_do_negocio_md_cita_o_cabecalho_real_do_template() -> None:
    """`## Comportamento atual` sem o sufixo não existe no template que a prosa manda consultar."""
    secao = sem_quebras(SKILL[SKILL.index("## Template de negocio.md") :])
    assert "`## Comportamento atual (evidência no código)`" in secao
