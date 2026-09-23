"""Leitura somente leitura da Demanda de Negócio que ancora a publicação."""

import httpx
import pytest

from publicar_backlog_demanda_azure_boards.cliente_azure_devops import ErroDestinoInvalido
from publicar_backlog_demanda_azure_boards.leitor_demanda import ler_demanda

_URL = "https://dev.azure.com/contoso/CESOP-DILIGENCIA/_apis/wit/workItems/13959"


def _payload(**sobrescritas: object) -> dict[str, object]:
    campos: dict[str, object] = {
        "System.WorkItemType": "Demanda de Negócio",
        "System.TeamProject": "CESOP-DILIGENCIA",
        "System.Title": "PADRONIZAÇÃO E ATUALIZAÇÃO DAS STACKS DA APLICAÇÃO",
        "System.AreaPath": "CESOP-DILIGENCIA\\Sustentacao",
        "System.IterationPath": "CESOP-DILIGENCIA\\Sprint 18",
    }
    campos.update(sobrescritas)
    return {"id": 13959, "url": _URL, "fields": campos}


def _transporte(payload: object, status: int = 200) -> httpx.MockTransport:
    def responder(requisicao: httpx.Request) -> httpx.Response:
        assert requisicao.method == "GET"
        return httpx.Response(status, json=payload)

    return httpx.MockTransport(responder)


def _ler(payload: object, status: int = 200, tipo: str = "Demanda de Negócio"):
    return ler_demanda(
        "contoso",
        "CESOP-DILIGENCIA",
        "token-de-teste",
        13959,
        tipo,
        transport=_transporte(payload, status),
    )


def test_le_a_demanda_e_extrai_titulo_e_caminhos() -> None:
    demanda = _ler(_payload())
    assert demanda.id == 13959
    assert demanda.titulo == "PADRONIZAÇÃO E ATUALIZAÇÃO DAS STACKS DA APLICAÇÃO"
    assert demanda.area_path == "CESOP-DILIGENCIA\\Sustentacao"
    assert demanda.iteration_path == "CESOP-DILIGENCIA\\Sprint 18"
    assert demanda.url == _URL


def test_recusa_work_item_de_outro_tipo() -> None:
    with pytest.raises(ErroDestinoInvalido) as erro:
        _ler(_payload(**{"System.WorkItemType": "Epic"}))
    assert "Epic" in str(erro.value)
    assert "Demanda de Negócio" in str(erro.value)


def test_recusa_demanda_de_outro_projeto() -> None:
    with pytest.raises(ErroDestinoInvalido) as erro:
        _ler(_payload(**{"System.TeamProject": "OUTRO-PROJETO"}))
    assert "OUTRO-PROJETO" in str(erro.value)


@pytest.mark.parametrize("campo", ["System.AreaPath", "System.IterationPath", "System.Title"])
def test_recusa_demanda_sem_campo_necessario(campo: str) -> None:
    with pytest.raises(ErroDestinoInvalido) as erro:
        _ler(_payload(**{campo: ""}))
    assert campo in str(erro.value)


def test_recusa_work_item_inexistente() -> None:
    with pytest.raises(ErroDestinoInvalido) as erro:
        _ler({"message": "não encontrado"}, status=404)
    assert "13959" in str(erro.value)


def test_recusa_identificador_nao_positivo() -> None:
    with pytest.raises(ErroDestinoInvalido):
        ler_demanda(
            "contoso",
            "CESOP-DILIGENCIA",
            "token-de-teste",
            0,
            "Demanda de Negócio",
            transport=_transporte(_payload()),
        )


def test_nao_expoe_o_token_na_mensagem_de_erro() -> None:
    with pytest.raises(ErroDestinoInvalido) as erro:
        _ler({"message": "não encontrado"}, status=404)
    assert "token-de-teste" not in str(erro.value)


@pytest.mark.parametrize(
    "url_invalida",
    [
        "http://dev.azure.com/contoso/_apis/wit/workItems/13959",
        "",
        "   ",
        "dev.azure.com/contoso/_apis/wit/workItems/13959",
    ],
)
def test_recusa_demanda_sem_url_utilizavel(url_invalida: str) -> None:
    payload = _payload()
    payload["url"] = url_invalida
    with pytest.raises(ErroDestinoInvalido) as erro:
        _ler(payload)
    assert "13959" in str(erro.value)


def test_recusa_demanda_com_url_de_tipo_errado() -> None:
    payload = _payload()
    payload["url"] = 13959
    with pytest.raises(ErroDestinoInvalido):
        _ler(payload)
