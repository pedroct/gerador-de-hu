from dataclasses import replace

from publicar_backlog_demanda_azure_boards.modelos import (
    ConfiguracaoPublicacao,
    ItemBacklog,
    MapeamentoTipos,
    TipoItem,
)
from publicar_backlog_demanda_azure_boards.planejar_publicacao import criar_plano

CONFIGURACAO = ConfiguracaoPublicacao(
    organizacao="organizacao",
    projeto="projeto",
    area_path="projeto",
    iteration_path="projeto\\Sprint 18",
    demanda_id=13959,
)
DATA_GERACAO = "2026-09-16"
ITENS = [
    ItemBacklog("1.1.1", TipoItem.HISTORIA_USUARIO, "História", "1.1.0", "Descrição", ""),
    ItemBacklog("1.1.0", TipoItem.FEATURE, "Feature", "1.0.0", "Descrição", ""),
    ItemBacklog("1.0.0", TipoItem.EPIC, "Épico", None, "Descrição", ""),
]


def test_plano_ordena_epic_feature_e_folha() -> None:
    plano = criar_plano(ITENS, CONFIGURACAO, DATA_GERACAO)

    assert [operacao.chave for operacao in plano.operacoes] == ["1.0.0", "1.1.0", "1.1.1"]


def test_plano_preserva_backlog_completo_para_validar_retomada() -> None:
    plano = criar_plano(ITENS, CONFIGURACAO, DATA_GERACAO)

    assert tuple(operacao.chave for operacao in plano.operacoes) == (
        "1.0.0",
        "1.1.0",
        "1.1.1",
    )
    assert plano.configuracao == CONFIGURACAO


def test_plano_converte_apenas_campos_copiaveis_e_inclui_pai() -> None:
    plano = criar_plano(ITENS, CONFIGURACAO, DATA_GERACAO)
    historia = plano.operacoes[-1]

    assert historia.descricao == "<p>Descrição</p>\n"
    assert historia.criterios_aceitacao == ""
    assert historia.chave_pai == "1.1.0"
    assert historia.tipo_remoto == "User Story"


def test_operacao_usa_titulo_com_numeracao_hierarquica() -> None:
    plano = criar_plano(ITENS, CONFIGURACAO, DATA_GERACAO)
    historia = plano.operacoes[-1]

    assert historia.titulo == "01.01.01 História"


def test_operacao_usa_titulo_curto_quando_declarado() -> None:
    itens_com_titulo_curto = [
        ItemBacklog(
            "1.1.1",
            TipoItem.HISTORIA_USUARIO,
            "História completa e bem mais longa",
            "1.1.0",
            "Descrição",
            "",
            titulo_curto="História curta",
        ),
    ]

    plano = criar_plano(itens_com_titulo_curto, CONFIGURACAO, DATA_GERACAO)

    assert plano.operacoes[0].titulo == "01.01.01 História curta"


def test_hash_muda_quando_destino_muda() -> None:
    outro_destino = replace(CONFIGURACAO, projeto="outro-projeto")

    assert (
        criar_plano(ITENS, CONFIGURACAO, DATA_GERACAO).hash_plano
        != criar_plano(ITENS, outro_destino, DATA_GERACAO).hash_plano
    )


def test_hash_muda_quando_data_de_geracao_muda() -> None:
    assert (
        criar_plano(ITENS, CONFIGURACAO, DATA_GERACAO).hash_plano
        != criar_plano(ITENS, CONFIGURACAO, "2026-01-01").hash_plano
    )


def test_titulo_usa_numeracao_hierarquica_sem_data() -> None:
    itens = [
        ItemBacklog(
            chave="1.0.0",
            tipo=TipoItem.EPIC,
            titulo="Gestão do projeto",
            pai=None,
            descricao="",
            criterios_aceitacao="",
        ),
        ItemBacklog(
            chave="1.1.1",
            tipo=TipoItem.HISTORIA_USUARIO,
            titulo="Análise de padrões de stacks",
            pai="1.1.0",
            descricao="",
            criterios_aceitacao="",
        ),
    ]
    plano = criar_plano(itens, CONFIGURACAO, "2026-09-22")
    titulos = {operacao.chave: operacao.titulo for operacao in plano.operacoes}
    assert titulos["1.0.0"] == "01 Gestão do projeto"
    assert titulos["1.1.1"] == "01.01.01 Análise de padrões de stacks"
    assert all("2026-09-22" not in titulo for titulo in titulos.values())


def test_data_de_geracao_continua_no_hash() -> None:
    itens = [
        ItemBacklog(
            chave="1.0.0",
            tipo=TipoItem.EPIC,
            titulo="Gestão do projeto",
            pai=None,
            descricao="",
            criterios_aceitacao="",
        )
    ]
    primeiro = criar_plano(itens, CONFIGURACAO, "2026-09-22")
    segundo = criar_plano(itens, CONFIGURACAO, "2026-09-23")
    assert primeiro.hash_plano != segundo.hash_plano


def test_mapeamento_product_backlog_item_integra_operacao_e_hash() -> None:
    configuracao_pbi = replace(
        CONFIGURACAO,
        mapeamento_tipos=MapeamentoTipos(historia_usuario="Product Backlog Item"),
    )

    plano_padrao = criar_plano(ITENS, CONFIGURACAO, DATA_GERACAO)
    plano_pbi = criar_plano(ITENS, configuracao_pbi, DATA_GERACAO)

    assert plano_pbi.operacoes[-1].tipo_remoto == "Product Backlog Item"
    assert plano_pbi.hash_plano != plano_padrao.hash_plano


# Hash produzido pela versão anterior aos campos novos. Ele existe para que um backlog
# sem tags, sem dependências e sem ID declarado continue gerando o mesmo plano — é o que
# permite a toda publicação parcial já gravada retomar. Se este teste falhar, a assimetria
# do hash foi quebrada; não atualize o literal para "consertar".
HASH_ANTES_DOS_CAMPOS_NOVOS = "36d9bee8e7073aa1e2c2de786a316a373f38ad5ba83e23b3dd4b628dedf1af58"


def test_hash_nao_muda_para_backlog_sem_tags() -> None:
    plano = criar_plano(ITENS, CONFIGURACAO, DATA_GERACAO)

    assert plano.hash_plano == HASH_ANTES_DOS_CAMPOS_NOVOS


def test_operacao_propaga_tags_do_item() -> None:
    itens = [replace(ITENS[0], tags=("debito-tecnico",)), ITENS[1], ITENS[2]]

    plano = criar_plano(itens, CONFIGURACAO, DATA_GERACAO)

    assert plano.operacoes[-1].tags == ("debito-tecnico",)


def test_hash_muda_quando_ha_tags() -> None:
    com_tags = [replace(ITENS[0], tags=("debito-tecnico",)), ITENS[1], ITENS[2]]

    assert (
        criar_plano(com_tags, CONFIGURACAO, DATA_GERACAO).hash_plano
        != criar_plano(ITENS, CONFIGURACAO, DATA_GERACAO).hash_plano
    )


def test_predecessor_e_criado_antes_do_dependente_mesmo_com_chave_maior() -> None:
    funcional = ItemBacklog(
        "1.1.1",
        TipoItem.HISTORIA_USUARIO,
        "Funcional",
        "1.1.0",
        "Descrição",
        "",
        depende_de=("1.1.2",),
    )
    design = ItemBacklog("1.1.2", TipoItem.HISTORIA_USUARIO, "Design", "1.1.0", "Descrição", "")
    itens = [funcional, design, ITENS[1], ITENS[2]]

    plano = criar_plano(itens, CONFIGURACAO, DATA_GERACAO)

    chaves = [operacao.chave for operacao in plano.operacoes]
    assert chaves.index("1.1.2") < chaves.index("1.1.1")


def test_ordem_sem_dependencias_e_identica_a_de_hoje() -> None:
    plano = criar_plano(ITENS, CONFIGURACAO, DATA_GERACAO)

    assert [operacao.chave for operacao in plano.operacoes] == ["1.0.0", "1.1.0", "1.1.1"]


def test_pai_continua_antes_do_filho_com_dependencia_entre_irmaos() -> None:
    funcional = ItemBacklog(
        "1.1.1",
        TipoItem.HISTORIA_USUARIO,
        "Funcional",
        "1.1.0",
        "Descrição",
        "",
        depende_de=("1.1.2",),
    )
    design = ItemBacklog("1.1.2", TipoItem.HISTORIA_USUARIO, "Design", "1.1.0", "Descrição", "")

    plano = criar_plano([funcional, design, ITENS[1], ITENS[2]], CONFIGURACAO, DATA_GERACAO)

    chaves = [operacao.chave for operacao in plano.operacoes]
    assert chaves.index("1.1.0") < chaves.index("1.1.2")


def test_operacao_propaga_dependencias() -> None:
    funcional = ItemBacklog(
        "1.1.1",
        TipoItem.HISTORIA_USUARIO,
        "Funcional",
        "1.1.0",
        "Descrição",
        "",
        depende_de=("1.1.2",),
    )
    design = ItemBacklog("1.1.2", TipoItem.HISTORIA_USUARIO, "Design", "1.1.0", "Descrição", "")

    plano = criar_plano([funcional, design, ITENS[1], ITENS[2]], CONFIGURACAO, DATA_GERACAO)
    operacao = next(o for o in plano.operacoes if o.chave == "1.1.1")

    assert operacao.depende_de == ("1.1.2",)


def test_hash_nao_muda_para_backlog_sem_dependencias() -> None:
    # mesmo literal da Tarefa 2: a ordenação topológica estável não pode alterar
    # nem a ordem nem o conteúdo serializado de um backlog sem arestas
    esperado = criar_plano(ITENS, CONFIGURACAO, DATA_GERACAO).hash_plano

    assert criar_plano(list(reversed(ITENS)), CONFIGURACAO, DATA_GERACAO).hash_plano == esperado


def test_dependencia_entre_ramos_preserva_pai_antes_do_filho() -> None:
    itens = [
        ItemBacklog("1.0.0", TipoItem.EPIC, "E1", None, "Descrição", ""),
        ItemBacklog("3.0.0", TipoItem.EPIC, "E3", None, "Descrição", ""),
        ItemBacklog("1.1.0", TipoItem.FEATURE, "F1", "1.0.0", "Descrição", ""),
        ItemBacklog("3.1.0", TipoItem.FEATURE, "F3", "3.0.0", "Descrição", ""),
        ItemBacklog(
            "1.1.1",
            TipoItem.HISTORIA_USUARIO,
            "L1",
            "1.1.0",
            "Descrição",
            "",
            depende_de=("3.1.1",),
        ),
        ItemBacklog("3.1.1", TipoItem.HISTORIA_USUARIO, "L3", "3.1.0", "Descrição", ""),
    ]

    chaves = [o.chave for o in criar_plano(itens, CONFIGURACAO, DATA_GERACAO).operacoes]

    assert chaves.index("3.1.1") < chaves.index("1.1.1")
    assert chaves.index("3.0.0") < chaves.index("3.1.0") < chaves.index("3.1.1")
    assert chaves.index("1.0.0") < chaves.index("1.1.0") < chaves.index("1.1.1")
