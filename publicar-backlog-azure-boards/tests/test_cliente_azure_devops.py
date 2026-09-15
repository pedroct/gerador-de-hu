from __future__ import annotations

from json import loads

import httpx
import pytest

from publicar_backlog_azure_boards.cliente_azure_devops import (
    ClienteAzureDevOps,
    ErroAutenticacao,
    ErroAzureDevOps,
    ErroConflito,
    ErroDestinoInvalido,
    ErroFalhaTransitoria,
    ErroPermissao,
)
from publicar_backlog_azure_boards.modelos import (
    ConfiguracaoPublicacao,
    OperacaoCriacao,
    TipoItem,
)

CONFIGURACAO = ConfiguracaoPublicacao("org", "projeto", "Projeto", r"Projeto\Sprint 18")
OPERACAO = OperacaoCriacao("1.0.0", TipoItem.EPIC, "Épico", "<p>Descrição</p>\n", "", None)
CAMPOS_OBRIGATORIOS = [
    {"referenceName": "System.Title"},
    {"referenceName": "System.Description"},
    {"referenceName": "Microsoft.VSTS.Common.AcceptanceCriteria"},
    {"referenceName": "System.AreaPath"},
    {"referenceName": "System.IterationPath"},
]


def cliente(
    respostas: list[httpx.Response | Exception],
) -> tuple[ClienteAzureDevOps, list[httpx.Request]]:
    chamadas: list[httpx.Request] = []

    def enviar(request: httpx.Request) -> httpx.Response:
        chamadas.append(request)
        resposta = respostas.pop(0)
        if isinstance(resposta, Exception):
            raise resposta
        return resposta

    return (
        ClienteAzureDevOps(
            CONFIGURACAO,
            "valor" + "-de-teste",
            transport=httpx.MockTransport(enviar),
            espera_inicial=0,
        ),
        chamadas,
    )


def resposta(status: int, corpo: dict[str, object] | None = None) -> httpx.Response:
    return httpx.Response(status, json=corpo or {}, request=httpx.Request("GET", "https://teste"))


def respostas_verificacao() -> list[httpx.Response]:
    return [
        resposta(
            200,
            {
                "value": [
                    {"name": "Epic"},
                    {"name": "Feature"},
                    {"name": "User Story"},
                    {"name": "Bug"},
                ]
            },
        ),
        *(resposta(200, {"value": CAMPOS_OBRIGATORIOS}) for _ in range(4)),
        resposta(200, {"value": [{"referenceName": "System.LinkTypes.Hierarchy-Reverse"}]}),
        resposta(200, {"name": "Projeto", "path": r"\Projeto"}),
        resposta(200, {"name": "Sprint 18", "path": r"\Projeto\Sprint 18"}),
    ]


def test_verificacao_consulta_tipos_sem_criar_item() -> None:
    cliente_azure, chamadas = cliente(respostas_verificacao())

    destino = cliente_azure.verificar_destino(CONFIGURACAO)

    assert destino.tipos == ("Epic", "Feature", "User Story", "Bug")
    assert {campo["referenceName"] for campo in CAMPOS_OBRIGATORIOS} <= set(destino.campos)
    assert destino.relacoes == ("System.LinkTypes.Hierarchy-Reverse",)
    assert destino.area_path == "Projeto"
    assert destino.iteration_path == r"Projeto\Sprint 18"
    assert not any(
        request.method == "POST" and "/workitems/" in str(request.url) for request in chamadas
    )


@pytest.mark.parametrize(
    ("indice", "corpo_invalido"),
    [
        (0, {}),
        (1, {"value": []}),
        (5, {"value": [{"referenceName": "System.LinkTypes.Related"}]}),
        (6, {"name": "Projeto"}),
        (7, {"name": "Sprint 18", "path": r"\Outro\Sprint 18"}),
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


def test_criacao_envia_json_patch_e_tipo() -> None:
    cliente_azure, chamadas = cliente(
        [resposta(200, {"id": 123, "url": "https://dev.azure.com/item/123"})]
    )

    registro = cliente_azure.criar_item(OPERACAO)

    request = chamadas[0]
    assert request.headers["content-type"] == "application/json-patch+json"
    assert "/workitems/Epic" in str(request.url)
    assert "validateOnly" not in str(request.url)
    assert registro.id == 123


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


def test_timeout_vira_falha_transitoria_sem_expor_token() -> None:
    cliente_azure, chamadas = cliente([httpx.ReadTimeout("tempo esgotado") for _ in range(3)])

    with pytest.raises(ErroFalhaTransitoria) as falha:
        cliente_azure.criar_item(OPERACAO)

    assert "valor-de-teste" not in str(falha.value)
    assert len(chamadas) == 1


def test_nao_re_tenta_post_apos_erro_transitorio_ambiguo() -> None:
    cliente_azure, chamadas = cliente(
        [resposta(503), resposta(200, {"id": 9, "url": "https://item/9"})]
    )

    with pytest.raises(ErroFalhaTransitoria):
        cliente_azure.criar_item(OPERACAO)

    assert len(chamadas) == 1


def test_re_tenta_apenas_leitura_com_erro_transitorio() -> None:
    cliente_azure, chamadas = cliente([resposta(503), *respostas_verificacao()])

    destino = cliente_azure.verificar_destino(CONFIGURACAO)

    assert destino.tipos[0] == "Epic"
    assert len(chamadas) == 9


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
