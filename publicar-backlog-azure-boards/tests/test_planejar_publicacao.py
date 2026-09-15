from publicar_backlog_azure_boards.modelos import (
    ConfiguracaoPublicacao,
    ItemBacklog,
    RegistroManifesto,
    TipoItem,
)
from publicar_backlog_azure_boards.planejar_publicacao import criar_plano

CONFIGURACAO = ConfiguracaoPublicacao(
    organizacao="organizacao",
    projeto="projeto",
    area_path="Projeto",
    iteration_path="Projeto\\Sprint 18",
)
ITENS = [
    ItemBacklog("1.1.1", TipoItem.HISTORIA_USUARIO, "História", "1.1.0", "Descrição", ""),
    ItemBacklog("1.1.0", TipoItem.FEATURE, "Feature", "1.0.0", "Descrição", ""),
    ItemBacklog("1.0.0", TipoItem.EPIC, "Épico", None, "Descrição", ""),
]
REGISTRO_EXISTENTE = RegistroManifesto(id=123, tipo=TipoItem.EPIC, url="https://exemplo/123")


def test_plano_ordena_epic_feature_e_folha() -> None:
    plano = criar_plano(ITENS, CONFIGURACAO, {})

    assert [operacao.chave for operacao in plano.operacoes] == ["1.0.0", "1.1.0", "1.1.1"]


def test_plano_exclui_item_registrado_no_manifesto() -> None:
    plano = criar_plano(ITENS, CONFIGURACAO, {"1.0.0": REGISTRO_EXISTENTE})

    assert "1.0.0" not in [operacao.chave for operacao in plano.operacoes]


def test_plano_converte_apenas_campos_copiaveis_e_inclui_pai() -> None:
    plano = criar_plano(ITENS, CONFIGURACAO, {})
    historia = plano.operacoes[-1]

    assert historia.descricao == "<p>Descrição</p>\n"
    assert historia.criterios_aceitacao == ""
    assert historia.chave_pai == "1.1.0"


def test_hash_muda_quando_destino_muda() -> None:
    outro_destino = ConfiguracaoPublicacao(
        organizacao="organizacao",
        projeto="outro-projeto",
        area_path="Projeto",
        iteration_path="Projeto\\Sprint 18",
    )

    assert criar_plano(ITENS, CONFIGURACAO, {}).hash_plano != criar_plano(
        ITENS, outro_destino, {}
    ).hash_plano
