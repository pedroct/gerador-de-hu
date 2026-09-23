from __future__ import annotations

from dataclasses import replace
from json import loads

import httpx
import pytest

from publicar_backlog_demanda_azure_boards.cliente_azure_devops import (
    ClienteAzureDevOps,
    ErroAutenticacao,
    ErroAzureDevOps,
    ErroConflito,
    ErroCriacaoAmbigua,
    ErroDestinoInvalido,
    ErroFalhaTransitoria,
    ErroPermissao,
)
from publicar_backlog_demanda_azure_boards.modelos import (
    ConfiguracaoPublicacao,
    MapeamentoTipos,
    OperacaoCriacao,
    TipoItem,
)

CONFIGURACAO = ConfiguracaoPublicacao("org", "Projeto", "Projeto", r"Projeto\Sprint 18", 13959)
OPERACAO = OperacaoCriacao("1.0.0", TipoItem.EPIC, "Épico", "<p>Descrição</p>\n", "", None, "Epic")
CAMPOS_OBRIGATORIOS = [
    {"referenceName": "System.Title"},
    {"referenceName": "System.Description"},
    {"referenceName": "Microsoft.VSTS.Common.AcceptanceCriteria"},
    {"referenceName": "System.AreaPath"},
    {"referenceName": "System.IterationPath"},
]


def cliente(
    respostas: list[httpx.Response | Exception],
    configuracao: ConfiguracaoPublicacao = CONFIGURACAO,
) -> tuple[ClienteAzureDevOps, list[httpx.Request]]:
    chamadas: list[httpx.Request] = []

    def enviar(request: httpx.Request) -> httpx.Response:
        chamadas.append(request)
        resposta_atual = respostas.pop(0)
        if isinstance(resposta_atual, Exception):
            raise resposta_atual
        return resposta_atual

    return (
        ClienteAzureDevOps(
            configuracao,
            "valor" + "-de-teste",
            transport=httpx.MockTransport(enviar),
            espera_inicial=0,
        ),
        chamadas,
    )


def resposta(status: int, corpo: dict[str, object] | None = None) -> httpx.Response:
    return httpx.Response(status, json=corpo or {}, request=httpx.Request("GET", "https://teste"))


def resposta_bruta(status: int, conteudo: bytes) -> httpx.Response:
    return httpx.Response(
        status,
        content=conteudo,
        request=httpx.Request("POST", "https://teste"),
    )


def respostas_verificacao(
    configuracao: ConfiguracaoPublicacao = CONFIGURACAO,
) -> list[httpx.Response]:
    tipos = configuracao.mapeamento_tipos.nomes_remotos()
    return [
        resposta(200, {"value": [{"name": tipo} for tipo in tipos]}),
        *(resposta(200, {"value": CAMPOS_OBRIGATORIOS}) for _ in tipos),
        resposta(200, {"value": [{"referenceName": "System.LinkTypes.Hierarchy-Reverse"}]}),
        resposta(
            200,
            {
                "name": "Projeto",
                "path": r"\Projeto\Area",
                "url": "https://dev.azure.com/org/Projeto/_apis/wit/classificationnodes/Areas",
                "structureType": "area",
            },
        ),
        resposta(
            200,
            {
                "name": "Sprint 18",
                "path": r"\Projeto\Iteration\Sprint 18",
                "url": "https://dev.azure.com/org/Projeto/_apis/wit/classificationnodes/Iterations/Sprint%2018",
                "structureType": "iteration",
            },
        ),
    ]


def test_verificacao_consulta_tipos_e_classification_paths_sem_criar_item() -> None:
    cliente_azure, chamadas = cliente(respostas_verificacao())

    destino = cliente_azure.verificar_destino(CONFIGURACAO)

    assert destino.tipos == ("Epic", "Feature", "User Story", "Bug")
    assert {campo["referenceName"] for campo in CAMPOS_OBRIGATORIOS} <= set(destino.campos)
    assert destino.relacoes == ("System.LinkTypes.Hierarchy-Reverse",)
    assert destino.area_path == "Projeto"
    assert destino.iteration_path == r"Projeto\Sprint 18"
    assert chamadas[-2].url.path.endswith("/classificationnodes/Areas")
    assert chamadas[-1].url.path.endswith("/classificationnodes/Iterations/Sprint 18")
    assert chamadas[-3].url.path.endswith("/org/_apis/wit/workitemrelationtypes")
    assert not any(request.method == "POST" for request in chamadas)


def test_verificacao_aceita_tipo_sem_campo_de_criterios_de_aceitacao() -> None:
    respostas = respostas_verificacao()
    campos_sem_criterios = [
        campo
        for campo in CAMPOS_OBRIGATORIOS
        if campo["referenceName"] != "Microsoft.VSTS.Common.AcceptanceCriteria"
    ]
    respostas[1] = resposta(200, {"value": campos_sem_criterios})

    cliente_azure, _ = cliente(respostas)

    destino = cliente_azure.verificar_destino(CONFIGURACAO)

    assert destino.tipos == ("Epic", "Feature", "User Story", "Bug")


def test_validacao_de_tipo_sem_criterios_nao_envia_campo_indisponivel() -> None:
    respostas = respostas_verificacao()
    campos_sem_criterios = [
        campo
        for campo in CAMPOS_OBRIGATORIOS
        if campo["referenceName"] != "Microsoft.VSTS.Common.AcceptanceCriteria"
    ]
    respostas[1] = resposta(200, {"value": campos_sem_criterios})
    respostas.append(resposta(200))
    cliente_azure, chamadas = cliente(respostas)

    cliente_azure.verificar_destino(CONFIGURACAO)
    cliente_azure.validar_operacao(OPERACAO)

    assert all(
        item["path"] != "/fields/Microsoft.VSTS.Common.AcceptanceCriteria"
        for item in loads(chamadas[-1].content)
    )


@pytest.mark.parametrize(
    ("indice", "corpo_invalido"),
    [
        (0, {}),
        (1, {"value": []}),
        (5, {"value": [{"referenceName": "System.LinkTypes.Related"}]}),
        (6, {"name": "Projeto", "path": r"\Projeto", "structureType": "iteration"}),
        (
            7,
            {"name": "Sprint 18", "path": r"\Outro\Sprint 18", "structureType": "iteration"},
        ),
    ],
)
def test_verificacao_rejeita_resposta_incompleta_ou_destino_incompativel(
    indice: int, corpo_invalido: dict[str, object]
) -> None:
    respostas = respostas_verificacao()
    respostas[indice] = resposta(200, corpo_invalido)
    cliente_azure, _ = cliente(respostas)

    with pytest.raises(ErroDestinoInvalido):
        cliente_azure.verificar_destino(CONFIGURACAO)


def test_verificacao_rejeita_url_de_classification_node_incompativel() -> None:
    respostas = respostas_verificacao()
    respostas[-2] = resposta(
        200,
        {
            "name": "Projeto",
            "path": r"\Projeto\Area",
            "url": "https://dev.azure.com/org/Projeto/_apis/wit/classificationnodes/Areas/Outro",
            "structureType": "area",
        },
    )
    cliente_azure, _ = cliente(respostas)

    with pytest.raises(ErroDestinoInvalido):
        cliente_azure.verificar_destino(CONFIGURACAO)


def test_verificacao_aceita_url_oficial_com_id_de_projeto_e_casing_do_endpoint() -> None:
    respostas = respostas_verificacao()
    respostas[-2] = resposta(
        200,
        {
            "name": "Projeto",
            "path": r"\Projeto\Area",
            "url": "https://dev.azure.com/org/00000000-0000-0000-0000-000000000001/_apis/wit/classificationNodes/Areas",
            "structureType": "area",
        },
    )
    respostas[-1] = resposta(
        200,
        {
            "name": "Sprint 18",
            "path": r"\Projeto\Iteration\Sprint 18",
            "url": "https://dev.azure.com/org/00000000-0000-0000-0000-000000000001/_apis/wit/classificationNodes/Iterations/Sprint%2018",
            "structureType": "iteration",
        },
    )
    cliente_azure, _ = cliente(respostas)

    destino = cliente_azure.verificar_destino(CONFIGURACAO)

    assert destino.iteration_path == r"Projeto\Sprint 18"


def test_verificacao_aceita_area_path_filho_com_segmento_fixo_inserido_pelo_azure() -> None:
    """Reproduz o `path` real de um nó filho, com o segmento `Area` que o Azure sempre insere."""
    configuracao = replace(CONFIGURACAO, area_path=r"Projeto\Sustentacao")
    respostas = respostas_verificacao(configuracao)
    respostas[-2] = resposta(
        200,
        {
            "name": "Sustentacao",
            "path": r"\Projeto\Area\Sustentacao",
            "url": "https://dev.azure.com/org/Projeto/_apis/wit/classificationnodes/Areas/Sustentacao",
            "structureType": "area",
        },
    )
    cliente_azure, _ = cliente(respostas, configuracao)

    destino = cliente_azure.verificar_destino(configuracao)

    assert destino.area_path == r"Projeto\Sustentacao"


def test_criacao_usa_endpoint_com_cifrao_json_patch_e_tipo_remoto() -> None:
    cliente_azure, chamadas = cliente(
        [resposta(200, {"id": 123, "url": "https://dev.azure.com/item/123"})]
    )

    registro = cliente_azure.criar_item(OPERACAO)

    request = chamadas[0]
    assert request.headers["content-type"] == "application/json-patch+json"
    assert request.url.path.endswith("/workitems/$Epic")
    assert "validateOnly" not in str(request.url)
    assert registro.id == 123


def test_product_backlog_item_e_validado_e_usado_na_url() -> None:
    configuracao = replace(
        CONFIGURACAO,
        mapeamento_tipos=MapeamentoTipos(historia_usuario="Product Backlog Item"),
    )
    operacao = OperacaoCriacao(
        "1.1.1",
        TipoItem.HISTORIA_USUARIO,
        "História",
        "",
        "",
        "1.1.0",
        "Product Backlog Item",
    )
    respostas = respostas_verificacao(configuracao)
    respostas.append(resposta(200, {"id": 8, "url": "https://dev.azure.com/item/8"}))
    cliente_azure, chamadas = cliente(respostas, configuracao)

    cliente_azure.verificar_destino(configuracao)
    cliente_azure.criar_item(operacao)

    assert "Product Backlog Item" in [item for item in cliente_azure.tipos_remotos]
    assert chamadas[-1].url.path.endswith("/workitems/$Product Backlog Item")


def test_validacao_eh_somente_remota_e_nunca_bypass_rules() -> None:
    cliente_azure, chamadas = cliente([resposta(200)])

    cliente_azure.validar_operacao(OPERACAO)

    url = str(chamadas[0].url)
    assert "validateOnly=true" in url
    assert "bypassRules" not in url


@pytest.mark.parametrize(
    ("status", "erro"),
    [
        (401, ErroAutenticacao),
        (403, ErroPermissao),
        (404, ErroDestinoInvalido),
        (409, ErroConflito),
    ],
)
def test_classifica_erros_http_permanentes(status: int, erro: type[Exception]) -> None:
    cliente_azure, _ = cliente([resposta(status)])

    with pytest.raises(erro):
        cliente_azure.criar_item(OPERACAO)


def test_timeout_de_criacao_e_ambiguo_sem_repetir_post_ou_expor_token() -> None:
    cliente_azure, chamadas = cliente([httpx.ReadTimeout("tempo esgotado")])

    with pytest.raises(ErroCriacaoAmbigua) as falha:
        cliente_azure.criar_item(OPERACAO)

    assert "valor-de-teste" not in str(falha.value)
    assert len(chamadas) == 1


def test_erro_de_rede_de_criacao_e_ambiguo_sem_repetir_post() -> None:
    cliente_azure, chamadas = cliente([httpx.ProtocolError("protocolo interrompido")])

    with pytest.raises(ErroCriacaoAmbigua):
        cliente_azure.criar_item(OPERACAO)

    assert len(chamadas) == 1


def test_corpo_invalido_de_criacao_e_ambiguo() -> None:
    cliente_azure, chamadas = cliente([resposta_bruta(200, b"nao-json")])

    with pytest.raises(ErroCriacaoAmbigua):
        cliente_azure.criar_item(OPERACAO)

    assert len(chamadas) == 1


def test_url_malformada_de_criacao_e_ambigua_sem_repetir_post() -> None:
    cliente_azure, chamadas = cliente([resposta(200, {"id": 10, "url": "https://[invalido"})])

    with pytest.raises(ErroCriacaoAmbigua):
        cliente_azure.criar_item(OPERACAO)

    assert len(chamadas) == 1


def test_nao_re_tenta_post_apos_erro_transitorio_ambiguo() -> None:
    cliente_azure, chamadas = cliente(
        [resposta(503), resposta(200, {"id": 9, "url": "https://item/9"})]
    )

    with pytest.raises(ErroCriacaoAmbigua):
        cliente_azure.criar_item(OPERACAO)

    assert len(chamadas) == 1


def test_re_tenta_apenas_leitura_com_erro_transitorio() -> None:
    cliente_azure, chamadas = cliente([resposta(503), *respostas_verificacao()])

    destino = cliente_azure.verificar_destino(CONFIGURACAO)

    assert destino.tipos[0] == "Epic"
    assert len(chamadas) == 9


def test_timeout_de_validacao_nao_eh_estado_ambiguo_de_escrita() -> None:
    cliente_azure, chamadas = cliente([httpx.ReadTimeout("tempo esgotado")])

    with pytest.raises(ErroFalhaTransitoria):
        cliente_azure.validar_operacao(OPERACAO)

    assert len(chamadas) == 1


@pytest.mark.parametrize(
    "corpo",
    [
        {},
        {"id": True, "url": "https://dev.azure.com/org/projeto/_apis/wit/workItems/1"},
        {"id": 0, "url": "https://dev.azure.com/org/projeto/_apis/wit/workItems/1"},
        {"id": 1, "url": ""},
        {"id": 1, "url": "item-sem-esquema"},
    ],
)
def test_criacao_rejeita_resposta_sem_identidade_valida(corpo: dict[str, object]) -> None:
    cliente_azure, _ = cliente([resposta(200, corpo)])

    with pytest.raises(ErroAzureDevOps):
        cliente_azure.criar_item(OPERACAO)


def test_relacao_hierarquica_so_eh_enviada_com_id_do_pai() -> None:
    cliente_azure, chamadas = cliente([resposta(200, {"id": 10, "url": "https://item/10"})])

    cliente_azure.criar_item(OPERACAO, id_pai=7)

    assert any(item["path"] == "/relations/-" for item in loads(chamadas[0].content))
