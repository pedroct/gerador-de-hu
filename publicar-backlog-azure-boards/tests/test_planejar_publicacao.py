from dataclasses import replace

from publicar_backlog_azure_boards.modelos import (
    ConfiguracaoPublicacao,
    ItemBacklog,
    MapeamentoTipos,
    TipoItem,
)
from publicar_backlog_azure_boards.planejar_publicacao import criar_plano

CONFIGURACAO = ConfiguracaoPublicacao(
    organizacao="organizacao",
    projeto="projeto",
    area_path="projeto",
    iteration_path="projeto\\Sprint 18",
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


def test_operacao_prefixa_titulo_com_data_de_geracao_e_chave_documental() -> None:
    plano = criar_plano(ITENS, CONFIGURACAO, DATA_GERACAO)
    historia = plano.operacoes[-1]

    assert historia.titulo == "2026-09-16 1.1.1 História"


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

    assert plano.operacoes[0].titulo == "2026-09-16 1.1.1 História curta"


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


def test_mapeamento_product_backlog_item_integra_operacao_e_hash() -> None:
    configuracao_pbi = replace(
        CONFIGURACAO,
        mapeamento_tipos=MapeamentoTipos(historia_usuario="Product Backlog Item"),
    )

    plano_padrao = criar_plano(ITENS, CONFIGURACAO, DATA_GERACAO)
    plano_pbi = criar_plano(ITENS, configuracao_pbi, DATA_GERACAO)

    assert plano_pbi.operacoes[-1].tipo_remoto == "Product Backlog Item"
    assert plano_pbi.hash_plano != plano_padrao.hash_plano
